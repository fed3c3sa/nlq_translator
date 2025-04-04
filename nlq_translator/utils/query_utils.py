"""
Query utility functions for NLQ Translator.

This module provides utility functions for working with queries in the NLQ Translator library.
"""

import json
import re
from typing import Dict, Any, Optional, List, Union, Set


def format_query(query: Union[str, Dict[str, Any]], indent: int = 2) -> str:
    """
    Format a query as a JSON string with proper indentation.
    
    Args:
        query: The query to format (string or dictionary).
        indent: The number of spaces to use for indentation (default: 2).
        
    Returns:
        The formatted query as a JSON string.
        
    Raises:
        ValueError: If the query is not valid JSON.
    """
    if isinstance(query, str):
        try:
            # Parse and re-format to ensure proper indentation
            query_dict = json.loads(query)
            return json.dumps(query_dict, indent=indent)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON query: {str(e)}")
    else:
        return json.dumps(query, indent=indent)


def parse_query_string(query_string: str) -> Dict[str, Any]:
    """
    Parse a query string into a dictionary.
    
    Args:
        query_string: The query string to parse.
        
    Returns:
        The parsed query as a dictionary.
        
    Raises:
        ValueError: If the query string is not valid JSON.
    """
    try:
        # Try to parse as JSON directly
        return json.loads(query_string)
    except json.JSONDecodeError:
        # Try to extract JSON from the string if it contains markdown or explanations
        try:
            # Look for JSON between triple backticks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', query_string)
            if json_match:
                return json.loads(json_match.group(1))
            
            # If no JSON found between backticks, try to find any JSON object in the string
            json_match = re.search(r'({[\s\S]*})', query_string)
            if json_match:
                return json.loads(json_match.group(1))
            
            raise ValueError("Could not extract valid JSON from the query string")
        except Exception as e:
            raise ValueError(f"Invalid JSON query string: {str(e)}")


def extract_fields_from_query(query: Union[str, Dict[str, Any]]) -> Set[str]:
    """
    Extract all field names used in a query.
    
    Args:
        query: The query to extract fields from (string or dictionary).
        
    Returns:
        A set of field names used in the query.
        
    Raises:
        ValueError: If the query is not valid JSON.
    """
    # Convert query to dictionary if it's a string
    if isinstance(query, str):
        query_dict = parse_query_string(query)
    else:
        query_dict = query
    
    field_names = set()
    
    def extract_fields(obj: Any) -> None:
        """Recursively extract field names from a query object."""
        if not isinstance(obj, dict):
            return
        
        for key, value in obj.items():
            # Check for common query types that use field names
            if key in {"term", "terms", "match", "match_phrase", "range", "exists", "prefix", "wildcard", "regexp", "fuzzy"}:
                if isinstance(value, dict):
                    field_names.update(value.keys())
            
            # Check for multi_match query
            elif key == "multi_match" and isinstance(value, dict) and "fields" in value:
                fields = value["fields"]
                if isinstance(fields, list):
                    for field in fields:
                        # Handle field with boost (field^boost)
                        if "^" in field:
                            field = field.split("^")[0]
                        field_names.add(field)
            
            # Recursively process nested objects and arrays
            elif isinstance(value, dict):
                extract_fields(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, (dict, list)):
                        extract_fields(item)
    
    # Start extraction with the query dictionary
    extract_fields(query_dict)
    return field_names
