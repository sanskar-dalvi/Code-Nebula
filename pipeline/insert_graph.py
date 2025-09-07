"""Graph insertion module."""
import json
import sys
import os
import logging
from datetime import datetime
from pipeline.models import CodeEntity,File,ContainsRel,Project,Module 
from  pathlib import Path

logger = logging.getLogger("csharp-parser")

def collect_all_nodes(ast_node):
    """Recursively collect all nodes from AST."""
    nodes = []
    queue = [ast_node]
    while queue:
        current = queue.pop()
        nodes.append(current)
        children = []
        for key in ["body", "members", "statements", "children"]:
            if key in current and isinstance(current[key], list):
                children.extend(current[key])
        queue.extend(children)
    return nodes

def ingest_enriched_json(curated_path: str):
    """
    Read enriched JSON and create nodes/edges in Neo4j.
    """
    logger.info(f"Starting ingestion of enriched JSON: {curated_path}")
    curated_path = Path(curated_path)
    if not curated_path.exists() or not curated_path.is_dir():
        logger.error(f"Invalid curated path: {curated_path}")
        return
    json_files = list(curated_path.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in curated directory: {curated_path}")
        return

    for json_file in json_files:
        _process_single_file(json_file)

def _process_single_file(file_path: Path):
    """
    Process a single curated JSON file and create nodes/edges in Neo4j.
    """
    logger.info(f"Processing curated file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON file {file_path}: {e}")
        return
    
    file_stem = file_path.stem  # Remove .json
    parts = file_stem.split("_")
    if parts[-1].lower() == "enriched":
        parts = parts[:-1]
    project_name = parts[0]
    module_name = parts[1] if len(parts) >= 2 else "UnknownModule"
    file_name = parts[2] if len(parts) >= 3 else file_stem

    # --- Project node ---
    project_uid = f"Project:{project_name}"
    project_node = Project.nodes.get_or_none(uid=project_uid)
    if not project_node:
        project_node = Project(uid=project_uid, name=project_name).save()
        logger.info(f"Created Project node: {project_name}")

    # --- Module node ---
    module_uid = f"Module:{project_name}/{module_name}"
    module_node = Module.nodes.get_or_none(uid=module_uid)
    if not module_node:
        module_node = Module(
            uid=module_uid,
            name=module_name,
            path=str(file_path.parent),
            module_type="folder" if file_path.parent != file_path.parents[1] else "root"                
        ).save()
        logger.info(f"project_node.modules expects: {project_node.modules.definition['node_class']}")
        logger.info(f"module_node is instance of: {type(module_node)}")
        project_node.modules.connect(module_node) 
        logger.info(f"Created Module node: {module_name}")
    file_uid = f"File:{file_path}"
    file_node = File.nodes.get_or_none(uid=file_uid)
    if not file_node:
        try:
            file_node = File(
                uid=file_uid,
                name=file_path.name,
                path=str(file_path),
                file_type=file_path.suffix.lstrip("."),
                last_modified=datetime.now(),
                content_hash=data.get("file_hash", ""),
                lines_of_code=data.get("loc", 0),
                size_bytes=data.get("size", 0)
            ).save()
            # Create HAS_FILE relationship between module and file
            module_node.files.connect(file_node)
            logger.info(f"Created File node: {file_name} and connected it to module: {module_name}")
        except Exception as e:
            logger.error(f"File node creation failed: {e}")
            return
    
    
    ast_nodes = []
    for root in data.get("ast", []):
        ast_nodes.extend(collect_all_nodes(root))
    logger.info(f"Collected {len(ast_nodes)} AST nodes")

    node_map = {}
    new_nodes, new_links = 0, 0
    
    # First pass: Create all CodeEntity nodes including enum members
    all_nodes_to_process = []
    for node in ast_nodes:
        all_nodes_to_process.append(node)
        # Also add enum members if they exist
        for child in node.get("members", []):
            if isinstance(child, dict):
                # Handle enum members which might not have a type field
                if "type" not in child and "name" in child and child.get("startLine"):
                    child["type"] = "EnumMember"
                    logger.info(f"Fixed enum member node: {child['name']} at line {child.get('startLine')}")
                all_nodes_to_process.append(child)
        # Also add body items
        for child in node.get("body", []):
            if isinstance(child, dict):
                all_nodes_to_process.append(child)
        # Also add statements
        for child in node.get("statements", []):
            if isinstance(child, dict):
                all_nodes_to_process.append(child)
    
    # Create CodeEntity nodes for all collected nodes
    for node in all_nodes_to_process:
        node_type = node.get("type")
        node_name = node.get("name")
        if not node_type or not node_name:
            continue  # Skip malformed nodes

        uid = f"{node_type}:{node_name}:{node.get('startLine', 0)}"
        if uid in node_map:
            continue
        try:
            enrichment = node.get("enrichment", {})
            access_modifier = next((m for m in node.get("modifiers", []) if m in ["public", "private", "protected", "internal"]), "")
            signature = ""
            if node["type"] == "Method":
                return_type = node.get("returnType", "void")
                params = ", ".join(f"{p.get('type', '')} {p.get('name', '')}" for p in node.get("parameters", []))
                signature = f"{return_type} {node_name}({params})"

            entity = CodeEntity.nodes.get_or_none(uid=uid)
            if not entity:
                entity = CodeEntity(
                    uid=uid,
                    name=node_name,
                    type=node_type,
                    summary=enrichment.get("summary", ""),
                    tags=enrichment.get("tags", []),
                    access_modifier=access_modifier,
                    signature=signature,
                    metadata={
                        "startLine": node.get("startLine"),
                        "endLine": node.get("endLine"),
                        "modifiers": node.get("modifiers", []),
                        "baseTypes": node.get("baseTypes", []),
                        "method_names": node.get("method_names", [])
                    }
                ).save()
                new_nodes += 1
            if not file_node.entities.is_connected(entity):
                file_node.entities.connect(entity, {
                    "start_line": node.get("startLine", 0),
                    "end_line": node.get("endLine", 0)
                })
                new_links += 1

            node_map[uid] = entity
      
        except Exception as e:
            logger.error(f"Failed to process AST node {node.get('name')}: {e}")

    logger.info(f"Created {new_nodes} new CodeEntity nodes and {new_links} file→entity connections")

    # Second Pass: Entity-to-entity CONTAINS relationships
    contains_count = 0
    for node in ast_nodes:
        if not isinstance(node, dict):
            continue
            
        # Continue with the normal validation
        if "type" not in node or "name" not in node:
            continue
        parent_uid = f"{node['type']}:{node['name']}:{node.get('startLine', 0)}"
        parent = node_map.get(parent_uid)
        if not parent:
            continue
        for key in ["body", "members", "statements"]:
            for child in node.get(key, []):
                if not isinstance(child, dict):
                    continue
                # Handle enum members which might not have a type field
                if "type" not in child and "name" in child and child.get("startLine"):
                    child["type"] = "EnumMember"
                if 'type' not in child or 'name' not in child:
                    continue
                child_uid = f"{child['type']}:{child['name']}:{child.get('startLine', 0)}"
                child_entity = node_map.get(child_uid)
                if child_entity and not parent.contains.is_connected(child_entity):
                    parent.contains.connect(child_entity,{
                        "start_line": child.get("startLine"),
                        "end_line": child.get("endLine")
                    })
                    contains_count += 1
    logger.info(f"Created {contains_count} CONTAINS relationships")

    # HAS_PARAMETER and RETURNS
    param_count = 0
    return_count = 0
    for node in ast_nodes:
        if node.get("type") != "Method":
            continue
        method_uid = f"Method:{node['name']}:{node.get('startLine', 0)}"
        method_node = node_map.get(method_uid)
        if not method_node:
            continue

            # Parameters
        for p in node.get("parameters", []):
            pname = p.get("name")
            ptype = p.get("type")
            if not pname or not ptype:
                continue
            param_uid = f"Parameter:{method_uid}:{pname}"
            param_node = CodeEntity.nodes.get_or_none(uid=param_uid)
            if not param_node:
                param_node = CodeEntity(
                    uid=param_uid,
                    name=pname,
                    type="Parameter",
                    metadata={"dataType": ptype}
                ).save()
                node_map[param_uid] = param_node
            if not method_node.has_parameter.is_connected(param_node):
                method_node.has_parameter.connect(param_node)
                param_count += 1

        # Return type
        return_type = node.get("returnType", "void")
        return_uid = f"ReturnType:{return_type}"
        return_node = node_map.get(return_uid) or CodeEntity.nodes.get_or_none(uid=return_uid)
        if not return_node:
            return_node = CodeEntity(uid=return_uid, name=return_type, type="ReturnType").save()
            node_map[return_uid] = return_node

        if not method_node.returns.is_connected(return_node):
            method_node.returns.connect(return_node)
            return_count += 1

    logger.info(f"Created {param_count} HAS_PARAMETER and {return_count} RETURNS relationships")

    # IMPLEMENTS relationships
    impl_count = 0
    for node in ast_nodes:
        if node.get("baseTypes"):
            from_uid = f"{node['type']}:{node['name']}:{node.get('startLine', 0)}"
            from_node = node_map.get(from_uid)
            for base in node["baseTypes"]:
                to_uid = f"Interface:{base}:0"
                to_node = node_map.get(to_uid) or CodeEntity.nodes.get_or_none(uid=to_uid)
                if not to_node:
                    to_node = CodeEntity(uid=to_uid, name=base, type="Interface").save()
                    node_map[to_uid] = to_node
                if not from_node.implements.is_connected(to_node):
                    from_node.implements.connect(to_node)
                    impl_count += 1
        else:
            continue
    logger.info(f"Created {impl_count} IMPLEMENTS relationships")

    logger.info(f"✅ Completed ingestion: {file_name}")

        