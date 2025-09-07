"""
AST Enrichment Module.

This module provides functionality to enrich C# Abstract Syntax Trees (ASTs)
with additional metadata using Large Language Models (LLMs).
The enrichment process adds summaries, dependencies, and tags to the AST nodes.
"""
import os
import json
import requests
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

# Import centralized logging module
from logs.logger import get_logger, log_llm_raw_output

# Get logger for this module
logger = get_logger(__name__)

# Load environment variables from the .env file
# These contain API endpoints and model configurations
# Force reload the environment to ensure we get fresh values
import os
for key in ['LLM_MODEL', 'OLLAMA_BASE_URL', 'LLM_PROVIDER']:
    if key in os.environ:
        del os.environ[key]

load_dotenv(override=True)  # Override any existing environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # Base URL for the Ollama API
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-coder:1.3b")  # Use deepseek-coder as default

# Clean up the LLM_MODEL in case it has comments
if LLM_MODEL and '#' in LLM_MODEL:
    LLM_MODEL = LLM_MODEL.split('#')[0].strip()

# Debug logging for environment variables
logger.info(f"Environment - OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
logger.info(f"Environment - LLM_MODEL: {repr(LLM_MODEL)}")
logger.info(f"Environment - Full URL will be: {OLLAMA_BASE_URL}/api/generate")


def build_prompt(ast_nodes: list[dict]) -> str:
    """
    Reads prompt template and fills in AST JSON.
    
    This function:
    1. Reads the prompt template from a file
    2. Replaces the placeholder with the stringified AST
    3. Returns the complete prompt ready for LLM consumption
    
    Args:
        ast_nodes (list[dict]): List of AST node dictionaries to be included in the prompt
        
    Returns:
        str: Completed prompt with AST JSON inserted
        
    Raises:
        Exception: If the template file cannot be read or processed
    """
    try:
        # Open the template file containing the prompt structure
        with open("prompt_templates/csharp_enrich_prompt.txt", "r", encoding="utf-8") as f:
            template = f.read()
        # Replace the placeholder with the actual AST JSON data
        return template.replace("{{AST_JSON}}", json.dumps(ast_nodes, indent=2))
    except Exception as e:
        logger.error(f"Error reading prompt template: {e}")
        raise


def call_llm(ast_nodes: list[dict]) -> dict:
    """
    Calls the LLM with our prompt and returns raw JSON response.
    Uses Ollama local API.
    
    This function:
    1. Builds a prompt using the AST nodes
    2. Configures the API request with appropriate parameters
    3. Sends the request to the Ollama API
    4. Returns the raw JSON response
    
    Args:
        ast_nodes (list[dict): List of AST node dictionaries to analyze
        
    Returns:
        dict: Raw JSON response from the LLM API
        
    Raises:
        requests.RequestException: If the API call fails
    """
    # Generate the prompt using the AST nodes
    prompt = build_prompt(ast_nodes)
    logger.debug(f"Prompt length: {len(prompt)} characters")
    
    # Configure the payload for the Ollama API request
    payload = {
        "model": LLM_MODEL,                 # Model to use for generation
        "prompt": prompt,                   # The prompt containing instructions and AST
        "stream": False,                    # Get complete response at once, not streaming
        "options": {
            "temperature": 0.0,             # Use deterministic output (0 = most deterministic)
            "top_p": 0.9,                   # Use full probability distribution
            "num_predict": 2048,            # Ollama parameter for max tokens to generate
            "stop": ["```", "---"]          # Stop sequences to prevent over-generation
        }
    }
    
    # Log which model we're using
    logger.info(f"Using LLM model: {LLM_MODEL}")
    
    try:
        # Log that we're sending a request
        logger.info(f"Sending request to Ollama API at {OLLAMA_BASE_URL}/api/generate")
        
        # Generate a unique identifier for this LLM call
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Send POST request to the Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",      # Endpoint for text generation
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60                              # 60 second timeout
        )
        
        # Log the response status
        logger.info(f"Received response from Ollama API: HTTP {response.status_code}")
        
        # Raise exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()
        
        # Try to parse the JSON response
        try:
            result = response.json()
            # Log the keys in the response to help with debugging
            if result:
                logger.info(f"Response keys: {list(result.keys())}")
            
            # Save raw LLM request and response to log file
            log_file = log_llm_raw_output(
                request_data=payload,
                response_data=result,
                identifier="ast_enrichment",
                run_id=request_id
            )
            logger.info(f"LLM raw output saved to: {log_file}")
            
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.error(f"Raw response text: {response.text[:200]}...")  # Log the first 200 chars
            # Log error response
            error_response = {
                "response": "",
                "error": f"Invalid JSON in response: {str(e)}",
                "raw_text": response.text[:500] if response.text else ""  # Include some raw text for debugging
            }
            
            # Save error details
            log_llm_raw_output(
                request_data=payload,
                response_data={"error": str(e), "partial_text": response.text[:500] if response.text else ""},
                identifier="ast_enrichment_error",
                run_id=request_id
            )
            
            return error_response
            
    except requests.RequestException as e:
        logger.error(f"Error calling Ollama LLM: {e}")
        # Return a structured error response instead of raising
        return {
            "response": "",
            "error": f"Request failed: {str(e)}",
            "exception_type": type(e).__name__
        }


