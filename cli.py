"""CLI interface for the C# parser with batch processing capabilities."""
import argparse
import logging
import sys
import os
from pathlib import Path

# Import individual pipeline components for legacy functionality
from pipeline.cs_parser import parse_cs_file, serialize_to_json
from pipeline.enrich import enrich_ast
from pipeline.insert_graph import ingest_enriched_json

# Import for batch mode ETL pipeline
from pipeline.run_etl import ETLRunner, run_etl_pipeline

# Import centralized logging module
from logs.logger import get_logger, configure_root_logger

# Configure logging using centralized logger
configure_root_logger(level=logging.INFO)
logger = get_logger("csharp-parser")


def main():
    """
    Main entry point for the CLI application.
    Orchestrates the full processing pipeline from C# code to Neo4j graph.
    
    Two modes are supported:
    1. Legacy mode: Process individual C# files one by one (original behavior)
    2. Batch mode: Process entire directories or zip files using the ETL pipeline
    """
    try:
        # Set up command line argument parsing
        parser = argparse.ArgumentParser(description="Run full C# → Neo4j pipeline.")
        
        # Input path argument
        parser.add_argument(
            "input_path",
            nargs="?",
            default="input_code",
            help="Path to a .cs file, directory of .cs files, or .zip archive (default: input_code)"
        )
        
        # Common options
        parser.add_argument("-v", "--verbose", action="store_true", 
                           help="Enable verbose output")
        
        # Mode selection
        parser.add_argument("--batch", action="store_true",
                           help="Use batch ETL pipeline mode (recommended for directories or zip files)")
        
        # Batch mode options
        parser.add_argument("--skip", nargs="+", choices=["extract", "parse", "enrich", "load", "archive"],
                           help="In batch mode, skip specified pipeline phases")
        parser.add_argument("--output-base", dest="output_base",
                          help="In batch mode, base directory for outputs (default: project root)")
        
        args = parser.parse_args()

        # Set verbose logging if requested
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            # Update the root logger too
            logging.getLogger().setLevel(logging.DEBUG)

        # Validate input path exists
        input_path = args.input_path
        if not os.path.exists(input_path):
            parser.error(f"Path not found: {input_path}")

        # Check if we should use batch mode
        if args.batch or input_path.lower().endswith('.zip'):
            # Use the batch ETL pipeline
            logger.info(f"Starting batch ETL pipeline for {input_path}")
            
            try:
                # Run the ETL pipeline with provided options
                stats = run_etl_pipeline(
                    input_path=input_path,
                    output_base=args.output_base,
                    skip_phases=args.skip
                )
                
                # Log the results
                phases_str = ", ".join(stats.get('phases_completed', []))
                logger.info(f"Batch ETL pipeline completed with status: {stats.get('status')}")
                logger.info(f"Phases completed: {phases_str}")
                logger.info(f"Files processed: {stats.get('files_processed', 0)}")
                
                # Show where to find logs
                logger.info("ETL logs available with: python logs/logger.py etl")
                logger.info("LLM logs available with: python logs/logger.py llm")
                
                if "enrich" in stats.get("phases_completed", []) and stats.get("files_processed", 0) > 0:
                    logger.info("✅ Pipeline complete. Check Neo4j for results.")
                else:
                    logger.warning("⚠️ Pipeline completed but may not have processed all phases.")
                    
            except Exception as e:
                logger.error(f"Batch ETL pipeline failed: {e}")
                sys.exit(1)
                
        else:
            # Original single file mode
            logger.info(f"Using legacy mode for processing {input_path}")
            
            # Collect .cs files from the given path
            if os.path.isdir(input_path):
                cs_files = [
                    os.path.join(input_path, fn)
                    for fn in os.listdir(input_path)
                    if fn.lower().endswith(".cs")
                ]
                if not cs_files:
                    parser.error(f"No .cs files found in directory: {input_path}")
            else:
                cs_files = [input_path]
    
            for cs_file in cs_files:
                logger.info(f"Starting pipeline processing for {cs_file}")
    
                # Ensure output directories exist
                Path("parsed_output").mkdir(exist_ok=True)
                Path("enriched_output").mkdir(exist_ok=True)
    
                # 1. Parse to AST JSON
                # Convert C# code to Abstract Syntax Tree representation
                logger.info("Step 1: Parsing C# to AST")
                try:
                    ast_nodes = parse_cs_file(cs_file)
                    # Save the raw AST to JSON file for inspection/debugging
                    ast_output_path = "parsed_output/cli_ast.json"
                    serialize_to_json(ast_nodes, ast_output_path)
                    logger.debug(f"AST saved to {ast_output_path}")
                except Exception as e:
                    logger.error(f"Failed to parse C# file: {e}")
                    sys.exit(1)
    
                # 2. Enrich to enriched JSON
                # Use LLM to add additional context, summaries and relationships to the AST
                logger.info("Step 2: Enriching AST with LLM")
                try:
                    enriched_output_path = "enriched_output/cli_enriched.json"
                    enrich_ast(ast_nodes, enriched_output_path)
                    logger.debug(f"Enriched AST saved to {enriched_output_path}")
                except Exception as e:
                    logger.error(f"Failed to enrich AST: {e}")
                    sys.exit(1)
    
                # 3. Ingest to Neo4j
                # Create nodes and relationships in Neo4j graph database based on enriched data
                logger.info("Step 3: Ingesting to Neo4j")
                try:
                    ingest_enriched_json(enriched_output_path)
                    logger.info("✅ Pipeline complete. Check Neo4j for results.")
                except Exception as e:
                    logger.error(f"Failed to ingest to Neo4j: {e}")
                    sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()