"""
ETL Pipeline Orchestrator

This module orchestrates the complete ETL (Extract, Transform, Load) pipeline
for C# code analysis. It coordinates:
1. Extract: Unzip/copy source files to raw/
2. Parse: Convert C# files to AST JSON in staging/ast/
3. Enrich: Add LLM metadata to AST and save to curated/
4. Load: Insert enriched data into Neo4j graph database
5. Archive: Move processed files from raw/ to archive/

This module implements task D2 from the batch ETL requirements.
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import argparse

# Import pipeline components
from .extract import extract_source, validate_raw
from .cs_parser import parse_cs_file, serialize_to_json
from .enrich import enrich_ast
from .insert_graph import ingest_enriched_json
from .archive import archive_processed_files

# Import centralized logging module
from logs.logger import get_logger, log_etl_summary

# Get logger for this module
logger = get_logger(__name__)

# Default directories relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DEFAULT_DIRS = {
    'input': PROJECT_ROOT / 'input_code',
    'raw': PROJECT_ROOT / 'raw', 
    'staging_ast': PROJECT_ROOT / 'staging' / 'ast',
    'curated': PROJECT_ROOT / 'curated',
    'logs': PROJECT_ROOT / 'logs' / 'etl',
    'archive': PROJECT_ROOT / 'archive'
}


class ETLPipelineError(Exception):
    """Custom exception for ETL pipeline errors"""
    pass


class ETLRunner:
    """
    Main ETL Pipeline Runner
    
    Orchestrates the complete data pipeline from raw C# source code
    to enriched graph data in Neo4j.
    """
    
    def __init__(self, 
                 input_path: Optional[str] = None,
                 output_base: Optional[str] = None,
                 skip_phases: Optional[List[str]] = None):
        """
        Initialize ETL Runner
        
        Args:
            input_path: Path to input zip/folder (defaults to input_code/)
            output_base: Base directory for outputs (defaults to project root)
            skip_phases: List of phases to skip ['extract', 'parse', 'enrich', 'load']
        """
        self.input_path = input_path
        self.skip_phases = skip_phases or []
        
        # Set up directories
        if output_base:
            base = Path(output_base)
            self.dirs = {
                'raw': base / 'raw',
                'staging_ast': base / 'staging' / 'ast', 
                'curated': base / 'curated',
                'logs': base / 'logs' / 'etl',
                'archive': base / 'archive'  # Add archive directory
            }
        else:
            self.dirs = DEFAULT_DIRS.copy()
            
        # Create required directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # ETL run metadata
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = {
            'run_id': self.run_id,
            'start_time': datetime.now().isoformat(),
            'phases_completed': [],
            'phases_skipped': self.skip_phases,
            'files_processed': 0,
            'nodes_created': 0,
            'errors': []
        }
        
        logger.info(f"ETL Runner initialized - Run ID: {self.run_id}")
        logger.info(f"Skip phases: {self.skip_phases}")
        
    def run(self) -> Dict:
        """
        Execute the complete ETL pipeline
        
        Returns:
            Dict: ETL execution statistics and results
        """
        try:
            logger.info("=" * 60)
            logger.info(f"Starting ETL Pipeline Run: {self.run_id}")
            logger.info("=" * 60)
            
            # Phase 1: Extract
            if 'extract' not in self.skip_phases:
                self._extract_phase()
            else:
                logger.info("Skipping extract phase")
                self.stats['phases_skipped'].append('extract')
                
            # Phase 2: Parse  
            if 'parse' not in self.skip_phases:
                self._parse_phase()
            else:
                logger.info("Skipping parse phase")
                self.stats['phases_skipped'].append('parse')
                
            # Phase 3: Enrich
            if 'enrich' not in self.skip_phases:
                self._enrich_phase()
            else:
                logger.info("Skipping enrich phase")
                self.stats['phases_skipped'].append('enrich')
                
            # Phase 4: Load
            if 'load' not in self.skip_phases:
                self._load_phase()
            else:
                logger.info("Skipping load phase")
                self.stats['phases_skipped'].append('load')
                
            # Phase 5: Archive
            if 'archive' not in self.skip_phases:
                self._archive_phase()
            else:
                logger.info("Skipping archive phase")
                self.stats['phases_skipped'].append('archive')
                
            # Finalize
            self.stats['end_time'] = datetime.now().isoformat()
            self.stats['status'] = 'SUCCESS'
            
            logger.info("=" * 60)
            logger.info(f"ETL Pipeline Completed Successfully: {self.run_id}")
            logger.info(f"Files processed: {self.stats['files_processed']}")
            logger.info(f"Phases completed: {self.stats['phases_completed']}")
            logger.info("=" * 60)
            
        except Exception as e:
            self.stats['end_time'] = datetime.now().isoformat()
            self.stats['status'] = 'FAILED'
            self.stats['errors'].append(str(e))
            
            logger.error(f"ETL Pipeline Failed: {e}")
            raise ETLPipelineError(f"ETL Pipeline failed: {e}") from e
            
        finally:
            # Always save run statistics
            self._save_run_stats()
            
        return self.stats
        
    def _extract_phase(self) -> None:
        """Phase 1: Extract source files from zip/folder to raw/"""
        logger.info("Phase 1: Extract - Starting")
        
        try:
            # Extract files using the extract module
            extracted_files = extract_source(
                input_path=self.input_path,
                raw_dir=str(self.dirs['raw'])
            )
            
            # Validate extraction results
            validate_raw(str(self.dirs['raw']), allowed_exts=('.cs',))
            
            self.stats['files_extracted'] = len(extracted_files)
            self.stats['phases_completed'].append('extract')
            
            logger.info(f"Phase 1: Extract - Completed ({len(extracted_files)} files)")
            
        except Exception as e:
            error_msg = f"Extract phase failed: {e}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            raise ETLPipelineError(error_msg) from e
            
    def _parse_phase(self) -> None:
        """Phase 2: Parse C# files to AST JSON"""
        logger.info("Phase 2: Parse - Starting")
        
        try:
            # Find all .cs files in raw directory
            cs_files = []
            for root, _, files in os.walk(self.dirs['raw']):
                for file in files:
                    if file.endswith('.cs'):
                        cs_files.append(os.path.join(root, file))
                        
            if not cs_files:
                raise ETLPipelineError("No .cs files found in raw directory")
                
            logger.info(f"Found {len(cs_files)} C# files to parse")
            
            # Parse each file and save AST JSON
            total_nodes = 0
            parsed_files = []
            
            for cs_file in cs_files:
                try:
                    # Parse the C# file
                    ast_nodes = parse_cs_file(cs_file)
                    
                    # Generate output filename
                    rel_path = os.path.relpath(cs_file, self.dirs['raw'])
                    output_name = rel_path.replace('/', '_').replace('\\', '_').replace('.cs', '_ast.json')
                    output_path = self.dirs['staging_ast'] / output_name
                    
                    # Add file metadata to each node
                    for node in ast_nodes:
                        node['filePath'] = rel_path
                        node['sourceFile'] = os.path.basename(cs_file)
                        
                    # Save AST JSON
                    serialize_to_json(ast_nodes, str(output_path))
                    
                    total_nodes += len(ast_nodes)
                    parsed_files.append({
                        'source_file': rel_path,
                        'ast_file': output_name,
                        'nodes_count': len(ast_nodes)
                    })
                    
                    logger.info(f"Parsed {cs_file} -> {len(ast_nodes)} nodes")
                    
                except Exception as e:
                    error_msg = f"Failed to parse {cs_file}: {e}"
                    self.stats['errors'].append(error_msg)
                    logger.warning(error_msg)
                    continue
                    
            self.stats['files_processed'] = len(parsed_files)
            self.stats['total_nodes_parsed'] = total_nodes
            self.stats['parsed_files'] = parsed_files
            self.stats['phases_completed'].append('parse')
            
            logger.info(f"Phase 2: Parse - Completed ({len(parsed_files)} files, {total_nodes} nodes)")
            
        except Exception as e:
            error_msg = f"Parse phase failed: {e}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            raise ETLPipelineError(error_msg) from e
            
    def _enrich_phase(self) -> None:
        """Phase 3: Enrich AST with LLM metadata"""
        logger.info("Phase 3: Enrich - Starting")
        
        try:
            # Find all AST JSON files in staging
            ast_files = list(self.dirs['staging_ast'].glob('*_ast.json'))
            
            if not ast_files:
                raise ETLPipelineError("No AST JSON files found in staging directory")
                
            logger.info(f"Found {len(ast_files)} AST files to enrich")
            
            enriched_files = []
            total_enriched_nodes = 0
            
            for ast_file in ast_files:
                try:
                    # Load AST data
                    with open(ast_file, 'r', encoding='utf-8') as f:
                        ast_nodes = json.load(f)
                        
                    if not ast_nodes:
                        logger.warning(f"Empty AST file: {ast_file}")
                        continue
                        
                    # Generate enriched output filename
                    enriched_name = ast_file.name.replace('_ast.json', '_enriched.json')
                    enriched_path = self.dirs['curated'] / enriched_name
                    
                    # Enrich the AST with LLM metadata
                    enrichment_result = enrich_ast(ast_nodes, str(enriched_path))
                    
                    enriched_files.append({
                        'ast_file': ast_file.name,
                        'enriched_file': enriched_name,
                        'nodes_enriched': len(ast_nodes),
                        'enrichment_result': enrichment_result
                    })
                    
                    total_enriched_nodes += len(ast_nodes)
                    
                    logger.info(f"Enriched {ast_file.name} -> {enriched_name}")
                    
                except Exception as e:
                    error_msg = f"Failed to enrich {ast_file}: {e}"
                    self.stats['errors'].append(error_msg)
                    logger.warning(error_msg)
                    continue
                    
            self.stats['files_enriched'] = len(enriched_files)
            self.stats['total_nodes_enriched'] = total_enriched_nodes  
            self.stats['enriched_files'] = enriched_files
            self.stats['phases_completed'].append('enrich')
            
            logger.info(f"Phase 3: Enrich - Completed ({len(enriched_files)} files, {total_enriched_nodes} nodes)")
            
        except Exception as e:
            error_msg = f"Enrich phase failed: {e}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            raise ETLPipelineError(error_msg) from e
            
    def _load_phase(self) -> None:
        """Phase 4: Load enriched data into Neo4j"""
        logger.info("Phase 4: Load - Starting")
        
        try:
            # Find all enriched JSON files
            enriched_files = list(self.dirs['curated'].glob('*_enriched.json'))
            
            if not enriched_files:
                raise ETLPipelineError("No enriched JSON files found in curated directory")
                
            logger.info(f"Found {len(enriched_files)} enriched files to load into Neo4j")
            
            # Load each enriched file into Neo4j
            loaded_files = []
            
            for enriched_file in enriched_files:
                try:
                    # Use the insert_graph module to load into Neo4j
                    ingest_enriched_json(str(enriched_file))
                    
                    loaded_files.append(enriched_file.name)
                    logger.info(f"Loaded {enriched_file.name} into Neo4j")
                    
                except Exception as e:
                    error_msg = f"Failed to load {enriched_file}: {e}"
                    self.stats['errors'].append(error_msg)
                    logger.warning(error_msg)
                    continue
                    
            self.stats['files_loaded'] = len(loaded_files)
            self.stats['loaded_files'] = loaded_files
            self.stats['phases_completed'].append('load')
            
            logger.info(f"Phase 4: Load - Completed ({len(loaded_files)} files loaded into Neo4j)")
            
        except Exception as e:
            error_msg = f"Load phase failed: {e}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            raise ETLPipelineError(error_msg) from e
            
    def _archive_phase(self) -> None:
        """Phase 5: Archive processed raw files"""
        logger.info("Phase 5: Archive - Starting")
        
        try:
            # Archive all processed files from raw to archive directory
            files_archived, archived_items = archive_processed_files(
                raw_dir=str(self.dirs['raw']),
                archive_dir=str(self.dirs['archive']),
                run_id=self.run_id
            )
            
            if files_archived > 0:
                self.stats['files_archived'] = files_archived
                self.stats['archived_items'] = archived_items
                self.stats['phases_completed'].append('archive')
                
                logger.info(f"Phase 5: Archive - Completed ({files_archived} items archived)")
            else:
                logger.warning("No files were archived - raw directory may be empty")
                
        except Exception as e:
            error_msg = f"Archive phase failed: {e}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            # Don't raise exception for archiving errors - this is a non-critical phase
            # and shouldn't fail the entire pipeline if previous phases succeeded
            
    def _save_run_stats(self) -> None:
        """Save ETL run statistics to logs directory"""
        try:
            # Use the centralized logging module to save ETL stats
            log_file = log_etl_summary(self.run_id, self.stats)
            
            if log_file:
                logger.info(f"ETL run statistics saved to: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save run statistics: {e}")


