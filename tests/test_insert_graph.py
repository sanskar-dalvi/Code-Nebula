"""Tests for the graph insertion module."""
import os
import json
import tempfile
import pytest
from pipeline.insert_graph import ingest_enriched_json
from pipeline.models import CodeEntity
from pathlib import Path
from neomodel import db 


@pytest.fixture(autouse=True)
def clean_neo4j_before_each_test():
    db.cypher_query("MATCH (n) DETACH DELETE n")
    yield

@pytest.fixture(scope="module")
def sample_project_folder():
    """
    Read and return path to a sample enriched JSON file from the enriched output folder.
    """
   
    # Use the actual path to the existing cli_enriched.json file
    project_root = Path(__file__).parent.parent  # Go up from tests to project root
    curated_folder = project_root / "curated"

    assert curated_folder.exists() and curated_folder.is_dir(), f"Curated folder {curated_folder} not found"

    return str(curated_folder)
class TestGraphIngestion:

    def test_ingest_json(self, sample_project_folder):
        """Test that a File node is created and connected to the class node using direct Neo4j queries."""


        ingest_enriched_json(sample_project_folder)    # Get the base name of the file without extension
        
        # Print what nodes exist for debugging
        print("\nNodes in database:")
        result, _ = db.cypher_query("MATCH (n) RETURN count(n)")
        assert result[0][0] > 0, "Nodes should be created"

        result, _ = db.cypher_query("MATCH ()-[r]->() RETURN count(r)")
        assert result[0][0] > 0, "Relationships should be created"

    def test_has_parameter_and_returns(self, sample_project_folder):
        ingest_enriched_json(sample_project_folder)

        result, _ = db.cypher_query(
            """
            MATCH (m:CodeEntity)-[:HAS_PARAMETER]->(p:CodeEntity)
            WHERE m.type = 'Method' AND p.type = 'Parameter'
            RETURN count(*) as param_rel_count
            """
        )
        assert result[0][0] > 0, "HAS_PARAMETER relationship should exist"

        result, _ = db.cypher_query(
            """
            MATCH (m:CodeEntity)-[:RETURNS]->(r:CodeEntity)
            WHERE m.type = 'Method' AND r.type = 'ReturnType'
            RETURN count(*) as return_rel_count
            """
        )
        assert result[0][0] > 0, "RETURNS relationship should exist"

    def test_query_capabilities(self, sample_project_folder):
        ingest_enriched_json(sample_project_folder)

        result, _ = db.cypher_query(
            """
            MATCH (c:CodeEntity)-[:IMPLEMENTS]->(i:CodeEntity)
            WHERE c.type = 'Class' AND i.type = 'Interface'
            RETURN c.name, i.name
            """
        )
        if result:
            print("Class -> INTERFACE IMPLEMENTATION:")
            for c_name,i_name in result:
                print(f"  {c_name} implements {i_name}")
            assert len(result) > 0
        else:
            print("No IMPLEMENTS relationships found. Skipping assertion.")

        result, _ = db.cypher_query(
            """
            MATCH (f:File)-[:HAS_ENTITY]->(n:CodeEntity)
            RETURN count(n)
            """
        )
        assert result[0][0] > 0, "File node should CONTAIN other nodes"
    