"""C# Parser module."""
# Standard library imports
import sys
import os
import logging
import json
import traceback
# Third-party imports
from antlr4 import FileStream, CommonTokenStream

# Local application imports
from generated.csharp.CSharpLexer import CSharpLexer
from generated.csharp.CSharpParser import CSharpParser
from generated.csharp.CSharpParserVisitor import CSharpParserVisitor

# Set up logger for this module
logger = logging.getLogger(__name__)


class ASTCollector(CSharpParserVisitor):
    """Visitor to collect AST nodes from a C# parse tree."""

    def __init__(self):
        super().__init__()
        self.nodes = {
            "type": "Program",
            "statements": []
        }
        self.current_namespace = None
        self.current_class = None
        self.current_interface = None
        self.current_struct = None
        self.current_enum = None
        
    def visitNamespace_declaration(self, ctx):
        """
        Visit namespace declaration node and collect namespace information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the namespace declaration
            
        Returns:
            The result of visiting the namespace's children nodes
        """
        try:
            # Extract the namespace name
            namespace_name = ctx.qualified_identifier().getText()
            
            # Create a node representation for this namespace
            namespace_node = {
                "type": "Namespace",
                "name": namespace_name,
                "startLine": ctx.start.line,
                "body": []
            }
            self.nodes["statements"].append(namespace_node)
            
            # Set current namespace context
            previous_namespace = self.current_namespace
            self.current_namespace = namespace_node
            
            # Continue visiting child nodes within the namespace
            result = self.visitChildren(ctx)
            
            # Restore previous namespace context
            self.current_namespace = previous_namespace
            
            return result
        except Exception as e:
            logger.error(f"Error visiting namespace declaration at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def extract_modifiers_from_parent(self, ctx):
        """
        Traverses up the parse tree to find `all_member_modifiers`, if present.

        Args:
            ctx: Current parse tree node

        Returns:
            A list of modifier strings (e.g., ['public', 'static'])
        """
        parent = ctx.parentCtx
        while parent is not None:
            if hasattr(parent, "all_member_modifiers") and parent.all_member_modifiers():
                return [mod.getText() for mod in parent.all_member_modifiers().all_member_modifier()]
            parent = parent.parentCtx
        return []

    def visitClass_definition(self, ctx):
        """
        Visit class definition node and collect class information.
        
        This method is called whenever the visitor encounters a class definition
        in the C# parse tree. It extracts the class name and records its location.
        
        Args:
            ctx: The ANTLR4 parse tree context for the class definition
            
        Returns:
            The result of visiting the class's children nodes
        """
        try:
            # Extract the class name from the identifier node
            class_name = ctx.identifier().getText()
            
            # Extract class modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)
            if not modifiers:
                modifiers = ['internal']
            
            # Create a node representation for this class
            class_node = {
                "type": "Class",
                "name": class_name,
                "startLine": ctx.start.line,
                "modifiers": modifiers,
                "body": []
            }
            
            # Extract base types if present
            if ctx.class_base():
                base_types = []
                class_base_ctx = ctx.class_base()
                class_types = class_base_ctx.class_type()
                if class_types:
                    base_types.append(class_base_ctx.class_type().getText())
                if base_types:
                    class_node["baseTypes"] = base_types
            
            # Add to appropriate container
            if self.current_namespace:
                self.current_namespace["body"].append(class_node)
            else:
                self.nodes["statements"].append(class_node)
            
            # Set current class context
            previous_class = self.current_class
            self.current_class = class_node
            
            # Continue visiting child nodes (methods, properties, etc.)
            result = self.visitChildren(ctx)
            
            # Restore previous class context
            self.current_class = previous_class
            
            return result
        except Exception as e:
            logger.error(f"Error visiting class definition at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def visitInterface_definition(self, ctx):
        """
        Visit interface definition node and collect interface information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the interface definition
            
        Returns:
            The result of visiting the interface's children nodes
        """
        try:
            # Extract the interface name
            interface_name = ctx.identifier().getText()
            
            # Extract interface modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)

            # Create a node representation for this interface
            interface_node = {
                "type": "Interface",
                "name": interface_name,
                "startLine": ctx.start.line,
                "modifiers": modifiers,
                "body": []
            }
            
            # Extract base interfaces if present
            if ctx.interface_base():
                base_interfaces = []
                for interface_type in ctx.interface_base().interface_type_list().interface_type():
                    base_interfaces.append(interface_type.getText())
                if base_interfaces:
                    interface_node["baseInterfaces"] = base_interfaces
            
            # Add to appropriate container
            if self.current_namespace:
                self.current_namespace["body"].append(interface_node)
            else:
                self.nodes["statements"].append(interface_node)
            
            # Set current interface context
            previous_interface = self.current_interface
            self.current_interface = interface_node
            
            # Continue visiting child nodes
            result = self.visitChildren(ctx)
            
            # Restore previous interface context
            self.current_interface = previous_interface
            
            return result
        except Exception as e:
            logger.error(f"Error visiting interface definition at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def visitStruct_definition(self, ctx):
        """
        Visit struct definition node and collect struct information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the struct definition
            
        Returns:
            The result of visiting the struct's children nodes
        """
        try:
            # Extract the struct name
            struct_name = ctx.identifier().getText()
            
            # Extract struct modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)

            # Create a node representation for this struct
            struct_node = {
                "type": "Struct",
                "name": struct_name,
                "startLine": ctx.start.line,
                "modifiers": modifiers,
                "body": []
            }
            
            # Extract base interfaces if present
            if ctx.struct_interfaces():
                base_interfaces = []
                for interface_type in ctx.struct_interfaces().interface_type_list().interface_type():
                    base_interfaces.append(interface_type.getText())
                if base_interfaces:
                    struct_node["interfaces"] = base_interfaces
            
            # Add to appropriate container
            if self.current_namespace:
                self.current_namespace["body"].append(struct_node)
            else:
                self.nodes["statements"].append(struct_node)
            
            # Set current struct context
            previous_struct = self.current_struct
            self.current_struct = struct_node
            
            # Continue visiting child nodes
            result = self.visitChildren(ctx)
            
            # Restore previous struct context
            self.current_struct = previous_struct
            
            return result
        except Exception as e:
            logger.error(f"Error visiting struct definition at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def visitEnum_definition(self, ctx):
        """
        Visit enum definition node and collect enum information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the enum definition
            
        Returns:
            The result of visiting the enum's children nodes
        """
        try:
            # Extract the enum name
            enum_name = ctx.identifier().getText()
            
            # Extract enum modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)

            # Create a node representation for this enum
            enum_node = {
                "type": "Enum",
                "name": enum_name,
                "startLine": ctx.start.line,
                "modifiers": modifiers,
                "members": []
            }
            
            # Extract enum members
            if ctx.enum_body() and ctx.enum_body().enum_member_declaration():
                for member_ctx in ctx.enum_body().enum_member_declaration():
                    member_name = member_ctx.identifier().getText()
                    member_node = {
                        "name": member_name,
                        "startLine": member_ctx.start.line
                    }
                    # Extract value if present
                    if member_ctx.expression():
                        member_node["value"] = member_ctx.expression().getText()
                    enum_node["members"].append(member_node)
            
            # Add to appropriate container
            if self.current_namespace:
                self.current_namespace["body"].append(enum_node)
            else:
                self.nodes["statements"].append(enum_node)
            
            # Set current enum context
            previous_enum = self.current_enum
            self.current_enum = enum_node
            
            # Continue visiting child nodes
            result = self.visitChildren(ctx)
            
            # Restore previous enum context
            self.current_enum = previous_enum
            
            return result
        except Exception as e:
            logger.error(f"Error visiting enum definition at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None
    def visitTyped_member_declaration(self, ctx):
        """
        Visit typed member declaration node and extract common type information.
        This handles the type information for methods, properties, fields, etc.
    
        Args:
            ctx: The ANTLR4 parse tree context for the typed member declaration
        
        Returns:
        The result of visiting the declaration's children nodes
        """
        try:
            # Extract the type information to be used by child visitors
            if ctx.type_():
                # Store the type information in a shared location or context
                self.current_type_info = ctx.type_().getText()
        
                # Continue visiting child nodes
            return self.visitChildren(ctx)
        finally:
            # Clear the type info after children are processed
            self.current_type_info = None

    def visitMethod_declaration(self, ctx):
        """
        Visit method declaration node and collect method information.
        
        This method is called whenever the visitor encounters a method declaration
        in the C# parse tree. It extracts the method name and records its location.
        
        Args:
            ctx: The ANTLR4 parse tree context for the method declaration
            
        Returns:
            The result of visiting the method's children nodes
        """
        try:
            # Extract the method name
            method_name = ctx.method_member_name().getText()
            
            # Extract return type
            return_type = None
            
            # Check if return type exists using hasattr first
            if hasattr(ctx, "type_") and ctx.type_():
                return_type = ctx.type_().getText()
            elif hasattr(ctx, "return_type") and ctx.return_type():
                return_type = ctx.return_type().getText()
            elif hasattr(ctx, "VOID") and ctx.VOID():
                return_type = "void"
            
            elif hasattr(self, "current_type_info") and self.current_type_info:
                return_type = self.current_type_info
            else:
                return_type = "void"

            
            
            # Extract method modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)

            # Create method node
            method_node = {
                "type": "Method",
                "name": method_name,
                "startLine": ctx.start.line,
                "returnType": return_type,
                "modifiers": modifiers
            }
            
            # Extract parameters if present
            if hasattr(ctx, "formal_parameter_list") and ctx.formal_parameter_list():
                parameters = []
                for param in ctx.formal_parameter_list().fixed_parameters().fixed_parameter():
                    param_type = param.arg_declaration().type_().getText()
                    param_name = param.arg_declaration().identifier().getText()
                    param_node = {
                        "type": param_type,
                        "name": param_name
                    }
                    parameters.append(param_node)
                
                if parameters:
                    method_node["parameters"] = parameters
                    
            # Add method to appropriate container
            if self.current_class:
                self.current_class["body"].append(method_node)
            elif self.current_interface:
                self.current_interface["body"].append(method_node)
            elif self.current_struct:
                self.current_struct["body"].append(method_node)
            else:
                self.nodes["statements"].append(method_node)
            
            # Continue visiting child nodes
            return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting method declaration at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None
    

    def visitProperty_declaration(self, ctx):
        """
        Visit property declaration node and collect property information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the property declaration
            
        Returns:
            The result of visiting the property's children nodes
        """
        try:
            # Extract the property name
            property_name = ctx.member_name().getText()
            
            property_type = "<unknown>"
        
            # Check in current context first
            if hasattr(ctx, "type_") and ctx.type_() is not None:
                property_type = ctx.type_().getText()
            # Check parent context if type not found (handles typed_member_declaration)
            elif hasattr(ctx, "getParent") and ctx.getParent() is not None:
                parent = ctx.getParent()
                if hasattr(parent, "type_") and parent.type_() is not None:
                    property_type = parent.type_().getText()
            elif hasattr(self, "current_type_info") and self.current_type_info:
                property_type = self.current_type_info
            # Extract property modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)

            # Create property node
            property_node = {
                "type": "Property",
                "name": property_name,
                "propertyType": property_type,
                "startLine": ctx.start.line,
                "modifiers": modifiers,
                "accessors": [] 
            }
            
            # Extract accessors (get/set)
            
            if ctx.accessor_declarations():
                accessor_ctx_text = ctx.accessor_declarations().getText()
    
                # Check for 'get' accessor
                if 'get' in accessor_ctx_text.lower() or 'GET' in accessor_ctx_text:
                    property_node["accessors"].append("get")
    
                # Check for 'set' accessor
                if 'set' in accessor_ctx_text.lower() or 'SET' in accessor_ctx_text:
                    property_node["accessors"].append("set")
        
            # Add property to appropriate container
            if hasattr(self, "current_class") and self.current_class:
                self.current_class["body"].append(property_node)
            elif hasattr(self, "current_interface") and self.current_interface:
                self.current_interface["body"].append(property_node)
            elif hasattr(self, "current_struct") and self.current_struct:
                self.current_struct["body"].append(property_node)
            else:
                # Ensure nodes["statements"] exists
                if not hasattr(self, "nodes"):
                    self.nodes = {"statements": []}
                elif "statements" not in self.nodes:
                    self.nodes["statements"] = []
                self.nodes["statements"].append(property_node)
        
            # Continue visiting child nodes
            return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting property declaration at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def visitConstructor_declaration(self, ctx):
        """
        Visit constructor declaration node and collect constructor information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the constructor declaration
            
        Returns:
            The result of visiting the constructor's children nodes
        """
        try:
            # Extract the constructor name
            constructor_name = ctx.identifier().getText()
            
            # Extract constructor modifiers if present
            modifiers = self.extract_modifiers_from_parent(ctx)

            # Create constructor node
            constructor_node = {
                "type": "Constructor",
                "name": constructor_name,
                "startLine": ctx.start.line,
                "modifiers": modifiers
            }
            
            # Extract parameters if present
            if ctx.formal_parameter_list():
                parameters = []
                for param in ctx.formal_parameter_list().fixed_parameters().fixed_parameter():
                    param_type = param.arg_declaration().type_().getText()
                    param_name = param.arg_declaration().identifier().getText()
                    param_node = {
                        "type": param_type,
                        "name": param_name
                    }
                    parameters.append(param_node)
                
                if parameters:
                    constructor_node["parameters"] = parameters
            
            # Add constructor to appropriate container
            if self.current_class:
                self.current_class["body"].append(constructor_node)
            elif self.current_struct:
                self.current_struct["body"].append(constructor_node)
            else:
                self.nodes["statements"].append(constructor_node)
            
            # Continue visiting child nodes
            return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting constructor declaration at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None
    def visitDelegate_definition(self, ctx):
        """
        Parse delegate definitions according to the grammar rule.

        delegate_definition
            : DELEGATE return_type identifier variant_type_parameter_list? OPEN_PARENS formal_parameter_list? CLOSE_PARENS type_parameter_constraints_clauses?
            ';'
        """
        try:
            delegate_node = {
                "type": "Delegate",
                "name": ctx.identifier().getText(),
                "returnType": self.get_type(ctx.return_type()),
                "startLine": ctx.start.line,
                "modifiers": self.extract_modifiers_from_parent(ctx),
                "parameters": []
            }

            # Process parameters if present
            if ctx.formal_parameter_list():
                # Process fixed parameters
                if ctx.formal_parameter_list().fixed_parameters():
                    for param in ctx.formal_parameter_list().fixed_parameters().fixed_parameter():
                        param_info = {
                            "type": self.get_type(param.arg_declaration().type_()),
                            "name": param.arg_declaration().identifier().getText()
                        }
                        delegate_node["parameters"].append(param_info)
                
                # Process parameter array if present
                param_array = ctx.formal_parameter_list().parameter_array() if hasattr(ctx.formal_parameter_list(), 'parameter_array') else None
                if param_array:
                    param_info = {
                        "type": self.get_type(param_array.array_type()),
                        "name": param_array.identifier().getText(),
                        "isParams": True
                    }
                    delegate_node["parameters"].append(param_info)

            # Add delegate to appropriate container
            if hasattr(self, "current_class") and self.current_class:
                self.current_class["body"].append(delegate_node)
            elif hasattr(self, "current_namespace") and self.current_namespace:
                self.current_namespace["body"].append(delegate_node)
            else:
                self.nodes["statements"].append(delegate_node)
            
            # Continue visiting child nodes
            return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting delegate definition at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def visitEvent_declaration(self, ctx):
        """
        Parse event declarations according to the grammar rule.

        event_declaration
            : EVENT type_ (
            variable_declarators ';'
            | member_name OPEN_BRACE event_accessor_declarations CLOSE_BRACE
        )
        """
        try:
            event_type = self.get_type(ctx.type_())
            modifiers = self.extract_modifiers_from_parent(ctx)
            
            # Check which format is being used
            if ctx.variable_declarators():
                # This is the variable_declarators format (multiple events possible)
                event_nodes = []
                
                # Process each variable declarator as a separate event
                for declarator in ctx.variable_declarators().variable_declarator():
                    event_node = {
                        "type": "Event",
                        "name": declarator.identifier().getText(),
                        "eventType": event_type,
                        "startLine": ctx.start.line,
                        "modifiers": modifiers
                    }
                
                    # Check if event has initializer
                    if declarator.variable_initializer():
                        event_node["hasInitializer"] = True
                    
                    event_nodes.append(event_node)
                    
                    # Add each event to appropriate container
                    if hasattr(self, "current_class") and self.current_class:
                        self.current_class["body"].append(event_node)
                    elif hasattr(self, "current_struct") and self.current_struct:
                        self.current_struct["body"].append(event_node)
                    elif hasattr(self, "current_interface") and self.current_interface:
                        self.current_interface["body"].append(event_node)
                    else:
                        self.nodes["statements"].append(event_node)
                
                # Return list of event nodes
                return self.visitChildren(ctx)
            else:
                # This is the event with accessor declarations format
                event_node = {
                    "type": "Event",
                    "name": ctx.member_name().getText(),
                    "eventType": event_type,
                    "startLine": ctx.start.line,
                    "modifiers": modifiers,
                    "accessors": []
                }
            
                # Process event accessors
                if ctx.event_accessor_declarations():
                    # Add add accessor if present
                    add_accessor = ctx.event_accessor_declarations().add_accessor_declaration()
                    if add_accessor:
                        event_node["accessors"].append("add")
                
                    # Add remove accessor if present
                    remove_accessor = ctx.event_accessor_declarations().remove_accessor_declaration()
                    if remove_accessor:
                        event_node["accessors"].append("remove")
                
                # Add event to appropriate container
                if hasattr(self, "current_class") and self.current_class:
                    self.current_class["body"].append(event_node)
                elif hasattr(self, "current_struct") and self.current_struct:
                    self.current_struct["body"].append(event_node)
                elif hasattr(self, "current_interface") and self.current_interface:
                    self.current_interface["body"].append(event_node)
                else:
                    self.nodes["statements"].append(event_node)
                
                return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting event declaration at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def visitField_declaration(self, ctx):
        """
        Parse field declarations according to the grammar rule.

        field_declaration
            : variable_declarators ';'
        """
        try:
            field_nodes = []
        
            # Field declarations in C# require a type, which is typically 
            # associated with the parent class_member_declaration
            # We need to get the type from the parent context
            parent_ctx = ctx.parentCtx  # Get parent context (class_member_declaration)
        
            # Extract field type from parent context
            field_type = "Unknown"  # Default value
            if hasattr(parent_ctx, "type_") and parent_ctx.type_():
                field_type = self.get_type(parent_ctx.type_())
        
            # Extract modifiers from parent context
            modifiers = self.extract_modifiers_from_parent(ctx)
        
            # Process each variable declarator as a separate field
            for declarator in ctx.variable_declarators().variable_declarator():
                field_node = {
                    "type": "Field",
                    "name": declarator.identifier().getText(),
                    "fieldType": field_type,
                    "startLine": ctx.start.line,
                    "modifiers": modifiers
                }
            
                # Check if field is constant
                if "const" in modifiers:
                    field_node["isConstant"] = True
            
                # Check if field is readonly
                if "readonly" in modifiers:
                    field_node["isReadOnly"] = True
            
                # Check if field has initializer
                if declarator.variable_initializer():
                    field_node["hasInitializer"] = True
            
                field_nodes.append(field_node)
                
                # Add each field to appropriate container
                if hasattr(self, "current_class") and self.current_class:
                    self.current_class["body"].append(field_node)
                elif hasattr(self, "current_struct") and self.current_struct:
                    self.current_struct["body"].append(field_node)
                else:
                    self.nodes["statements"].append(field_node)
        
            # Continue visiting child nodes
            return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting field declaration at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None

    def get_type(self, ctx):
        """
        Extract type information from a type context.
        
        Args:
            ctx: The type context from the parser
            
        Returns:
            str: A string representation of the type
        """
        try:
            if ctx is None:
                return "void"
                
            # Handle different type contexts based on their structure
            if hasattr(ctx, 'getText'):
                return ctx.getText()
            elif hasattr(ctx, 'base_type') and ctx.base_type():
                return ctx.base_type().getText()
            elif hasattr(ctx, 'class_type') and ctx.class_type():
                return ctx.class_type().getText()
            elif hasattr(ctx, 'array_type') and ctx.array_type():
                # For array types, get the element type and add []
                element_type = self.get_type(ctx.array_type().base_type())
                return f"{element_type}[]"
            elif hasattr(ctx, 'predefined_type') and ctx.predefined_type():
                return ctx.predefined_type().getText()
            else:
                # Default case - just get the text content
                return ctx.getText()
        except Exception as e:
            logger.error(f"Error extracting type: {str(e)}")
            return "unknown"

    def visitUsing_directive(self, ctx):
        """
        Visit using directive node to collect import information.
        
        Args:
            ctx: The ANTLR4 parse tree context for the using directive
            
        Returns:
            The result of visiting the using directive's children nodes
        """
        try:
            # Extract the namespace or type being imported
            namespace_or_type = ctx.namespace_or_type_name().getText()
            
            # Create using directive node
            using_node = {
                "type": "UsingDirective",
                "target": namespace_or_type,
                "startLine": ctx.start.line
            }
            
            # Add using directive to the program statements
            self.nodes["statements"].append(using_node)
            
            # Continue visiting child nodes
            return self.visitChildren(ctx)
        except Exception as e:
            logger.error(f"Error visiting using directive at line {ctx.start.line}: {str(e)}")
            # Recover by returning None and continuing parsing
            return None


def parse_cs_file(file_path: str) -> list[dict]:
    """
    Parse a .cs file and return a list of AST node dictionaries.
    
    This function uses ANTLR4-generated C# parser to parse the input file
    and extract structure information using the ASTCollector visitor.
    
    Args:
        file_path: Path to the C# file to parse
        
    Returns:
        list[dict]: A list of AST nodes, where each node is a dictionary
                   with keys like 'type', 'name', and 'startLine'
    
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        Exception: If there are parsing errors
    """
    try:
        logger.info(f"Starting to parse file: {file_path}")
        data = FileStream(file_path, encoding="utf-8")
        lexer = CSharpLexer(data)
        stream = CommonTokenStream(lexer)
        parser = CSharpParser(stream)
        tree = parser.compilation_unit()
        visitor = ASTCollector()
        
        # Visit the parse tree to collect AST nodes
        try:
            visitor.visit(tree)
            
            # Count all nodes including nested ones
            def count_nodes(node_list):
                count = len(node_list)
                for node in node_list:
                    if "body" in node:
                        count += count_nodes(node["body"])
                    elif "members" in node:
                        count += len(node["members"])
                return count
            
            total_nodes = count_nodes(visitor.nodes["statements"])
            logger.info(f"Parsing completed. Found {total_nodes} total nodes across all structures.")
            logger.debug(f"Top-level nodes: {len(visitor.nodes['statements'])}")
            
            # Log types of entities found
            entity_types = {}
            def collect_entity_types(node_list):
                for node in node_list:
                    if "type" in node:
                        entity_type = node["type"]
                        if entity_type not in entity_types:
                            entity_types[entity_type] = 0
                        entity_types[entity_type] += 1
                    
                    if "body" in node:
                        collect_entity_types(node["body"])
            
            collect_entity_types(visitor.nodes["statements"])
            logger.info(f"Found entity types: {entity_types}")
            
            logger.debug(f"Nodes: {visitor.nodes}")
            return visitor.nodes["statements"]
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            # Return empty list if parsing fails
            return []
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error when processing file {file_path}: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def serialize_to_json(ast_nodes: list[dict], output_path: str) -> None:
    """
    Serialize AST nodes to a JSON file.
    
    This function takes the parsed AST nodes and writes them to a JSON file
    for persistence or further processing. The JSON is formatted with indentation
    for readability.
    
    Args:
        ast_nodes: List of AST node dictionaries containing parsed C# entities
        output_path: Path to the output JSON file
        
    Raises:
        IOError: If the file cannot be written due to permissions or disk space
        TypeError: If AST nodes cannot be serialized to JSON
    """
    try:
        # Log the start of serialization process
        logger.info(f"Serializing {len(ast_nodes)} nodes to {output_path}")
        
        # Open file with UTF-8 encoding to properly handle C# symbols
        with open(output_path, "w", encoding="utf-8") as f:
            # Write with indentation for human readability
            json.dump(ast_nodes, f, indent=2)
            
        # Log successful completion
        logger.info(f"Serialization complete. Output file created: {output_path}")
    except Exception as e:
        logger.error(f"Error during serialization to {output_path}: {str(e)}")
        raise
