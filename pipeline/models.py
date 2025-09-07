"""Data models for the pipeline."""

import os
from dotenv import load_dotenv
from neomodel import (StructuredNode, StructuredRel, StringProperty, JSONProperty, IntegerProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom,
    DateTimeProperty, BooleanProperty, ArrayProperty, config)

load_dotenv()
uri = os.getenv("NEO4J_BOLT_URL")
user = os.getenv("NEO4J_USERNAME")
pwd = os.getenv("NEO4J_PASSWORD")
print(f"BOLT_URL = {uri}")
config.DATABASE_URL = f"bolt://{user}:{pwd}@{uri.split('://')[1]}"



# Relationship properties
class DependencyRel(StructuredRel):
    strength = IntegerProperty()
    dependency_type = StringProperty()
    is_critical = BooleanProperty(default=False)
    
class ContainsRel(StructuredRel):
    start_line = IntegerProperty()
    end_line = IntegerProperty()


# Module Node (Subfolder or package)
class Module(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    path = StringProperty(required=True, unique_index=True)
    module_type = StringProperty()  # Core, Feature, Test, etc.

    project = RelationshipFrom("Project", "HAS_MODULE")
    files = RelationshipTo("File", "HAS_FILE")
    parent_module = RelationshipFrom("Module", "CONTAINS_MODULE")
    sub_modules = RelationshipTo("Module", "CONTAINS_MODULE")

# Project Node
class Project(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True, unique_index=True)
    description = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    repository_url = StringProperty()
    tags = ArrayProperty(StringProperty())

    modules = RelationshipTo(Module, "HAS_MODULE")

# File Node
class File(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    path = StringProperty(required=True, unique_index=True)
    file_type = StringProperty()  # .cs, .py, etc.
    lines_of_code = IntegerProperty()
    size_bytes = IntegerProperty()
    last_modified = DateTimeProperty()
    content_hash = StringProperty(index=True)

    module = RelationshipFrom("Module", "HAS_FILE")
    entities = RelationshipTo("CodeEntity", "HAS_ENTITY", model=ContainsRel)

# Core AST CodeEntity Node
class CodeEntity(StructuredNode):
    uid = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True, index=True)
    type = StringProperty(required=True, index=True)
    summary = StringProperty()
    access_modifier = StringProperty(index=True)
    signature = StringProperty()
    metadata = JSONProperty()
    tags = JSONProperty()
    full_text = StringProperty(index=True)
    complexity = IntegerProperty()
    labels = ArrayProperty(StringProperty(), index=True)

    # Relationships to other entities
    depends_on = RelationshipTo("CodeEntity", "DEPENDS_ON", model=DependencyRel)
    implements = RelationshipTo("CodeEntity", "IMPLEMENTS")
    inherits_from = RelationshipTo("CodeEntity", "INHERITS_FROM")
    overrides = RelationshipTo("CodeEntity", "OVERRIDES")
    uses = RelationshipTo("CodeEntity", "USES")
    accesses = RelationshipTo("CodeEntity", "ACCESSES")
    returns = RelationshipTo("CodeEntity", "RETURNS")
    has_parameter = RelationshipTo("CodeEntity", "HAS_PARAMETER")
    raises = RelationshipTo("CodeEntity", "RAISES")
    processes = RelationshipTo("CodeEntity", "PROCESSES")
    manages = RelationshipTo("CodeEntity", "MANAGES")
    contains = RelationshipTo("CodeEntity", "CONTAINS", model=ContainsRel)

    
    # Belongs to file
    file = RelationshipFrom(File, "HAS_ENTITY", model=ContainsRel)