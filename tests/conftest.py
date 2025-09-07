"""Pytest configuration file."""
import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Creating a proper conftest.py file that adds the project root to Python's path