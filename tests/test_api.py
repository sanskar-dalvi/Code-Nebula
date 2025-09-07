"""Tests for the API.

This module contains tests for the FastAPI endpoints, focusing on the /api/process
endpoint that processes C# files through the complete pipeline.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from api.routers.process_code import CodeInput

# Create a test client for the FastAPI app
client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns the expected health check information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the structure and basic content of the response
    assert data["status"] == "healthy"
    assert data["app"] == "C#→Neo4j AI Pipeline"
    assert any(endpoint["path"] == "/api/process" for endpoint in data["endpoints"])


@patch("api.routers.process_code.parse_cs_file")
@patch("api.routers.process_code.serialize_to_json")
@patch("api.routers.process_code.enrich_ast")
@patch("api.routers.process_code.ingest_enriched_json")
def test_process_endpoint_success(mock_ingest, mock_enrich, mock_serialize, mock_parse, tmp_path):
    """Test the /api/process endpoint with valid input."""
    # Create a temporary C# file for testing
    sample_cs_file = tmp_path / "Sample.cs"
    sample_cs_file.write_text(
        "namespace ExampleApp { public class Sample { public void DoIt() {} } }"
    )
    
    # Setup mock return values
    mock_parse.return_value = [
        {"type": "Class", "name": "Sample", "startLine": 1},
        {"type": "Method", "name": "DoIt", "startLine": 2}
    ]
    
    # Make request to the endpoint
    response = client.post(
        "/api/process", 
        json={"file_path": str(sample_cs_file)}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Graph updated in Neo4j" in data["message"]
    
    # Verify each step of the pipeline was called exactly once
    mock_parse.assert_called_once_with(str(sample_cs_file))
    mock_serialize.assert_called_once()
    mock_enrich.assert_called_once()
    mock_ingest.assert_called_once()


def test_process_endpoint_file_not_found():
    """Test the /api/process endpoint with a file that doesn't exist."""
    response = client.post(
        "/api/process", 
        json={"file_path": "/path/to/nonexistent/file.cs"}
    )
    
    # Should return a 404 error
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


@patch("api.routers.process_code.parse_cs_file")
def test_process_endpoint_pipeline_error(mock_parse, tmp_path):
    """Test handling of errors during pipeline processing."""
    # Create a temporary C# file for testing
    sample_cs_file = tmp_path / "ErrorSample.cs"
    sample_cs_file.write_text("class ErrorTrigger {}")
    
    # Make the parse step raise an exception
    mock_parse.side_effect = Exception("Parser error simulation")
    
    # Make request to the endpoint
    response = client.post(
        "/api/process", 
        json={"file_path": str(sample_cs_file)}
    )
    
    # Should return a 500 error
    assert response.status_code == 500
    assert "Parser error simulation" in response.json()["detail"]


@patch("api.routers.process_code.os.path.isfile")
@patch("api.routers.process_code.parse_cs_file")
@patch("api.routers.process_code.serialize_to_json")
@patch("api.routers.process_code.enrich_ast")
@patch("api.routers.process_code.ingest_enriched_json")
def test_process_endpoint_non_cs_file(mock_ingest, mock_enrich, mock_serialize, 
                                      mock_parse, mock_isfile):
    """Test processing a file that isn't a .cs file (should still work with warning)."""
    # Mock os.path.isfile to return True
    mock_isfile.return_value = True
    
    # Setup mock for parser
    mock_parse.return_value = [{"type": "Class", "name": "TestClass", "startLine": 1}]
    
    # Make request with a non-CS file
    response = client.post(
        "/api/process", 
        json={"file_path": "/path/to/file.txt"}
    )
    
    # Should still succeed despite warning
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@patch("api.routers.process_code.parse_cs_file")
@patch("api.routers.process_code.serialize_to_json")
@patch("api.routers.process_code.enrich_ast")
def test_process_endpoint_neo4j_error(mock_enrich, mock_serialize, mock_parse, tmp_path):
    """Test handling of Neo4j ingestion errors."""
    # Create a temporary C# file for testing
    sample_cs_file = tmp_path / "Sample.cs"
    sample_cs_file.write_text("namespace Test { class Sample {} }")
    
    # Setup mocks for the first two steps
    mock_parse.return_value = [{"type": "Class", "name": "Sample", "startLine": 1}]
    
    # Make enrich raise an error simulating Neo4j connection issues
    mock_enrich.side_effect = Exception("Neo4j connection failed")
    
    # Make request to the endpoint
    def test_request_validation():
        """Test validation of the request body."""
        # Test with missing required field
        response = client.post("/api/process", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with wrong data type
        response = client.post("/api/process", json={"file_path": 123})
        assert response.status_code == 422  # Validation error
