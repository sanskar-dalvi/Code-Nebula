"""
Archive Module for ETL Pipeline

This module handles archiving of processed raw files after ETL completion.
It moves files from raw/ directory to archive/ with timestamp-based directories
to maintain a history of processed data.

This module implements task D3 from the batch ETL requirements.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# Default directory for archiving processed files
DEFAULT_ARCHIVE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'archive')
)


def archive_processed_files(raw_dir: str = None,
                           archive_dir: str = None,
                           run_id: Optional[str] = None) -> Tuple[int, List[str]]:
    """
    Archive processed raw files by moving them to a timestamped directory in archive/.
    
    Args:
        raw_dir: Path to raw directory containing processed files (default: project's raw/ folder)
        archive_dir: Path to archive directory (default: project's archive/ folder)
        run_id: Optional ETL run ID to use for the archive folder name
               (defaults to current timestamp if not provided)
    
    Returns:
        Tuple containing (number of files archived, list of archived paths)
    """
    # Determine directories to use
    if raw_dir is None:
        raw_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'raw')
        )
        
    if archive_dir is None:
        archive_dir = DEFAULT_ARCHIVE_DIR
        
    # Create archive directory if it doesn't exist
    Path(archive_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped archive directory name if run_id not provided
    if not run_id:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    archive_subdir = os.path.join(archive_dir, f"run_{run_id}")
    
    try:
        # Create the archive subdirectory
        Path(archive_subdir).mkdir(parents=True, exist_ok=True)
        
        # Check if raw directory exists
        if not os.path.exists(raw_dir):
            logger.warning(f"Raw directory not found: {raw_dir}")
            return 0, []
        
        # Get list of files and directories in raw/
        raw_items = os.listdir(raw_dir)
        
        if not raw_items:
            logger.info(f"No files to archive in {raw_dir}")
            return 0, []
            
        # Archive each item (file or directory)
        archived_items = []
        
        for item in raw_items:
            src_path = os.path.join(raw_dir, item)
            dst_path = os.path.join(archive_subdir, item)
            
            try:
                # If it's a directory, copy the whole tree
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                    # After successful copy, remove the source directory
                    shutil.rmtree(src_path)
                # If it's a file, copy it
                else:
                    shutil.copy2(src_path, dst_path)
                    # After successful copy, remove the source file
                    os.remove(src_path)
                    
                archived_items.append(item)
                logger.info(f"Archived: {item} → {archive_subdir}")
                
            except Exception as e:
                logger.error(f"Failed to archive {item}: {e}")
                continue
                
        logger.info(f"Archived {len(archived_items)} items to {archive_subdir}")
        return len(archived_items), archived_items
        
    except Exception as e:
        logger.error(f"Archive operation failed: {e}")
        return 0, []


def get_archived_runs() -> Dict[str, List[str]]:
    """
    Get a list of all archived runs and their contents.
    
    Returns:
        Dict mapping run IDs to lists of archived items
    """
    archive_dir = DEFAULT_ARCHIVE_DIR
    
    # Create archive directory if it doesn't exist
    Path(archive_dir).mkdir(parents=True, exist_ok=True)
    
    archived_runs = {}
    
    try:
        # Check all subdirectories in archive/
        for run_dir in Path(archive_dir).iterdir():
            if run_dir.is_dir() and run_dir.name.startswith("run_"):
                run_id = run_dir.name.replace("run_", "")
                archived_items = [item.name for item in run_dir.iterdir()]
                archived_runs[run_id] = archived_items
                
        return archived_runs
        
    except Exception as e:
        logger.error(f"Failed to get archived runs: {e}")
        return {}


# Add CLI support when run directly
if __name__ == "__main__":
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    parser = argparse.ArgumentParser(
        description="Archive processed raw files to archive/ directory"
    )
    parser.add_argument(
        "-r", "--raw", dest="raw_dir",
        help="Path to raw directory (defaults to project's raw/ folder)",
        default=None
    )
    parser.add_argument(
        "-a", "--archive", dest="archive_dir",
        help="Path to archive directory (defaults to project's archive/ folder)",
        default=None
    )
    parser.add_argument(
        "-l", "--list", dest="list_archives", action="store_true",
        help="List all archived runs instead of creating a new archive"
    )
    
    args = parser.parse_args()
    
    if args.list_archives:
        archived_runs = get_archived_runs()
        
        if not archived_runs:
            print("No archived runs found.")
        else:
            print(f"Found {len(archived_runs)} archived runs:")
            for run_id, items in archived_runs.items():
                print(f"  Run {run_id}: {len(items)} items")
    else:
        count, archived = archive_processed_files(
            raw_dir=args.raw_dir,
            archive_dir=args.archive_dir
        )
        
        if count > 0:
            print(f"Successfully archived {count} items.")
        else:
            print("No items were archived.")
