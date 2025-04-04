"""
Elasticsearch query validator for NLQ Translator.

This module provides functionality for validating Elasticsearch queries
and identifying common errors.
"""

import json
from typing import Dict, Any, Optional, List, Union, Tuple, Set


class ElasticsearchQueryValidator:
    """
    Validates Elasticsearch queries and identifies errors.
    
    This class provides methods for checking if an Elasticsearch query is valid
    and identifying common errors in the query structure.
    """
    
    # Set of valid top-level Elasticsearch query keys
    VALID_TOP_LEVEL_KEYS: Set[str] = {
        "query", "from", "size", "sort", "aggs", "aggregations", 
        "_source", "fields", "script_fields", "stored_fields", 
        "highlight", "post_filter", "rescore", "explain", "version",
        "track_total_hits", "min_score", "track_scores", "timeout",
        "terminate_after", "search_after", "pit", "runtime_mappings"
    }
    
    # Set of valid query types
    VALID_QUERY_TYPES: Set[str] = {
        "match", "match_phrase", "match_phrase_prefix", "match_bool_prefix",
        "multi_match", "term", "terms", "range", "exists", "prefix", "wildcard",
        "regexp", "fuzzy", "ids", "bool", "dis_max", "function_score", "boosting",
        "nested", "has_child", "has_parent", "parent_id", "geo_shape", "geo_bounding_box",
        "geo_distance", "geo_polygon", "more_like_this", "script", "script_score",
        "wrapper", "pinned", "distance_feature", "rank_feature", "percolate",
        "intervals", "match_all", "match_none"
    }
    
    def __init__(self, mapping: Optional[Dict[str, Any]] = None):
        """
        Initialize the Elasticsearch query validator.
        
        Args:
            mapping: Optional Elasticsearch mapping information to use for validation.
        """
        self.mapping = mapping
    
    def validate(self, query: Union[str, Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Validate an Elasticsearch query.
        
        Args:
            query: The Elasticsearch query to validate (string or dictionary).
            
        Returns:
            A tuple containing:
                - A boolean indicating whether the query is valid.
                - An error message if the query is invalid, or None if it's valid.
        """
        # Convert string to dict if needed
        if isinstance(query, str):
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {str(e)}"
        else:
            query_dict = query
        
        # Check if query is a dictionary
        if not isinstance(query_dict, dict):
            return False, "Query must be a JSON object"
        
        # Validate top-level structure
        top_level_errors = self._validate_top_level_structure(query_dict)
        if top_level_errors:
            return False, top_level_errors
        
        # Validate query structure if present
        if "query" in query_dict:
            query_errors = self._validate_query_structure(query_dict["query"])
            if query_errors:
                return False, query_errors
        
        # Validate against mapping if available
        if self.mapping:
            mapping_errors = self._validate_against_mapping(query_dict)
            if mapping_errors:
                return False, mapping_errors
        
        return True, None
    
    def _validate_top_level_structure(self, query_dict: Dict[str, Any]) -> Optional[str]:
        """
        Validate the top-level structure of an Elasticsearch query.
        
        Args:
            query_dict: The Elasticsearch query dictionary.
            
        Returns:
            An error message if the structure is invalid, or None if it's valid.
        """
        # Check for unknown top-level keys
        unknown_keys = [key for key in query_dict.keys() if key not in self.VALID_TOP_LEVEL_KEYS]
        if unknown_keys:
            return f"Unknown top-level keys: {', '.join(unknown_keys)}"
        
        # Check if size and from are non-negative integers
        if "size" in query_dict and (not isinstance(query_dict["size"], int) or query_dict["size"] < 0):
            return "'size' must be a non-negative integer"
        
        if "from" in query_dict and (not isinstance(query_dict["from"], int) or query_dict["from"] < 0):
            return "'from' must be a non-negative integer"
        
        return None
    
    def _validate_query_structure(self, query: Any) -> Optional[str]:
        """
        Validate the structure of the 'query' part of an Elasticsearch query.
        
        Args:
            query: The 'query' part of the Elasticsearch query.
            
        Returns:
            An error message if the structure is invalid, or None if it's valid.
        """
        # Check if query is a dictionary
        if not isinstance(query, dict):
            return "'query' must be a JSON object"
        
        # Check if query is empty
        if not query:
            return "'query' cannot be empty"
        
        # Check query type
        query_type = next(iter(query.keys()), None)
        
        # Special case for match_all which can be empty
        if query_type == "match_all" and (not query[query_type] or query[query_type] == {}):
            return None
        
        # Validate query type
        if query_type not in self.VALID_QUERY_TYPES:
            return f"Unknown query type: {query_type}"
        
        # Validate bool query if present
        if query_type == "bool":
            bool_query = query["bool"]
            if not isinstance(bool_query, dict):
                return "'bool' query must be a JSON object"
            
            valid_bool_clauses = {"must", "must_not", "should", "filter", "minimum_should_match", "boost"}
            unknown_clauses = [clause for clause in bool_query.keys() if clause not in valid_bool_clauses]
            if unknown_clauses:
                return f"Unknown 'bool' clauses: {', '.join(unknown_clauses)}"
            
            # Validate each clause
            for clause in ["must", "must_not", "should", "filter"]:
                if clause in bool_query:
                    clause_value = bool_query[clause]
                    if not isinstance(clause_value, (dict, list)):
                        return f"'{clause}' clause must be a JSON object or array"
                    
                    if isinstance(clause_value, list):
                        for item in clause_value:
                            item_error = self._validate_query_structure(item)
                            if item_error:
                                return f"Error in '{clause}' clause: {item_error}"
                    else:
                        item_error = self._validate_query_structure(clause_value)
                        if item_error:
                            return f"Error in '{clause}' clause: {item_error}"
        
        # Validate nested query if present
        elif query_type == "nested":
            nested_query = query["nested"]
            if not isinstance(nested_query, dict):
                return "'nested' query must be a JSON object"
            
            if "path" not in nested_query:
                return "'nested' query must have a 'path' field"
            
            if "query" not in nested_query:
                return "'nested' query must have a 'query' field"
            
            query_error = self._validate_query_structure(nested_query["query"])
            if query_error:
                return f"Error in 'nested' query: {query_error}"
        
        return None
    
    def _validate_against_mapping(self, query_dict: Dict[str, Any]) -> Optional[str]:
        """
        Validate an Elasticsearch query against a mapping.
        
        Args:
            query_dict: The Elasticsearch query dictionary.
            
        Returns:
            An error message if the query is invalid for the mapping, or None if it's valid.
        """
        if not self.mapping:
            return None
        
        # Extract field names from the mapping
        field_names = self._extract_field_names_from_mapping(self.mapping)
        
        # Find all field names used in the query
        query_fields = self._extract_field_names_from_query(query_dict)
        
        # Check if all query fields exist in the mapping
        unknown_fields = [field for field in query_fields if field not in field_names]
        if unknown_fields:
            return f"Unknown fields in query: {', '.join(unknown_fields)}"
        
        return None
    
    def _extract_field_names_from_mapping(self, mapping: Dict[str, Any]) -> Set[str]:
        """
        Extract all field names from an Elasticsearch mapping.
        
        Args:
            mapping: The Elasticsearch mapping dictionary.
            
        Returns:
            A set of field names.
        """
        field_names = set()
        
        def extract_fields(prefix: str, obj: Dict[str, Any]) -> None:
            if not isinstance(obj, dict):
                return
            
            # Check for properties key which indicates fields
            if "properties" in obj:
                for field_name, field_def in obj["properties"].items():
                    full_name = f"{prefix}{field_name}" if prefix else field_name
                    field_names.add(full_name)
                    
                    # Handle nested fields
                    if field_def.get("type") == "nested" and "properties" in field_def:
                        extract_fields(f"{full_name}.", field_def)
                    elif "properties" in field_def:
                        extract_fields(f"{full_name}.", field_def)
            
            # Handle other keys that might contain mappings
            for key, value in obj.items():
                if key != "properties" and isinstance(value, dict):
                    if prefix:
                        new_prefix = f"{prefix}{key}."
                    else:
                        new_prefix = f"{key}."
                    extract_fields(new_prefix, value)
        
        # Start extraction with no prefix
        extract_fields("", mapping)
        return field_names
    
    def _extract_field_names_from_query(self, query_dict: Dict[str, Any]) -> Set[str]:
        """
        Extract all field names used in an Elasticsearch query.
        
        Args:
            query_dict: The Elasticsearch query dictionary.
            
        Returns:
            A set of field names.
        """
        field_names = set()
        
        def extract_fields(obj: Any) -> None:
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
