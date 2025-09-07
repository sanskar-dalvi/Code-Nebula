"""Tests for the C# parser module."""
import os
import json
import sys
import pytest
import logging
from pipeline.cs_parser import parse_cs_file, serialize_to_json
logger = logging.getLogger("csharp-parser")


RAW_INPUT_DIR = os.path.join("raw") 
OUTPUT_DIR = os.path.join("staging")

class TestCSharpParser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.input_dir = RAW_INPUT_DIR
        self.output_dir = OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
    def test_parse_and_serialize(self):
        """
        Test parsing and serialization for all .cs files in the raw input directory.

        It walks through subdirectories and:
        - Parses each .cs file
        - Validates the AST
        - Saves a JSON file for each .cs file
        """

        logger.info(f"Scanning directory: {self.input_dir}")
        # First, identify all subdirectories
        subdirectories = []
        root_files = []
        for entry in os.listdir(self.input_dir):
            full_path = os.path.join(self.input_dir, entry)
            if os.path.isdir(full_path):
                subdirectories.append(full_path)
            elif entry.endswith('.cs'):
                root_files.append(full_path)
        for subdir in sorted(subdirectories):
            subdir_files = self._get_all_cs_files(subdir)
            self._process_files(subdir_files)
    
        # Then process root-level files
        self._process_files(sorted(root_files))
       
    def _process_files(self, files):
        """
        Process a list of .cs files by parsing them and serializing to JSON.
        """
        for file_path in files:
            relative_path = os.path.relpath(file_path, self.input_dir)
            output_path = os.path.join(self.output_dir, relative_path.replace(".cs", ".json"))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            logger.info(f"Parsing file: {file_path}")
            try:
                ast_nodes = parse_cs_file(file_path)
                assert isinstance(ast_nodes, list)
            
                # Validate AST contains expected structures
                if ast_nodes:
                    entity = self._find_any_valid_entity(ast_nodes)
                    assert entity, f"No valid entities found in {file_path}"
                
                    classes = self._find_all_classes(ast_nodes)
                    interfaces = self._count_interfaces(ast_nodes)
                
                    logger.info(f"File {relative_path}: {len(classes)} classes parsed")
                    if interfaces:
                        logger.info(f"File {relative_path}: {interfaces} interfaces parsed")
                
                    # Serialize the AST to JSON
                    serialize_to_json(ast_nodes, output_path)
                else:
                    logger.warning(f"No AST nodes found for {file_path}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                raise

    def _get_all_cs_files(self, root_dir):
        """
        Walk through root_dir and return all .cs file paths.
        """
        cs_files = []
        # First process subdirectory files
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".cs"):
                    cs_files.append(os.path.join(root, file))
        return cs_files
    
    def _find_any_class(self, nodes):
        """
        Recursively search for any class node in the AST.
        Returns True if at least one class is found.
        """
        try:
            for node in nodes:
                try:
                    if node.get("type") == "Class":
                        return True
                    if "body" in node and isinstance(node["body"], list):
                        if self._find_any_class(node["body"]):
                            return True
                except Exception as e:
                    logger.error(f"Error processing node in _find_any_class: {str(e)}")
                    continue
            return False
        except Exception as e:
            logger.error(f"Error in _find_any_class: {str(e)}")
            return False

    def _find_all_classes(self, nodes):
        """
        Recursively find all class nodes in the AST.
        Returns a list of all class nodes found.
        """
        classes = []
        try:
            for node in nodes:
                try:
                    if node.get("type") == "Class":
                        classes.append(node)
                    # If the node has a "body" key with nested nodes, recurse into it
                    if "body" in node and isinstance(node["body"], list):
                        classes.extend(self._find_all_classes(node["body"]))
                except Exception as e:
                    logger.error(f"Error processing node in _find_all_classes: {str(e)}")
                    continue
            return classes
        except Exception as e:
            logger.error(f"Error in _find_all_classes: {str(e)}")
            return classes
    def _find_any_valid_entity(self, nodes):
        """
        Find any class or interface in the AST nodes.
        """
        if isinstance(nodes, list):
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if node.get("type") in ["Class", "Interface","Enum"]:
                    return True
                for value in node.values():
                    if isinstance(value, list):
                        if self._find_any_valid_entity(value):
                            return True
        return False
    def _count_interfaces(self, nodes):
        """
        Count the number of interfaces in the AST nodes.
        """
        count = 0
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    if node.get("type") == "Interface":
                        count += 1
                    # Check in body if it exists
                    if "body" in node and isinstance(node["body"], list):
                        count += self._count_interfaces(node["body"])
        return count