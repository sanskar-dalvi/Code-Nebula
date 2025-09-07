"""
Centralized Logging Configuration Module

This module provides centralized logging configuration and utilities
for the C# parser ETL pipeline. It sets up loggers for:
1. ETL pipeline operations (logs/etl/)
2. Raw LLM outputs (logs/llm_raw/)

This module implements task D4 from the batch ETL requirements.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Union

# Constants for log directories
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
ETL_LOG_DIR = PROJECT_ROOT / 'logs' / 'etl'
LLM_LOG_DIR = PROJECT_ROOT / 'logs' / 'llm_raw'

# Create log directories if they don't exist
ETL_LOG_DIR.mkdir(parents=True, exist_ok=True)
LLM_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
PIPELINE_LOG_FILE = PROJECT_ROOT / 'pipeline_run.log'
ETL_SUMMARY_PATTERN = "etl_run_{}.json"  # Formatted with timestamp
LLM_OUTPUT_PATTERN = "llm_response_{}.json"  # Formatted with timestamp + identifier


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger with the specified name and level.
    
    Args:
        name: Name for the logger (typically __name__ of the calling module)
        level: Logging level (default: logging.INFO)
    
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
        )
        logger.addHandler(console_handler)
        
        # File handler for overall pipeline log
        file_handler = logging.FileHandler(PIPELINE_LOG_FILE)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
        )
        logger.addHandler(file_handler)
    
    return logger


def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the entire application.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PIPELINE_LOG_FILE)
        ]
    )


def log_etl_summary(run_id: str, data: Dict[str, Any]) -> str:
    """
    Log ETL run summary data to a JSON file in the ETL log directory.
    
    Args:
        run_id: Unique identifier for the ETL run (typically timestamp)
        data: Dict containing ETL run statistics and metadata
    
    Returns:
        Path to the created log file
    """
    log_file = ETL_LOG_DIR / ETL_SUMMARY_PATTERN.format(run_id)
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger = get_logger(__name__)
        logger.info(f"ETL run summary saved to: {log_file}")
        return str(log_file)
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to save ETL summary: {e}")
        return ""


def log_llm_raw_output(
    request_data: Dict[str, Any], 
    response_data: Dict[str, Any], 
    identifier: Optional[str] = None,
    run_id: Optional[str] = None
) -> str:
    """
    Log raw LLM request and response data to a JSON file.
    
    Args:
        request_data: The request sent to the LLM API
        response_data: The raw response received from the LLM API
        identifier: Optional identifier for the specific LLM call (e.g., class/method name)
        run_id: Optional ETL run ID to associate with the LLM call
              (defaults to current timestamp if not provided)
    
    Returns:
        Path to the created log file
    """
    # Generate run_id if not provided
    if not run_id:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create identifier string
    id_str = f"_{identifier}" if identifier else ""
    log_file = LLM_LOG_DIR / LLM_OUTPUT_PATTERN.format(f"{run_id}{id_str}")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,
        "identifier": identifier,
        "request": request_data,
        "response": response_data
    }
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        logger = get_logger(__name__)
        logger.debug(f"LLM raw output saved to: {log_file}")
        return str(log_file)
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to save LLM raw output: {e}")
        return ""


def get_etl_logs(limit: int = 10) -> Dict[str, Dict]:
    """
    Get the most recent ETL run logs.
    
    Args:
        limit: Maximum number of logs to return (default: 10)
    
    Returns:
        Dict mapping run_ids to their ETL summary data
    """
    logs = {}
    
    try:
        etl_files = list(ETL_LOG_DIR.glob("etl_run_*.json"))
        # Sort by modification time (newest first)
        etl_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Take only the requested number of logs
        for log_file in etl_files[:limit]:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                run_id = data.get('run_id', log_file.stem.replace('etl_run_', ''))
                logs[run_id] = data
                
        return logs
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to get ETL logs: {e}")
        return {}


def get_llm_logs(run_id: Optional[str] = None, limit: int = 10) -> Dict[str, Dict]:
    """
    Get LLM raw output logs, optionally filtered by run_id.
    
    Args:
        run_id: Optional ETL run ID to filter logs
        limit: Maximum number of logs to return (default: 10)
    
    Returns:
        Dict mapping log filenames to their LLM log data
    """
    logs = {}
    
    try:
        if run_id:
            # Filter logs for the specific run
            llm_files = list(LLM_LOG_DIR.glob(f"llm_response_{run_id}*.json"))
        else:
            # Get all logs
            llm_files = list(LLM_LOG_DIR.glob("llm_response_*.json"))
            
        # Sort by modification time (newest first)
        llm_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Take only the requested number of logs
        for log_file in llm_files[:limit]:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logs[log_file.name] = data
                
        return logs
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to get LLM logs: {e}")
        return {}


# Initialize logger for this module
logger = get_logger(__name__)

# Run when imported to ensure log directories exist
if __name__ != "__main__":
    logger.debug(f"Logger module initialized. ETL logs: {ETL_LOG_DIR}, LLM logs: {LLM_LOG_DIR}")


# CLI functionality when run directly
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ETL and LLM Logging Utility")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command to list ETL logs
    etl_parser = subparsers.add_parser("etl", help="List ETL run logs")
    etl_parser.add_argument("-l", "--limit", type=int, default=5, help="Max number of logs to show")
    
    # Command to list LLM logs
    llm_parser = subparsers.add_parser("llm", help="List LLM raw output logs")
    llm_parser.add_argument("-r", "--run-id", help="Filter by ETL run ID")
    llm_parser.add_argument("-l", "--limit", type=int, default=5, help="Max number of logs to show")
    
    args = parser.parse_args()
    
    if args.command == "etl":
        print(f"=== Recent ETL Runs (limit={args.limit}) ===")
        logs = get_etl_logs(args.limit)
        for run_id, data in logs.items():
            status = data.get('status', 'UNKNOWN')
            phases = ', '.join(data.get('phases_completed', []))
            files = data.get('files_processed', 0)
            print(f"Run {run_id}: Status={status}, Phases={phases}, Files={files}")
            
    elif args.command == "llm":
        run_filter = f"for run {args.run_id}" if args.run_id else ""
        print(f"=== LLM Raw Outputs {run_filter} (limit={args.limit}) ===")
        logs = get_llm_logs(args.run_id, args.limit)
        for filename, data in logs.items():
            timestamp = data.get('timestamp', 'Unknown')
            identifier = data.get('identifier', 'None')
            print(f"{filename}: Timestamp={timestamp}, Identifier={identifier}")
    
    else:
        parser.print_help()
