"""
LLM Interface for NLQ Translator.

This module defines the interface for language models used in the NLQ Translator.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union


@dataclass
class LLMResponse:
    """
    Data class representing a response from a language model.
    
    Attributes:
        content: The text content of the response.
        raw_response: The raw response from the language model.
        usage: Information about token usage.
        model: The model used for the response.
    """
    content: str
    raw_response: Any
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class LLMInterface(ABC):
    """
    Abstract base class for language model interfaces.
    
    This class defines the interface that all language model implementations
    must follow to be used with the NLQ Translator.
    """
    
    @abstractmethod
    def generate_response(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the language model.
        
        Args:
            prompt: The prompt to send to the language model.
            context: Optional context information to include in the prompt.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            An LLMResponse object containing the generated response.
        """
        pass
    
    @abstractmethod
    def translate_to_query(
        self, 
        natural_language: str, 
        database_type: str,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Translate a natural language query to a database query.
        
        Args:
            natural_language: The natural language query to translate.
            database_type: The type of database to generate a query for.
            mapping: Optional mapping information for the database.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            An LLMResponse object containing the generated database query.
        """
        pass
    
    @abstractmethod
    def fix_query(
        self, 
        query: str, 
        database_type: str,
        error_message: Optional[str] = None,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Fix errors in a database query.
        
        Args:
            query: The database query to fix.
            database_type: The type of database the query is for.
            error_message: Optional error message to help guide the fix.
            mapping: Optional mapping information for the database.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            An LLMResponse object containing the fixed database query.
        """
        pass
    
    @abstractmethod
    def improve_query(
        self, 
        query: str, 
        database_type: str,
        improvement_goal: Optional[str] = None,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Improve a database query for better performance or results.
        
        Args:
            query: The database query to improve.
            database_type: The type of database the query is for.
            improvement_goal: Optional description of the improvement goal.
            mapping: Optional mapping information for the database.
            **kwargs: Additional arguments to pass to the language model.
            
        Returns:
            An LLMResponse object containing the improved database query.
        """
        pass
