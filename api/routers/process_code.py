"""Router for code processing endpoints.

This module defines the FastAPI router for processing C# code files through the pipeline.
It exposes a POST endpoint that takes a file path, and runs the entire pipeline:
1. Parse the C# file into AST nodes
2. Enrich the AST with additional metadata using LLM
3. Ingest the enriched data into Neo4j graph database
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import the pipeline components we'll need to process the code
from pipeline.cs_parser import parse_cs_file, serialize_to_json
from pipeline.enrich import enrich_ast
from pipeline.insert_graph import ingest_enriched_json

# Configure logger for this module
logger = logging.getLogger(__name__)

# Create the FastAPI router that will be included in the main app
router = APIRouter()


class CodeInput(BaseModel):
    """Input model for code processing endpoint.
    
    Attributes:
        file_path (str): The absolute path to the C# file that should be processed.
                         This file must exist on the server's filesystem.
    """
    file_path: str


@router.post("/process")
async def process_code(input: CodeInput):
    """
    Process a C# file through the complete pipeline.
    
    This endpoint performs the entire processing pipeline:
    1. Parse the file into AST nodes using ANTLR (handled by Haritha's code)
    2. Enrich the AST with additional information using LLM (handled by Darshan's code)
    3. Ingest the enriched data into Neo4j (handled by Haritha's code)
    
    Args:
        input (CodeInput): Object containing the file_path to process
    
    Returns:
        Dict with status and message indicating success
        
    Raises:
        HTTPException 404: If the file doesn't exist
        HTTPException 500: If any step in the pipeline fails
    """
    # Step 0: Validate input file exists
    if not os.path.isfile(input.file_path):
        logger.error(f"File not found: {input.file_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # Validate file is a C# file (by extension)
    if not input.file_path.endswith('.cs'):
        logger.warning(f"File may not be C# source: {input.file_path}")
        # Continue processing but log warning
    
    try:
        # Step 1: Parse the C# file into AST nodes
        # This calls Haritha's implementation in cs_parser.py
        logger.info(f"Parsing file: {input.file_path}")
        ast_nodes = parse_cs_file(input.file_path)
        # Save the raw AST as JSON for debugging/reference
        serialize_to_json(ast_nodes, "parsed_output/api_ast.json")

        # Step 2: Enrich the AST with LLM-generated metadata
        # This calls Darshan's implementation in enrich.py
        logger.info(f"Enriching AST from file: {input.file_path}")
        enrich_ast(ast_nodes, "enriched_output/api_enriched.json")

        # Step 3: Ingest the enriched data into Neo4j
        # This calls Haritha's implementation in insert_graph.py
        logger.info(f"Ingesting enriched data from file: {input.file_path}")
        ingest_enriched_json("enriched_output/api_enriched.json")
        
        # Log successful completion
        logger.info(f"Successfully processed file: {input.file_path}")
        return {"status": "success", "message": "Graph updated in Neo4j."}
    
    except Exception as e:
        # Log any exceptions that occur during processing
        logger.exception(f"Error processing file {input.file_path}: {str(e)}")
        # Return a 500 error with details about what went wrong
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process code: {str(e)}"
        )