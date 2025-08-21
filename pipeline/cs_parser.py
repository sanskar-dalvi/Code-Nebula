"""C# Parser using ANTLR.

This module provides functions to parse C# source files into AST nodes.
It uses the ANTLR4 C# grammar and a visitor pattern to extract information.
"""

import os
import json
from antlr4 import FileStream, CommonTokenStream
from grammar.CSharpLexer import CSharpLexer
from grammar.CSharpParser import CSharpParser

# TODO: implement visitor to walk the parse tree
# For now, we provide a simple stub if full parser is not ready

def parse_cs_file(filepath: str):
    """Parse a C# source file into AST nodes."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"C# file not found: {filepath}")

    try:
        # Real ANTLR pipeline
        input_stream = FileStream(filepath, encoding="utf-8")
        lexer = CSharpLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CSharpParser(stream)
        tree = parser.compilation_unit()

        # TODO: walk the parse tree with custom visitor
        # Currently returning stub result
        return [{"class": "SampleClass", "method": "SampleMethod"}]

    except Exception as e:
        # fallback stub
        print(f"[Parser] Error parsing {filepath}, falling back to stub. Error: {e}")
        return [{"class": "SampleClass", "method": "SampleMethod"}]


def serialize_to_json(ast_nodes, out_path: str):
    """Save AST nodes to JSON file for debugging/reference."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(ast_nodes, f, indent=2)
    print(f"[Parser] AST written to {out_path}")
