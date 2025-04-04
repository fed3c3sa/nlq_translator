"""
Elasticsearch query generator for NLQ Translator.

This module provides functionality for generating Elasticsearch queries
from natural language using language models.
"""

import json
from typing import Dict, Any, Optional, List, Union, Tuple

from ..llm import LLMInterface, OpenAILLM


class ElasticsearchQueryGenerator:
    """
    Generates Elasticsearch queries from natural language.
    
    This class uses language models to translate natural language queries
    into Elasticsearch queries, with support for database mapping.
    """
    
    def __init__(self, llm: Optional[LLMInterface] = None):
        """
        Initialize the Elasticsearch query generator.
        
        Args:
            llm: Optional language model interface to use for translation.
                If not provided, will use OpenAILLM with default settings.
        """
        self.llm = llm or OpenAILLM()
    
    def generate_query(
        self, 
        natural_language: str,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an Elasticsearch query from natural language.
        
        Args:
            natural_language: The natural language query to translate.
            mapping: Optional Elasticsearch mapping information.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            A dictionary representing the Elasticsearch query.
            
        Raises:
            ValueError: If the generated query is not valid JSON.
            Exception: If there is an error generating the query.
        """
        try:
            response = self.llm.translate_to_query(
                natural_language=natural_language,
                database_type="elasticsearch",
                mapping=mapping,
                **kwargs
            )
            
            # Parse the response as JSON
            try:
                query = json.loads(response.content)
                return query
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response if it contains markdown or explanations
                try:
                    # Look for JSON between triple backticks
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response.content)
                    if json_match:
                        query = json.loads(json_match.group(1))
                        return query
                    
                    # If no JSON found between backticks, try to find any JSON object in the response
                    json_match = re.search(r'({[\s\S]*})', response.content)
                    if json_match:
                        query = json.loads(json_match.group(1))
                        return query
                    
                    raise ValueError(f"Generated query is not valid JSON: {e}")
                except Exception:
                    raise ValueError(f"Generated query is not valid JSON: {e}")
        except Exception as e:
            raise Exception(f"Error generating Elasticsearch query: {str(e)}")
    
    def fix_query(
        self, 
        query: Union[str, Dict[str, Any]],
        error_message: Optional[str] = None,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fix errors in an Elasticsearch query.
        
        Args:
            query: The Elasticsearch query to fix (string or dictionary).
            error_message: Optional error message to help guide the fix.
            mapping: Optional Elasticsearch mapping information.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            A dictionary representing the fixed Elasticsearch query.
            
        Raises:
            ValueError: If the fixed query is not valid JSON.
            Exception: If there is an error fixing the query.
        """
        # Convert query to string if it's a dictionary
        if isinstance(query, dict):
            query_str = json.dumps(query, indent=2)
        else:
            query_str = query
        
        try:
            response = self.llm.fix_query(
                query=query_str,
                database_type="elasticsearch",
                error_message=error_message,
                mapping=mapping,
                **kwargs
            )
            
            # Parse the response as JSON
            try:
                fixed_query = json.loads(response.content)
                return fixed_query
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response if it contains markdown or explanations
                try:
                    # Look for JSON between triple backticks
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response.content)
                    if json_match:
                        fixed_query = json.loads(json_match.group(1))
                        return fixed_query
                    
                    # If no JSON found between backticks, try to find any JSON object in the response
                    json_match = re.search(r'({[\s\S]*})', response.content)
                    if json_match:
                        fixed_query = json.loads(json_match.group(1))
                        return fixed_query
                    
                    raise ValueError(f"Fixed query is not valid JSON: {e}")
                except Exception:
                    raise ValueError(f"Fixed query is not valid JSON: {e}")
        except Exception as e:
            raise Exception(f"Error fixing Elasticsearch query: {str(e)}")
    
    def improve_query(
        self, 
        query: Union[str, Dict[str, Any]],
        improvement_goal: Optional[str] = None,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Improve an Elasticsearch query for better performance or results.
        
        Args:
            query: The Elasticsearch query to improve (string or dictionary).
            improvement_goal: Optional description of the improvement goal.
            mapping: Optional Elasticsearch mapping information.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            A dictionary representing the improved Elasticsearch query.
            
        Raises:
            ValueError: If the improved query is not valid JSON.
            Exception: If there is an error improving the query.
        """
        # Convert query to string if it's a dictionary
        if isinstance(query, dict):
            query_str = json.dumps(query, indent=2)
        else:
            query_str = query
        
        try:
            response = self.llm.improve_query(
                query=query_str,
                database_type="elasticsearch",
                improvement_goal=improvement_goal,
                mapping=mapping,
                **kwargs
            )
            
            # Parse the response as JSON
            try:
                improved_query = json.loads(response.content)
                return improved_query
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response if it contains markdown or explanations
                try:
                    # Look for JSON between triple backticks
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response.content)
                    if json_match:
                        improved_query = json.loads(json_match.group(1))
                        return improved_query
                    
                    # If no JSON found between backticks, try to find any JSON object in the response
                    json_match = re.search(r'({[\s\S]*})', response.content)
                    if json_match:
                        improved_query = json.loads(json_match.group(1))
                        return improved_query
                    
                    raise ValueError(f"Improved query is not valid JSON: {e}")
                except Exception:
                    raise ValueError(f"Improved query is not valid JSON: {e}")
        except Exception as e:
            raise Exception(f"Error improving Elasticsearch query: {str(e)}")
