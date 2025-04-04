"""
OpenAI LLM implementation for NLQ Translator.

This module provides an implementation of the LLM interface using OpenAI's GPT models.
"""

import json
from typing import Dict, Any, Optional, List, Union, Tuple

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .llm_interface import LLMInterface, LLMResponse
from ..config import APIKeyManager


class OpenAILLM(LLMInterface):
    """
    OpenAI implementation of the LLM interface.
    
    This class provides methods for using OpenAI's GPT models to translate
    natural language queries into database queries.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        api_key_manager: Optional[APIKeyManager] = None
    ):
        """
        Initialize the OpenAI LLM interface.
        
        Args:
            api_key: Optional API key for OpenAI. If not provided, will attempt
                to get it from the APIKeyManager or environment variables.
            model: The OpenAI model to use (default: "gpt-4").
            temperature: The temperature to use for generation (default: 0.1).
            max_tokens: The maximum number of tokens to generate (default: 2000).
            api_key_manager: Optional APIKeyManager instance to use for getting the API key.
        
        Raises:
            ImportError: If the openai package is not installed.
            ValueError: If no API key is provided and none can be found.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "The openai package is required to use OpenAILLM. "
                "Please install it with: pip install openai"
            )
        
        # Get API key if not provided
        if api_key is None:
            if api_key_manager is None:
                api_key_manager = APIKeyManager()
            
            api_key = api_key_manager.get_api_key("openai")
            
            if api_key is None:
                raise ValueError(
                    "No OpenAI API key provided and none found in configuration. "
                    "Please provide an API key or set it in the configuration."
                )
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=api_key)
    
    def generate_response(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the OpenAI model.
        
        Args:
            prompt: The prompt to send to the model.
            context: Optional context information to include in the prompt.
            **kwargs: Additional arguments to pass to the OpenAI API.
            
        Returns:
            An LLMResponse object containing the generated response.
            
        Raises:
            Exception: If there is an error communicating with the OpenAI API.
        """
        # Merge kwargs with default parameters
        params = {
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Add system message if context is provided
        if context:
            system_content = f"Context information: {json.dumps(context)}"
            messages.insert(0, {"role": "system", "content": system_content})
        
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                **params
            )
            
            content = response.choices[0].message.content
            
            return LLMResponse(
                content=content,
                raw_response=response,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                model=response.model
            )
        except Exception as e:
            raise Exception(f"Error generating response from OpenAI: {str(e)}")
    
    def _format_mapping_for_prompt(self, mapping: Dict[str, Any]) -> str:
        """
        Format the Elasticsearch mapping for inclusion in a prompt.
        
        Args:
            mapping: The Elasticsearch mapping dictionary.
            
        Returns:
            A formatted string representation of the mapping.
        """
        if not mapping:
            return "No mapping provided."
        
        try:
            return json.dumps(mapping, indent=2)
        except Exception:
            return str(mapping)
    
    def translate_to_query(
        self, 
        natural_language: str, 
        database_type: str,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Translate a natural language query to an Elasticsearch query.
        
        Args:
            natural_language: The natural language query to translate.
            database_type: The type of database to generate a query for (e.g., "elasticsearch").
            mapping: Optional mapping information for the database.
            **kwargs: Additional arguments to pass to the OpenAI API.
            
        Returns:
            An LLMResponse object containing the generated database query.
        """
        # Prepare the prompt
        prompt = f"""
        Translate the following natural language query into a {database_type} query.
        
        Natural language query: {natural_language}
        
        """
        
        if mapping:
            prompt += f"""
            Use the following database mapping:
            
            ```json
            {self._format_mapping_for_prompt(mapping)}
            ```
            
            """
        
        prompt += f"""
        Return ONLY the {database_type} query as a valid JSON object without any explanations or markdown formatting.
        """
        
        return self.generate_response(prompt, context={"database_type": database_type}, **kwargs)
    
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
            **kwargs: Additional arguments to pass to the OpenAI API.
            
        Returns:
            An LLMResponse object containing the fixed database query.
        """
        # Prepare the prompt
        prompt = f"""
        Fix the following {database_type} query that contains errors.
        
        Query with errors:
        ```json
        {query}
        ```
        """
        
        if error_message:
            prompt += f"""
            Error message:
            {error_message}
            """
        
        if mapping:
            prompt += f"""
            Database mapping:
            ```json
            {self._format_mapping_for_prompt(mapping)}
            ```
            """
        
        prompt += f"""
        Return ONLY the fixed {database_type} query as a valid JSON object without any explanations or markdown formatting.
        """
        
        return self.generate_response(prompt, context={"database_type": database_type}, **kwargs)
    
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
            **kwargs: Additional arguments to pass to the OpenAI API.
            
        Returns:
            An LLMResponse object containing the improved database query.
        """
        # Prepare the prompt
        prompt = f"""
        Improve the following {database_type} query.
        
        Original query:
        ```json
        {query}
        ```
        """
        
        if improvement_goal:
            prompt += f"""
            Improvement goal: {improvement_goal}
            """
        else:
            prompt += """
            Improve the query for better performance, accuracy, and readability.
            """
        
        if mapping:
            prompt += f"""
            Database mapping:
            ```json
            {self._format_mapping_for_prompt(mapping)}
            ```
            """
        
        prompt += f"""
        Return ONLY the improved {database_type} query as a valid JSON object without any explanations or markdown formatting.
        """
        
        return self.generate_response(prompt, context={"database_type": database_type}, **kwargs)
