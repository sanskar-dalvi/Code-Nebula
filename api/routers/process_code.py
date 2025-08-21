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

# Import the pipeline components
from pipeline.cs_parser import parse_cs_file, serialize_to_json
from pipeline.enrich import enrich_ast
from pipeline.insert_graph import ingest_enriched_json

logger = logging.getLogger(__name__)
router = APIRouter()

class CodeInput(BaseModel):
    """Input model for code processing endpoint."""
    file_path: str

@router.post("/process")
async def process_code(input: CodeInput):
    """Process a C# file through the complete pipeline."""
    if not os.path.isfile(input.file_path):
        logger.error(f"File not found: {input.file_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    if not input.file_path.endswith('.cs'):
        logger.warning(f"File may not be C# source: {input.file_path}")
    
    try:
        # Parse
        logger.info(f"Parsing file: {input.file_path}")
        ast_nodes = parse_cs_file(input.file_path)
        serialize_to_json(ast_nodes, "parsed_output/api_ast.json")

        # Enrich
        logger.info(f"Enriching AST: {input.file_path}")
        enrich_ast(ast_nodes, "enriched_output/api_enriched.json")

        # Ingest
        logger.info(f"Ingesting enriched data: {input.file_path}")
        ingest_enriched_json("enriched_output/api_enriched.json")
        
        return {"status": "success", "message": "Graph updated in Neo4j."}
    
    except Exception as e:
        logger.exception(f"Error processing {input.file_path}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process code: {str(e)}"
        )