def clean_json_response(text: str) -> str:
    """
    Clean and extract JSON from LLM response text.
    
    Args:
        text (str): Raw text response from LLM
        
    Returns:
        str: Cleaned JSON string
    """
    import re
    
    # Remove common prefixes and suffixes
    text = re.sub(r'^.*?(?=\{)', '', text, flags=re.DOTALL)  # Remove everything before first {
    
    # Only remove content after last } if there actually is a }
    if '}' in text:
        text = re.sub(r'\}.*?$', '}', text, flags=re.DOTALL)     # Remove everything after last }
    
    # Remove comments from JSON
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)   # Remove // comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)   # Remove /* */ comments
    
    # Fix common JSON formatting issues
    text = re.sub(r',\s*([}\]])', r'\1', text)               # Remove trailing commas
    
    # Check if JSON appears to be truncated (no closing brace)
    if text.strip() and not text.strip().endswith('}'):
        # Count opening and closing braces/brackets
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        logger.info(f"Truncated JSON detected - Open braces: {open_braces}, Close braces: {close_braces}")
        logger.info(f"Open brackets: {open_brackets}, Close brackets: {close_brackets}")
        
        # Add missing closing brackets first
        missing_brackets = open_brackets - close_brackets
        if missing_brackets > 0:
            logger.info(f"Adding {missing_brackets} missing closing brackets")
            text += ']' * missing_brackets
            
        # Add missing closing braces
        missing_braces = open_braces - close_braces
        if missing_braces > 0:
            logger.info(f"Adding {missing_braces} missing closing braces")
            text += '}' * missing_braces
    
    # More aggressive comma fixing for the specific pattern we see
    # The main issue: "property": "value" "nextProperty" should be "property": "value", "nextProperty"
    
    # Step 1: Handle quoted strings followed by other quoted strings (property names)
    # Pattern: "value" "property" -> "value", "property"
    text = re.sub(r'("\s*)\s+"([a-zA-Z_])', r'\1, "\2', text)
    
    # Step 2: Handle arrays followed by property names
    # Pattern: ["item"] "property" -> ["item"], "property"
    text = re.sub(r'(\])\s+"([a-zA-Z_])', r'\1, "\2', text)
    
    # Step 3: Handle objects followed by property names
    # Pattern: {...} "property" -> {...}, "property"  
    text = re.sub(r'(\})\s+"([a-zA-Z_])', r'\1, "\2', text)
    
    # Step 4: Handle newlines between properties
    # Pattern: "value"\n  "property" -> "value",\n  "property"
    text = re.sub(r'("\s*)\n(\s*"[a-zA-Z_])', r'\1,\n\2', text)
    
    # Step 5: Handle arrays on newlines
    # Pattern: ]\n  "property" -> ],\n  "property"
    text = re.sub(r'(\])\s*\n(\s*"[a-zA-Z_])', r'\1,\n\2', text)
    
    # Step 6: Handle objects on newlines  
    # Pattern: }\n  "property" -> },\n  "property"
    text = re.sub(r'(\})\s*\n(\s*"[a-zA-Z_])', r'\1,\n\2', text)
    
    # Step 7: Clean up any issues we may have introduced
    # Remove double commas
    text = re.sub(r',,+', ',', text)
    
    # Remove commas right after opening braces (fixes the {, issue)
    text = re.sub(r'{\s*,', '{', text)
    
    # Remove trailing commas before closing brackets/braces
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    return text.strip()


# JSON validation helper

def validate_json(text: str) -> dict | None:
    """
    Validate and parse JSON text strictly.
    Returns parsed dict if valid, otherwise None.
    """
    try:
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError as e:
        logger.debug(f"JSON validation failed: {e}")
        logger.debug(f"Failed text: {text[:100]}...")
        return None


