"""Router for ETL pipeline trigger endpoints.

This module defines the FastAPI router for triggering the ETL pipeline.
It exposes a POST endpoint that takes a folder or ZIP file path and runs the entire ETL pipeline.
"""
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Optional, List

# Import the ETL runner
from pipeline.run_etl import run_etl_pipeline

# Configure logger for this module
logger = logging.getLogger(__name__)

# Create the FastAPI router that will be included in the main app
router = APIRouter()


class ETLInput(BaseModel):
    """Input model for ETL trigger endpoint.
    
    Attributes:
        input_path (str): The absolute path to the folder or ZIP file containing C# code.
                          This must exist on the server's filesystem.
        output_base (Optional[str]): The base directory for outputs. Defaults to project root if not provided.
        skip_phases (Optional[List[str]]): List of phases to skip. Valid values are:
                                          'extract', 'parse', 'enrich', 'load', 'archive'.
    """
    input_path: str
    output_base: Optional[str] = None
    skip_phases: Optional[List[str]] = None
    
    @validator('input_path')
    def validate_input_path(cls, v):
        """Validate that the input path exists and is either a folder or a ZIP file."""
        if not os.path.exists(v):
            raise ValueError(f"Input path '{v}' does not exist")
        
        if not (os.path.isdir(v) or v.lower().endswith('.zip')):
            raise ValueError(f"Input path must be a directory or a ZIP file: {v}")
        
        return v
    
    @validator('skip_phases')
    def validate_skip_phases(cls, v):
        """Validate that skip_phases contains only valid phase names."""
        if v is None:
            return v
            
        valid_phases = {'extract', 'parse', 'enrich', 'load', 'archive'}
        invalid_phases = [phase for phase in v if phase not in valid_phases]
        
        if invalid_phases:
            raise ValueError(f"Invalid skip phases: {', '.join(invalid_phases)}. "
                           f"Valid phases are: {', '.join(valid_phases)}")
        
        return v


@router.post("/trigger-etl")
async def trigger_etl(input: ETLInput):
    """
    Trigger the ETL pipeline for processing C# code.
    
    This endpoint runs the complete ETL pipeline:
    1. Extract: Extracts files from a ZIP archive or uses the directory directly
    2. Parse: Parses C# files into AST nodes
    3. Enrich: Enriches the AST with additional information
    4. Load: Loads the enriched data into Neo4j
    5. Archive: Archives the processed files and logs
    
    Args:
        input (ETLInput): Object containing the input_path and optional parameters
    
    Returns:
        Dict with ETL execution statistics and results
    
    Raises:
        HTTPException: If the ETL process fails
    """
    try:
        logger.info(f"Triggering ETL pipeline with input path: {input.input_path}")
        result = run_etl_pipeline(
            input_path=input.input_path,
            output_base=input.output_base,
            skip_phases=input.skip_phases
        )
        return {
            "status": "success",
            "message": "ETL pipeline completed successfully",
            "result": result
        }
    except Exception as e:
        logger.error(f"ETL pipeline failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"ETL pipeline failed: {str(e)}"
        )