def run_etl_pipeline(input_path: Optional[str] = None,
                    output_base: Optional[str] = None, 
                    skip_phases: Optional[List[str]] = None) -> Dict:
    """
    Convenience function to run the complete ETL pipeline
    
    Args:
        input_path: Path to input zip/folder (defaults to input_code/)
        output_base: Base directory for outputs (defaults to project root)
        skip_phases: List of phases to skip ['extract', 'parse', 'enrich', 'load', 'archive']
        
    Returns:
        Dict: ETL execution statistics and results
    """
    runner = ETLRunner(input_path=input_path, 
                      output_base=output_base,
                      skip_phases=skip_phases)
    return runner.run()


def main():
    """CLI entry point for ETL pipeline"""
    parser = argparse.ArgumentParser(
        description="Run the complete C# ETL pipeline: Extract → Parse → Enrich → Load → Archive"
    )
    parser.add_argument(
        "input", nargs="?", default=None,
        help="Path to input .zip file or directory containing C# files (default: input_code/)"
    )
    parser.add_argument(
        "--output-base", dest="output_base",
        help="Base directory for output files (default: project root)"
    )
    parser.add_argument(
        "--skip-extract", action="store_true",
        help="Skip the extract phase (use existing raw/ files)"
    )
    parser.add_argument(
        "--skip-parse", action="store_true", 
        help="Skip the parse phase (use existing AST files)"
    )
    parser.add_argument(
        "--skip-enrich", action="store_true",
        help="Skip the enrich phase (use existing enriched files)" 
    )
    parser.add_argument(
        "--skip-load", action="store_true",
        help="Skip the load phase (don't insert into Neo4j)"
    )
    parser.add_argument(
        "--skip-archive", action="store_true",
        help="Skip the archive phase (keep files in raw/ directory)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Skip all phases except extract (useful for testing)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Determine which phases to skip
    skip_phases = []
    if args.skip_extract:
        skip_phases.append('extract')
    if args.skip_parse:
        skip_phases.append('parse')
    if args.skip_enrich:
        skip_phases.append('enrich')
    if args.skip_load:
        skip_phases.append('load')
    if args.skip_archive:
        skip_phases.append('archive')
        
    # Dry run mode skips everything except extract
    if args.dry_run:
        skip_phases = ['parse', 'enrich', 'load', 'archive']
        logger.info("Dry run mode - only extract phase will run")
        
    try:
        # Run the ETL pipeline
        result = run_etl_pipeline(
            input_path=args.input,
            output_base=args.output_base,
            skip_phases=skip_phases
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("ETL PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Run ID: {result['run_id']}")
        print(f"Status: {result['status']}")
        print(f"Phases completed: {result['phases_completed']}")
        print(f"Files processed: {result.get('files_processed', 0)}")
        print(f"Total nodes: {result.get('total_nodes_parsed', 0)}")
        print(f"Files archived: {result.get('files_archived', 0)}")
        
        if result['errors']:
            print(f"Errors encountered: {len(result['errors'])}")
            for error in result['errors']:
                print(f"  - {error}")
                
        print("=" * 60)
        
        # Exit with error code if pipeline failed
        if result['status'] == 'FAILED':
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"ETL Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