def extract_enriched_data(raw_resp: dict) -> dict:
    """
    Extract and parse JSON from LLM response with aggressive cleaning.
    
    This function handles LLM responses that often contain explanatory text
    alongside the requested JSON by using multiple extraction strategies.
    
    Args:
        raw_resp (dict): Raw JSON response from the LLM API
        
    Returns:
        dict: Parsed enrichment data containing summary, dependencies, and tags
    """
    try:
        # Ollama returns the response in the "response" field
        # Get raw response text from Ollama's response format
        text = ""
        if "response" in raw_resp:
            text = raw_resp["response"].strip()
        elif "choices" in raw_resp and raw_resp["choices"]:
            # Handle OpenAI-style response format
            text = raw_resp["choices"][0].get("text", "").strip()
        else:
            # Fallback: try to find text in the response
            logger.warning(f"Unexpected response format: {list(raw_resp.keys())}")
            text = str(raw_resp).strip()
        
        # Log the extracted text for debugging
        logger.info(f"Extracted text from LLM (length: {len(text)}): {repr(text)}")
        
        if not text:
            logger.warning("Empty response from LLM")
            return {"summary": "No response generated", "dependencies": [], "tags": ["no-response"]}
        
        # Handle common LLM refusal patterns
        refusal_patterns = [
            "i'm sorry",
            "i cannot",
            "you didn't provide",
            "no method",
            "no code",
            "therefore i can only"
        ]
        
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in refusal_patterns):
            logger.warning(f"LLM refused to analyze: {text[:100]}...")
            # Try to extract any JSON that might still be in the response
            json_match = re.search(r'\{[^{}]*\}', text)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    if isinstance(parsed, dict):
                        parsed.setdefault("summary", "Generic implementation")
                        parsed.setdefault("dependencies", [])
                        parsed.setdefault("tags", ["generic"])
                        return parsed
                except json.JSONDecodeError:
                    pass
            return {"summary": "Generic implementation", "dependencies": [], "tags": ["generic"]}
        
        # First, try to parse as direct JSON
        try:
            direct_json = json.loads(text)
            if isinstance(direct_json, dict) and ('summary' in direct_json or 'tags' in direct_json):
                # Ensure required fields exist
                direct_json.setdefault("summary", "")
                direct_json.setdefault("dependencies", [])
                direct_json.setdefault("tags", [])
                logger.info(f"Successfully parsed direct JSON: {direct_json}")
                return direct_json
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            logger.info(f"Direct JSON parsing failed: {e}")
            logger.info(f"Failed text: {text[:500]}...")
        
        # If direct parsing fails, clean the response and try again
        logger.info(f"Direct parsing failed, attempting to clean JSON response...")
        logger.info(f"Original text to clean: {repr(text)}")
        cleaned = clean_json_response(text)
        logger.info(f"Cleaned JSON result: {repr(cleaned)}")
        
        # Try strict JSON validation on cleaned text
        parsed = validate_json(cleaned)
        if parsed is not None:
            # Ensure required fields exist
            parsed.setdefault("summary", "")
            parsed.setdefault("dependencies", [])
            parsed.setdefault("tags", [])
            logger.info(f"Successfully parsed cleaned JSON: {parsed}")
            return parsed
        else:
            logger.warning(f"Cleaned JSON also failed to parse")
            logger.warning(f"Full cleaned text: {repr(cleaned)}")
        
        # Aggressive fix for the specific comma issue we're seeing
        # The LLM consistently generates: "tags": ["tag1", "tag2"] "dependencies": ["dep1"]
        # We need to add commas between JSON properties
        comma_fixed_text = text
        
        # Fix missing commas after quoted values before new properties
        import re
        
        # Step 1: Add commas after quoted strings before new properties
        comma_fixed_text = re.sub(r'"\s+"([a-zA-Z_])', r'", "\1', comma_fixed_text)
        
        # Step 2: Add commas after arrays before new properties  
        comma_fixed_text = re.sub(r'(\])\s+"([a-zA-Z_])', r'\1, "\2', comma_fixed_text)
        
        # Step 3: Add commas after closing braces before new properties
        comma_fixed_text = re.sub(r'(\})\s+"([a-zA-Z_])', r'\1, "\2', comma_fixed_text)
        
        # Step 4: Handle newlines between properties
        comma_fixed_text = re.sub(r'"\s*\n\s*"([a-zA-Z_])', r'",\n"\1', comma_fixed_text)
        comma_fixed_text = re.sub(r'(\])\s*\n\s*"([a-zA-Z_])', r'\1,\n"\2', comma_fixed_text)
        comma_fixed_text = re.sub(r'(\})\s*\n\s*"([a-zA-Z_])', r'\1,\n"\2', comma_fixed_text)
        
        # Step 5: Fix array elements without commas
        comma_fixed_text = re.sub(r'("\w+[^,]*")\s+(")', r'\1, \2', comma_fixed_text)
        
        # Step 6: Clean up any double commas that might have been introduced
        comma_fixed_text = re.sub(r',,+', ',', comma_fixed_text)
        
        # Step 7: Remove trailing commas before closing brackets/braces
        comma_fixed_text = re.sub(r',\s*([}\]])', r'\1', comma_fixed_text)
        
        # Try parsing the comma-fixed version
        try:
            comma_parsed = json.loads(comma_fixed_text)
            if isinstance(comma_parsed, dict):
                comma_parsed.setdefault("summary", "")
                comma_parsed.setdefault("dependencies", [])
                comma_parsed.setdefault("tags", [])
                logger.debug(f"Successfully parsed comma-fixed JSON: {comma_parsed}")
                return comma_parsed
        except json.JSONDecodeError as e:
            logger.debug(f"Comma-fixed JSON still failed: {e}")
            logger.debug(f"Comma-fixed text: {comma_fixed_text[:200]}...")
            pass
        
        # Strategy: Find JSON objects with regex patterns
        logger.info(f"Attempting regex extraction on text length: {len(text)}")
        json_patterns = [
            r'\{[^{}]*"summary"[^{}]*\}',  # Simple JSON with summary
            r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',  # Nested JSON objects
            r'\{[^}]*\}',  # Any JSON-like structure
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # Clean the match
                    cleaned_match = match.strip()
                    # Fix common JSON issues
                    cleaned_match = re.sub(r',\s*([}\]])', r'\1', cleaned_match)  # Remove trailing commas
                    cleaned_match = re.sub(r'(["\w])\s*:\s*(["\w])', r'\1: \2', cleaned_match)  # Fix spacing
                    
                    result = json.loads(cleaned_match)
                    if isinstance(result, dict) and ('summary' in result or 'tags' in result):
                        # Ensure required fields exist
                        result.setdefault("summary", "")
                        result.setdefault("dependencies", [])
                        result.setdefault("tags", [])
                        logger.debug(f"Successfully extracted JSON with regex: {result}")
                        return result
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON decode error on match '{cleaned_match[:50]}...': {e}")
                    continue
        
        # Final fallback: Try to extract meaningful information even from broken JSON
        fallback_result = {"summary": "", "dependencies": [], "tags": []}
        
        # Extract any quoted strings that might be summaries
        summary_candidates = re.findall(r'["\']([^"\']{10,100})["\']', text)
        if summary_candidates:
            # Use the longest reasonable string as summary
            fallback_result["summary"] = max(summary_candidates, key=len)
        
        # Extract any array-like content for tags
        tags_candidates = re.findall(r'\[(.*?)\]', text, re.DOTALL)
        for candidate in tags_candidates:
            # Extract quoted strings from arrays
            tags = re.findall(r'["\']([^"\']+)["\']', candidate)
            if tags:
                fallback_result["tags"] = tags[:5]  # Limit to 5 tags
                break
        
        # If we couldn't extract anything meaningful, use generic values
        if not fallback_result["summary"]:
            fallback_result["summary"] = "Analysis completed"
        if not fallback_result["tags"]:
            fallback_result["tags"] = ["parsed"]
            
        logger.warning(f"Could not extract meaningful data from: {text[:100]}...")
        return fallback_result
        if tags_match:
            tags_text = tags_match.group(1)
            tags = [tag.strip().strip('"') for tag in tags_text.split(',')]
            fallback_result["tags"] = [tag for tag in tags if tag]
        
        # If we found some content, return it
        if fallback_result["summary"] or fallback_result["tags"]:
            logger.debug(f"Used fallback extraction: {fallback_result}")
            return fallback_result
        
        # Final fallback - create a basic response
        logger.warning(f"Could not extract meaningful data from: {text[:100]}...")
        return {
            "summary": "Could not parse LLM response",
            "dependencies": [],
            "tags": ["parsing_failed"]
        }
        
    except Exception as e:
        logger.error(f"Error extracting LLM response: {e}")
        return {
            "summary": f"Error processing response: {str(e)}",
            "dependencies": [],
            "tags": ["error"]
        }


# Chunked Enrichment Strategy Functions

def extract_chunks(ast_nodes: list[dict]) -> dict:
    """
    Extract class and method chunks from AST for chunked processing.
    
    Args:
        ast_nodes (list[dict]): List of AST node dictionaries
        
    Returns:
        dict: Dictionary with class_chunks and method_chunks
    """
    class_chunks = []
    method_chunks = []
    
    # Navigate through the AST structure
    for node in ast_nodes:
        if node.get("type") == "Namespace":
            # Look inside namespace body
            for namespace_item in node.get("body", []):
                if namespace_item.get("type") == "Class":
                    # Extract class core metadata
                    class_core = {
                        "type": namespace_item["type"],
                        "name": namespace_item["name"],
                        "startLine": namespace_item.get("startLine"),
                        "modifiers": namespace_item.get("modifiers", []),
                        "baseTypes": namespace_item.get("baseTypes", [])
                    }
                    
                    # Extract methods from class body
                    class_methods = []
                    for body_item in namespace_item.get("body", []):
                        if body_item.get("type") == "Method":
                            method_chunk = {
                                "class_name": namespace_item["name"],
                                "method": body_item
                            }
                            method_chunks.append(method_chunk)
                            class_methods.append(body_item["name"])
                    
                    # Add class chunk with method names list
                    class_core["method_names"] = class_methods
                    class_chunks.append(class_core)
        elif node.get("type") == "Class":
            # Direct class node (not in namespace)
            class_core = {
                "type": node["type"],
                "name": node["name"],
                "startLine": node.get("startLine"),
                "modifiers": node.get("modifiers", []),
                "baseTypes": node.get("baseTypes", [])
            }
            
            class_methods = []
            for body_item in node.get("body", []):
                if body_item.get("type") == "Method":
                    method_chunk = {
                        "class_name": node["name"],
                        "method": body_item
                    }
                    method_chunks.append(method_chunk)
                    class_methods.append(body_item["name"])
            
            class_core["method_names"] = class_methods
            class_chunks.append(class_core)
    
    return {
        "class_chunks": class_chunks,
        "method_chunks": method_chunks
    }


def enrich_class(class_data: dict, methods: list[str]) -> dict:
    """
    Enrich class-level metadata using LLM or mock data.
    
    Args:
        class_data (dict): Class metadata
        methods (list[str]): List of method names in the class
        
    Returns:
        dict: Enriched class metadata
    """
    # Use mock enrichment if LLM is unavailable or mock mode is enabled
    if is_mock_mode():
        logger.info(f"Using mock enrichment for class: {class_data['name']}")
        return mock_enrich_class(class_data, methods)
    
    try:
        # Load class-specific prompt template
        class_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompt_templates', 'csharp_class_enrich_prompt.txt')
        if os.path.exists(class_prompt_path):
            with open(class_prompt_path, 'r') as f:
                prompt_template = f.read()
        else:
            # Fallback template
            prompt_template = """Analyze this C# class and return ONLY JSON:
            
            Class: {{AST_JSON}}
            
            Required JSON format:
            {"summary":"brief description","tags":["keywords"],"dependencies":["types"]}
            
            JSON:"""
        
        # Prepare class data for prompt
        class_summary = {
            "name": class_data['name'],
            "type": class_data['type'],
            "methods": methods[:5],  # Limit to avoid token overflow
            "modifiers": class_data.get('modifiers', []),
            "base_types": class_data.get('baseTypes', [])
        }
        
        prompt = prompt_template.replace('{{AST_JSON}}', json.dumps(class_summary, indent=2))
        
        logger.info(f"Enriching class: {class_data['name']}")
        result = call_llm_with_retry(prompt, max_retries=3, timeout=45)
        enrichment = extract_enriched_data(result)
        
        # Validate and ensure we have proper structure
        if enrichment and isinstance(enrichment, dict):
            return enrichment
        else:
            return {"summary": f"Analysis of {class_data['name']} class", "tags": ["class"], "dependencies": []}
            
    except Exception as e:
        logger.error(f"Error enriching class {class_data['name']}: {e}")
        logger.info(f"Falling back to mock enrichment for class: {class_data['name']}")
        return mock_enrich_class(class_data, methods)


def enrich_method(class_name: str, method_data: dict) -> dict:
    """
    Enrich individual method using LLM or mock data.
    
    Args:
        class_name (str): Name of the containing class
        method_data (dict): Method metadata
        
    Returns:
        dict: Enriched method metadata
    """
    # Use mock enrichment if LLM is unavailable or mock mode is enabled
    if is_mock_mode():
        logger.debug(f"Using mock enrichment for method: {class_name}.{method_data['name']}")
        return mock_enrich_method(class_name, method_data)
    
    try:
        # Load method-specific prompt template
        method_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompt_templates', 'csharp_method_enrich_prompt.txt')
        if os.path.exists(method_prompt_path):
            with open(method_prompt_path, 'r') as f:
                prompt_template = f.read()
        else:
            # Fallback template
            prompt_template = """Analyze this C# method and return ONLY JSON:
            
            Method: {{AST_JSON}}
            
            Required JSON format:
            {"summary":"brief description","tags":["keywords"],"dependencies":["types"]}
            
            JSON:"""
        
        # Prepare method data with validation
        method_summary = {
            "class": class_name,
            "name": method_data.get('name', 'UnknownMethod'),
            "type": method_data.get('type', 'method'),
            "returnType": method_data.get('returnType', 'void'),
            "parameters": method_data.get('parameters', [])[:3],  # Limit params
            "modifiers": method_data.get('modifiers', [])
        }
        
        # Add some context about the method for better LLM understanding
        if method_data.get('parameters'):
            method_summary["parameterCount"] = len(method_data['parameters'])
        if method_data.get('body'):
            method_summary["hasBody"] = True
        
        # Ensure we have valid data to send
        if not method_summary.get("name") or method_summary["name"] == "UnknownMethod":
            logger.warning(f"Method data missing or invalid for class {class_name}: {method_data}")
            return mock_enrich_method(class_name, method_data)
        
        prompt = prompt_template.replace('{{AST_JSON}}', json.dumps(method_summary, indent=2))
        
        logger.debug(f"Enriching method: {class_name}.{method_data['name']} with data: {method_summary}")
        result = call_llm_with_retry(prompt, max_retries=2, timeout=30)
        
        # Validate the LLM response
        if not result or "response" not in result:
            logger.warning(f"Invalid LLM response for method {class_name}.{method_data['name']}: {result}")
            return mock_enrich_method(class_name, method_data)
        
        enrichment = extract_enriched_data(result)
        
        # Validate enrichment result
        if not enrichment or not isinstance(enrichment, dict):
            logger.warning(f"Failed to extract enrichment for method {class_name}.{method_data['name']}")
            enrichment = {"summary": f"Method {method_data['name']}", "tags": ["method"], "dependencies": []}
        
        # Ensure all required fields are present
        enrichment.setdefault("summary", f"Method {method_data.get('name', 'Unknown')}")
        enrichment.setdefault("tags", ["method"])
        enrichment.setdefault("dependencies", [])
        
        # Return method with enrichment
        return {
            **method_data,
            "enrichment": enrichment
        }
            
    except Exception as e:
        logger.debug(f"Error enriching method {class_name}.{method_data['name']}: {e}")
        logger.debug(f"Falling back to mock enrichment for method: {class_name}.{method_data['name']}")
        return mock_enrich_method(class_name, method_data)


def compose_enriched_class(class_core: dict, class_meta: dict, enriched_methods: list[dict]) -> dict:
    """
    Merge class core data, class-level enrichment, and enriched methods.
    
    Args:
        class_core (dict): Core class metadata
        class_meta (dict): Class-level enrichment data
        enriched_methods (list[dict]): List of enriched method data
        
    Returns:
        dict: Complete enriched class data
    """
    # Create the enriched class by merging everything
    enriched_class = {
        **class_core,
        "enrichment": class_meta,  # Add class-level enrichment
        "body": enriched_methods  # Replace body with enriched methods
    }
    
    return enriched_class


def enrich_ast(ast_nodes: list[dict], enriched_output_path: str) -> dict:
    """
    Chunked enrichment pipeline: processes classes and methods separately.
    
    This function implements a chunked strategy to avoid JSON parsing errors:
    1. Extract class and method chunks from AST
    2. Enrich each class with class-level metadata
    3. Enrich each method individually
    4. Compose everything into final enriched output
    5. Save to disk and return
    
    Args:
        ast_nodes (list[dict]): List of AST node dictionaries to enrich
        enriched_output_path (str): Path where the enriched JSON will be saved
        
    Returns:
        dict: Combined data with the original AST and enrichment metadata
        
    Raises:
        Exception: If any step in the pipeline fails
    """
    try:
        logger.info("Starting chunked enrichment pipeline...")
        
        # Step 1: Extract chunks
        logger.info("Extracting class and method chunks...")
        chunks = extract_chunks(ast_nodes)
        class_chunks = chunks["class_chunks"]
        method_chunks = chunks["method_chunks"]
        # If no methods to enrich, use original pipeline for simplicity
        if not method_chunks:
            logger.info("No method chunks detected, using original enrichment strategy...")
            raw_response = call_llm(ast_nodes)
            enriched = extract_enriched_data(raw_response)
            final_output = {
                "ast": ast_nodes,
                "summary": enriched.get("summary", ""),
                "dependencies": enriched.get("dependencies", []),
                "tags": enriched.get("tags", []),
                "processing_info": {"strategy": "original"}
            }
            with open(enriched_output_path, "w", encoding="utf-8") as f:
                json.dump(final_output, f, indent=2)
            logger.info(f"Original enrichment completed. Saved to {enriched_output_path}")
            return final_output
        
        logger.info(f"Found {len(class_chunks)} classes and {len(method_chunks)} methods")
        
        # Step 2: Enrich classes
        enriched_classes = []
        for class_data in class_chunks:
            class_methods = class_data.get("method_names", [])
            class_meta = enrich_class(class_data, class_methods)
            
            # Find enriched methods for this class
            class_enriched_methods = []
            for method_chunk in method_chunks:
                if method_chunk["class_name"] == class_data["name"]:
                    enriched_method = enrich_method(method_chunk["class_name"], method_chunk["method"])
                    class_enriched_methods.append(enriched_method)
            
            # Compose the complete enriched class
            enriched_class = compose_enriched_class(class_data, class_meta, class_enriched_methods)
            enriched_classes.append(enriched_class)
        
        # Step 3: Aggregate class-level data for overall summary
        all_summaries = []
        all_tags = []
        all_dependencies = []
        
        for enriched_class in enriched_classes:
            class_enrich = enriched_class.get("class_enrichment", {})
            if class_enrich.get("summary"):
                all_summaries.append(f"{enriched_class['name']}: {class_enrich['summary']}")
            all_tags.extend(class_enrich.get("tags", []))
            all_dependencies.extend(class_enrich.get("dependencies", []))
        
        # Remove duplicates and create overall summary
        unique_tags = list(set(all_tags))
        unique_dependencies = list(set(all_dependencies))
        overall_summary = "; ".join(all_summaries) if all_summaries else "C# code analysis"
        
        # Step 4: Replace classes in AST with enriched versions
        enriched_ast = []
        for node in ast_nodes:
            if node.get("type") == "Namespace":
                # Create new namespace with enriched classes
                enriched_body = []
                for body_item in node.get("body", []):
                    if body_item.get("type") == "Class":
                        # Find the corresponding enriched class
                        enriched_class = None
                        for ec in enriched_classes:
                            if ec["name"] == body_item["name"]:
                                enriched_class = ec
                                break
                        
                        if enriched_class:
                            enriched_body.append(enriched_class)
                        else:
                            # Keep original if no enrichment found
                            enriched_body.append(body_item)
                    else:
                        # Keep non-class items as-is
                        enriched_body.append(body_item)
                
                # Create new namespace with enriched body
                enriched_namespace = {
                    **node,
                    "body": enriched_body
                }
                enriched_ast.append(enriched_namespace)
            else:
                # Keep non-namespace nodes as-is
                enriched_ast.append(node)
        
        # Step 5: Create final output
        final_output = {
            "ast": enriched_ast,
            "summary": overall_summary,
            "dependencies": unique_dependencies,
            "tags": unique_tags,
            "enriched_classes": enriched_classes,
            "processing_info": {
                "classes_processed": len(class_chunks),
                "methods_processed": len(method_chunks),
                "strategy": "chunked"
            }
        }

        # Step 6: Save the enriched data
        with open(enriched_output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2)

        logger.info(f"Chunked enrichment completed. Saved to {enriched_output_path}")
        logger.info(f"Processed {len(class_chunks)} classes and {len(method_chunks)} methods")
        return final_output
        
    except Exception as e:
        logger.error(f"Error in chunked enrichment pipeline: {e}")
        
        # Create a minimal fallback output
        fallback_output = {
            "ast": ast_nodes,
            "summary": f"Error during chunked enrichment: {str(e)}",
            "dependencies": [],
            "tags": ["error", "enrichment_failed"],
            "error": str(e),
            "processing_info": {
                "classes_processed": 0,
                "methods_processed": 0,
                "strategy": "chunked_fallback"
            }
        }
        
        # Try to save the fallback output
        try:
            with open(enriched_output_path, "w", encoding="utf-8") as f:
                json.dump(fallback_output, f, indent=2)
            logger.info(f"Fallback output saved to {enriched_output_path}")
        except Exception as save_error:
            logger.error(f"Failed to save fallback output: {save_error}")
            
        # Re-raise the original exception
        raise


# Original enrichment functions (kept for backward compatibility)

def call_llm_original(ast_nodes: list[dict]) -> dict:
    """
    Original function: Calls the LLM with full AST and returns raw JSON response.
    Kept for backward compatibility.
    
    Args:
        ast_nodes (list[dict): List of AST node dictionaries to analyze
        
    Returns:
        dict: Raw JSON response from the LLM API
    """
    prompt = build_prompt(ast_nodes)
    logger.debug(f"Prompt length: {len(prompt)} characters")
    
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.9,
            "max_tokens": 512
        }
    }
    
    logger.info(f"Using LLM model: {LLM_MODEL}")
    
    try:
        logger.info(f"Sending request to Ollama API at {OLLAMA_BASE_URL}/api/generate")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=600
        )
        
        logger.info(f"Received response from Ollama API: HTTP {response.status_code}")
        response.raise_for_status()
        
        try:
            result = response.json()
            if result:
                logger.info(f"Response keys: {list(result.keys())}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.error(f"Raw response text: {response.text[:200]}...")
            return {
                "response": "",
                "error": f"Invalid JSON in response: {str(e)}",
                "raw_text": response.text[:500] if response.text else ""
            }
            
    except requests.RequestException as e:
        logger.error(f"Error calling Ollama LLM: {e}")
        return {
            "response": "",
            "error": f"Request failed: {str(e)}",
            "exception_type": type(e).__name__
        }


def enrich_ast_original(ast_nodes: list[dict], enriched_output_path: str) -> dict:
    """
    Original enrichment pipeline: calls LLM with full AST, saves enriched JSON to disk.
    Kept for backward compatibility.
    
    Args:
        ast_nodes (list[dict]): List of AST node dictionaries to enrich
        enriched_output_path (str): Path where the enriched JSON will be saved
        
    Returns:
        dict: Combined data with the original AST and enrichment metadata
    """
    try:
        logger.info("Using original enrichment strategy...")
        raw_response = call_llm_original(ast_nodes)
        enriched = extract_enriched_data(raw_response)

        final_output = {
            "ast": ast_nodes,
            "summary": enriched.get("summary", ""),
            "dependencies": enriched.get("dependencies", []),
            "tags": enriched.get("tags", []),
            "processing_info": {
                "strategy": "original"
            }
        }

        with open(enriched_output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2)

        logger.info(f"Original enrichment completed. Saved to {enriched_output_path}")
        return final_output
    except Exception as e:
        logger.error(f"Error in original enrichment pipeline: {e}")
        fallback_output = {
            "ast": ast_nodes,
            "summary": f"Error during original enrichment: {str(e)}",
            "dependencies": [],
            "tags": ["error", "enrichment_failed"],
            "error": str(e)
        }
        
        try:
            with open(enriched_output_path, "w", encoding="utf-8") as f:
                json.dump(fallback_output, f, indent=2)
            logger.info(f"Fallback output saved to {enriched_output_path}")
        except Exception as save_error:
            logger.error(f"Failed to save fallback output: {save_error}")
            
        raise

# Alias for backward compatibility
call_llm = call_llm_original

# Mock enrichment for testing without LLM
def is_mock_mode():
    """Check if mock enrichment mode is enabled."""
    return os.getenv("MOCK_ENRICHMENT", "false").lower() == "true"

def mock_enrich_class(class_data: dict, methods: list[str]) -> dict:
    """
    Mock enrichment for testing without LLM.
    """
    class_name = class_data.get('name', 'Unknown')
    base_types = class_data.get('baseTypes', [])
    
    # Generate realistic mock data based on class characteristics
    if 'Controller' in class_name:
        return {
            "summary": f"API controller for {class_name.replace('Controller', '').lower()} operations",
            "tags": ["controller", "api", "web"],
            "dependencies": base_types + ["IActionResult", "HttpContext"]
        }
    elif 'Service' in class_name:
        return {
            "summary": f"Business service handling {class_name.replace('Service', '').lower()} logic",
            "tags": ["service", "business-logic"],
            "dependencies": base_types + ["Repository", "Domain"]
        }
    elif 'Repository' in class_name:
        return {
            "summary": f"Data access repository for {class_name.replace('Repository', '').lower()} entities",
            "tags": ["repository", "data-access", "persistence"],
            "dependencies": base_types + ["Entity", "DbContext"]
        }
    elif 'Request' in class_name:
        return {
            "summary": f"Data transfer object for {class_name.replace('Request', '').lower()} requests",
            "tags": ["dto", "request", "model"],
            "dependencies": base_types
        }
    else:
        return {
            "summary": f"Domain entity representing {class_name.lower()}",
            "tags": ["entity", "domain", "model"],
            "dependencies": base_types
        }

def mock_enrich_method(class_name: str, method_data: dict) -> dict:
    """
    Mock enrichment for methods without LLM.
    """
    method_name = method_data.get('name', 'Unknown')
    method_type = method_data.get('type', 'Method')
    return_type = method_data.get('returnType')
    parameters = method_data.get('parameters', [])
    
    # Generate realistic enrichment based on method characteristics
    tags = ["method"]
    dependencies = []
    
    if method_type == "Constructor":
        summary = f"Initializes a new instance of {class_name}"
        tags.extend(["constructor", "initialization"])
    elif method_name.lower().startswith('get'):
        summary = f"Retrieves {method_name[3:].lower()} data"
        tags.extend(["getter", "query", "read"])
    elif method_name.lower().startswith('create'):
        summary = f"Creates a new {method_name[6:].lower()}"
        tags.extend(["create", "write", "insert"])
    elif method_name.lower().startswith('update'):
        summary = f"Updates existing {method_name[6:].lower()}"
        tags.extend(["update", "write", "modify"])
    elif method_name.lower().startswith('delete'):
        summary = f"Deletes {method_name[6:].lower()}"
        tags.extend(["delete", "write", "remove"])
    else:
        summary = f"Performs {method_name.lower()} operation"
        tags.append("operation")
    
    # Add dependencies from parameters and return type
    if return_type:
        dependencies.append(return_type)
    for param in parameters:
        if param.get('type'):
            dependencies.append(param['type'])
    
    return {
        **method_data,
        "enrichment": {
            "summary": summary,
            "tags": tags,
            "dependencies": list(set(dependencies))  # Remove duplicates
        }
    }

def call_llm_with_retry(prompt: str, max_retries: int = 3, timeout: int = 45) -> dict:
    """
    Call LLM with retry mechanism for better reliability.
    
    Args:
        prompt (str): The prompt to send to the LLM
        max_retries (int): Maximum number of retry attempts
        timeout (int): Timeout for each request
        
    Returns:
        dict: LLM response or error response
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            payload = {
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,     # Deterministic output
                    "top_p": 0.1,          # Very focused
                    "max_tokens": 200,     # Shorter responses
                    "stop": ["}\n", "}\r\n", "}\r", "JSON:", "\n\n", "```", "SYSTEM:", "INSTRUCTION:", "FORMAT:", "RULES:", "Method:", "Class:"],  # Stop after JSON object
                    "repeat_penalty": 1.0,  # No penalty
                    "num_predict": 150,     # Predict fewer tokens
                    "mirostat": 2,         # Use mirostat for better stopping
                    "mirostat_tau": 1.0
                }
            }
            
            logger.debug(f"LLM call attempt {attempt + 1}/{max_retries}")
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Log the raw response for debugging
            raw_response_text = response.text[:300] if response.text else "No response text"
            logger.debug(f"Raw LLM response (attempt {attempt + 1}): {raw_response_text}")
            
            result = response.json()
            
            # Validate that we got a proper response
            if "response" in result:
                response_text = result["response"].strip()
                if response_text:
                    # Check if response contains JSON or meaningful content
                    if "{" in response_text or "summary" in response_text.lower():
                        return result
                    elif len(response_text) > 10:  # Accept longer responses even if not JSON
                        return result
                    else:
                        raise ValueError(f"Response too short or invalid: {response_text[:50]}")
                else:
                    raise ValueError("Empty response from LLM")
            else:
                raise ValueError("No 'response' field in LLM result")
                
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            last_error = e
            logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                # Wait before retrying (exponential backoff)
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                import time
                time.sleep(wait_time)
            continue
    
    # All retries failed
    logger.error(f"All {max_retries} LLM call attempts failed. Last error: {last_error}")
    # Return a response that mimics successful LLM output for fallback handling
    return {
        "response": '{"summary":"Analysis failed - using fallback","tags":["fallback","error"],"dependencies":[]}',
        "error": f"All retry attempts failed: {str(last_error)}",
        "exception_type": type(last_error).__name__,
        "fallback": True
    }
