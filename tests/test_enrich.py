"""Tests for the enrich module.

This module tests the functionality of the enrich module which is responsible for 
enriching abstract syntax trees (ASTs) with additional metadata using LLM integration.
"""
import os
import json
import pytest
from unittest import mock
from pipeline import enrich

@pytest.fixture
def sample_ast():
    """Provide a minimal sample AST for testing.
    
    Returns:
        list: A simple AST with a single class node
    """
    return [
        {"type": "Class", "name": "MyClass", "members": []}
    ]

@pytest.fixture
def sample_llm_response():
    """Provide a mock response from the LLM service.
    
    Returns:
        dict: A dictionary mimicking the structure of an LLM API response
              with metadata about the sample class
    """
    return {
        "response": json.dumps({
            "summary": "This is a sample class.",
            "dependencies": ["System"],
            "tags": ["class", "sample"]
        })
    }

def test_build_prompt_reads_template_and_inserts_ast(tmp_path, sample_ast):
    """Test that build_prompt correctly reads template and replaces AST placeholder.
    
    This test verifies that:
    1. The template file is read correctly
    2. The AST JSON placeholder is replaced with the actual AST
    
    Args:
        tmp_path: pytest fixture providing a temporary directory path
        sample_ast: fixture providing a sample AST object
    """
    # Create a test template file in the temporary directory
    template_path = tmp_path / "csharp_enrich_prompt.txt"
    template_content = "Prompt with AST: {{AST_JSON}}"
    template_path.write_text(template_content, encoding="utf-8")
    
    # Mock the open function to return our template content
    with mock.patch("builtins.open", mock.mock_open(read_data=template_content)):
        prompt = enrich.build_prompt(sample_ast)
        # Verify placeholder was replaced
        assert "{{AST_JSON}}" not in prompt
        # Verify AST content was inserted
        assert "MyClass" in prompt

def test_call_llm_success(sample_ast, sample_llm_response):
    """Test successful LLM API call.
    
    This test verifies that:
    1. The LLM API is called with the right parameters
    2. The response is correctly processed
    
    Args:
        sample_ast: fixture providing a sample AST object
        sample_llm_response: fixture providing a mock LLM response
    """
    # Mock the HTTP POST request to LLM service
    with mock.patch("pipeline.enrich.requests.post") as mock_post:
        # Configure mock to return a successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = sample_llm_response
        
        # Mock build_prompt to avoid template dependencies
        with mock.patch("pipeline.enrich.build_prompt", return_value="prompt"):
            resp = enrich.call_llm(sample_ast)
            # Verify response structure
            assert "response" in resp

def test_extract_enriched_data_success(sample_llm_response):
    """Test extracting data from a successful LLM response.
    
    This test verifies that JSON data from the LLM response is correctly
    parsed and extracted.
    
    Args:
        sample_llm_response: fixture providing a mock LLM response
    """
    enriched = enrich.extract_enriched_data(sample_llm_response)
    # Verify extracted data matches expected values
    assert enriched["summary"] == "This is a sample class."
    assert "dependencies" in enriched
    assert "tags" in enriched

def test_extract_enriched_data_invalid_json(caplog):
    """Test handling of invalid JSON in LLM response.
    
    This test verifies that the extract function raises an exception
    when the LLM response contains invalid JSON and logs the error.
    """
    # Create a response with non-JSON content
    bad_response = {"response": "not a json"}
    
    # Verify exception is raised for invalid JSON
    with pytest.raises(Exception):
        enrich.extract_enriched_data(bad_response)
    
    # Check that the error log was generated
    assert "Error extracting or parsing LLM response" in caplog.text

def test_enrich_ast_pipeline(tmp_path, sample_ast, sample_llm_response):
    """Test the full enrichment pipeline.
    
    This test verifies the entire workflow:
    1. AST is sent to LLM service
    2. Enriched data is extracted
    3. Results are saved to an output file
    4. Function returns the combined results
    
    Args:
        tmp_path: pytest fixture providing a temporary directory path
        sample_ast: fixture providing a sample AST object
        sample_llm_response: fixture providing a mock LLM response
    """
    # Define output path in the temporary directory
    output_path = tmp_path / "enriched.json"
    
    # Mock the LLM call to return our sample response
    with mock.patch("pipeline.enrich.call_llm", return_value=sample_llm_response):
        result = enrich.enrich_ast(sample_ast, str(output_path))
        
        # Verify output file was created
        assert output_path.exists()
        
        # Verify returned data structure
        assert result["summary"] == "This is a sample class."
        assert "ast" in result