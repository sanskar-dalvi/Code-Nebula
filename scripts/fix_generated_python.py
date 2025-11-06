#!/usr/bin/env python3
"""
Post-processing script to fix generated Python code from ANTLR.
Replaces Java-style 'this' with Python 'self'.
"""

import sys
import re
from pathlib import Path


def fix_this_to_self(file_path):
    """Replace 'this.' with 'self.' in the generated Python files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 'this.' with 'self.' in action methods
        # This pattern matches 'this.' followed by a method or property name
        content = re.sub(r'\bthis\.', 'self.', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] Fixed: {file_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Error fixing {file_path}: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_generated_python.py <directory>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    
    if not directory.exists():
        print(f"[ERROR] Directory not found: {directory}")
        sys.exit(1)
    
    print(f"Fixing generated Python files in {directory}...")
    
    # Fix all Python files in the directory
    fixed_count = 0
    for py_file in directory.glob("*.py"):
        if fix_this_to_self(py_file):
            fixed_count += 1
    
    print(f"[OK] Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
