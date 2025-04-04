"""
Core translator for NLQ Translator.

This module provides the main NLQueryTranslator class which integrates all components
of the library to translate natural language queries into database queries.
"""

import json
from typing import Dict, Any, Optional, List, Union, Tuple, Type

from ..config import APIKeyManager, ConfigManager
from ..llm import LLMInterface, OpenAILLM, LLMResponse
from ..elasticsearch import ElasticsearchQueryGenerator, ElasticsearchQueryValidator
from ..database import DatabaseInterface, ElasticsearchClient
from ..export import QueryExporter, ExportFormat
from ..utils import format_query, parse_query_string


class NLQueryTranslator:
    """
    Main translator class for converting natural language to database queries.
    
    This class integrates all components of the NLQ Translator library to provide
    a unified interface for translating, validating, fixing, and improving queries.
    """
    
    def __init__(
        self,
        llm: Optional[LLMInterface] = None,
        database_client: Optional[DatabaseInterface] = None,
        config_manager: Optional[ConfigManager] = None,
        api_key_manager: Optional[APIKeyManager] = None
    ):
        """
        Initialize the NLQueryTranslator.
        
        Args:
            llm: Optional language model interface to use for translation.
                If not provided, will use OpenAILLM with default settings.
            database_client: Optional database client to use for executing queries.
                If not provided, no database client will be used.
            config_manager: Optional configuration manager to use.
                If not provided, a new ConfigManager will be created.
            api_key_manager: Optional API key manager to use.
                If not provided, a new APIKeyManager will be created with the config_manager.
        """
        self.config_manager = config_manager or ConfigManager()
        self.api_key_manager = api_key_manager or APIKeyManager(self.config_manager)
        
        # Initialize LLM
        self.llm = llm or OpenAILLM(api_key_manager=self.api_key_manager)
        
        # Initialize database client
        self.database_client = database_client
        
        # Initialize query generator and validator
        self.query_generator = ElasticsearchQueryGenerator(self.llm)
        self.query_validator = ElasticsearchQueryValidator()
        
        # Initialize query exporter
        self.query_exporter = QueryExporter()
    
    def set_llm(
        self, 
        llm: Union[LLMInterface, str],
        **kwargs
    ) -> None:
        """
        Set the language model to use for translation.
        
        Args:
            llm: The language model interface to use, or a string name of a built-in model.
                Supported built-in models: 'openai'.
            **kwargs: Additional arguments to pass to the language model constructor.
            
        Raises:
            ValueError: If the specified built-in model is not supported.
        """
        if isinstance(llm, str):
            if llm.lower() == 'openai':
                self.llm = OpenAILLM(api_key_manager=self.api_key_manager, **kwargs)
            else:
                raise ValueError(f"Unsupported built-in language model: {llm}")
        else:
            self.llm = llm
        
        # Update the query generator with the new LLM
        self.query_generator = ElasticsearchQueryGenerator(self.llm)
    
    def set_database_client(
        self, 
        database_client: Union[DatabaseInterface, str],
        **kwargs
    ) -> None:
        """
        Set the database client to use for executing queries.
        
        Args:
            database_client: The database client to use, or a string name of a built-in client.
                Supported built-in clients: 'elasticsearch'.
            **kwargs: Additional arguments to pass to the database client constructor.
            
        Raises:
            ValueError: If the specified built-in client is not supported.
        """
        if isinstance(database_client, str):
            if database_client.lower() == 'elasticsearch':
                self.database_client = ElasticsearchClient(**kwargs)
            else:
                raise ValueError(f"Unsupported built-in database client: {database_client}")
        else:
            self.database_client = database_client
    
    def connect_to_database(self) -> bool:
        """
        Connect to the database using the current database client.
        
        Returns:
            A boolean indicating whether the connection was successful.
            
        Raises:
            ValueError: If no database client is set.
        """
        if not self.database_client:
            raise ValueError("No database client set")
        
        return self.database_client.connect()
    
    def disconnect_from_database(self) -> bool:
        """
        Disconnect from the database using the current database client.
        
        Returns:
            A boolean indicating whether the disconnection was successful.
            
        Raises:
            ValueError: If no database client is set.
        """
        if not self.database_client:
            raise ValueError("No database client set")
        
        return self.database_client.disconnect()
    
    def is_connected_to_database(self) -> bool:
        """
        Check if connected to the database using the current database client.
        
        Returns:
            A boolean indicating whether connected to the database.
            
        Raises:
            ValueError: If no database client is set.
        """
        if not self.database_client:
            raise ValueError("No database client set")
        
        return self.database_client.is_connected()
    
    def translate(
        self, 
        natural_language: str,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Translate a natural language query to a database query.
        
        Args:
            natural_language: The natural language query to translate.
            mapping: Optional mapping information for the database.
                If not provided and a database client is set and connected,
                will attempt to get the mapping from the database.
            **kwargs: Additional arguments to pass to the query generator.
            
        Returns:
            A dictionary representing the translated database query.
            
        Raises:
            Exception: If there is an error translating the query.
        """
        # Get mapping from database if not provided and database client is set
        if mapping is None and self.database_client and self.database_client.is_connected():
            try:
                mapping = self.database_client.get_mapping()
            except Exception:
                # If getting mapping fails, continue without it
                pass
        
        return self.query_generator.generate_query(natural_language, mapping, **kwargs)
    
    def validate(
        self, 
        query: Union[str, Dict[str, Any]],
        mapping: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a database query.
        
        Args:
            query: The database query to validate (string or dictionary).
            mapping: Optional mapping information for the database.
                If not provided and a database client is set and connected,
                will attempt to get the mapping from the database.
            
        Returns:
            A tuple containing:
                - A boolean indicating whether the query is valid.
                - An error message if the query is invalid, or None if it's valid.
        """
        # Get mapping from database if not provided and database client is set
        if mapping is None and self.database_client and self.database_client.is_connected():
            try:
                mapping = self.database_client.get_mapping()
                self.query_validator = ElasticsearchQueryValidator(mapping)
            except Exception:
                # If getting mapping fails, continue without it
                pass
        elif mapping is not None:
            self.query_validator = ElasticsearchQueryValidator(mapping)
        
        return self.query_validator.validate(query)
    
    def fix(
        self, 
        query: Union[str, Dict[str, Any]],
        error_message: Optional[str] = None,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fix errors in a database query.
        
        Args:
            query: The database query to fix (string or dictionary).
            error_message: Optional error message to help guide the fix.
                If not provided and the query is invalid, will use the validation error.
            mapping: Optional mapping information for the database.
                If not provided and a database client is set and connected,
                will attempt to get the mapping from the database.
            **kwargs: Additional arguments to pass to the query generator.
            
        Returns:
            A dictionary representing the fixed database query.
            
        Raises:
            Exception: If there is an error fixing the query.
        """
        # Get mapping from database if not provided and database client is set
        if mapping is None and self.database_client and self.database_client.is_connected():
            try:
                mapping = self.database_client.get_mapping()
            except Exception:
                # If getting mapping fails, continue without it
                pass
        
        # Validate the query to get an error message if not provided
        if error_message is None:
            is_valid, validation_error = self.validate(query, mapping)
            if not is_valid and validation_error:
                error_message = validation_error
        
        return self.query_generator.fix_query(query, error_message, mapping, **kwargs)
    
    def improve(
        self, 
        query: Union[str, Dict[str, Any]],
        improvement_goal: Optional[str] = None,
        mapping: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Improve a database query for better performance or results.
        
        Args:
            query: The database query to improve (string or dictionary).
            improvement_goal: Optional description of the improvement goal.
            mapping: Optional mapping information for the database.
                If not provided and a database client is set and connected,
                will attempt to get the mapping from the database.
            **kwargs: Additional arguments to pass to the query generator.
            
        Returns:
            A dictionary representing the improved database query.
            
        Raises:
            Exception: If there is an error improving the query.
        """
        # Get mapping from database if not provided and database client is set
        if mapping is None and self.database_client and self.database_client.is_connected():
            try:
                mapping = self.database_client.get_mapping()
            except Exception:
                # If getting mapping fails, continue without it
                pass
        
        return self.query_generator.improve_query(query, improvement_goal, mapping, **kwargs)
    
    def execute(
        self, 
        query: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a database query using the current database client.
        
        Args:
            query: The database query to execute (string or dictionary).
            
        Returns:
            A dictionary containing the query results.
            
        Raises:
            ValueError: If no database client is set or not connected.
            Exception: If there is an error executing the query.
        """
        if not self.database_client:
            raise ValueError("No database client set")
        
        if not self.database_client.is_connected():
            raise ValueError("Not connected to database")
        
        return self.database_client.execute_query(query)
    
    def export(
        self, 
        query: Union[str, Dict[str, Any]],
        format: Union[ExportFormat, str] = ExportFormat.JSON,
        file_path: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """
        Export a database query to the specified format.
        
        Args:
            query: The database query to export (string or dictionary).
            format: The format to export to (ExportFormat.JSON, ExportFormat.TEXT, or string name).
            file_path: Optional path to save the exported query to.
            pretty: Whether to format the output for readability (default: True).
            
        Returns:
            The exported query as a string.
            
        Raises:
            ValueError: If the query is not valid or the format is not supported.
            IOError: If there is an error writing to the file.
        """
        # Set pretty print option
        self.query_exporter.pretty_print = pretty
        
        # Convert string format to enum
        if isinstance(format, str):
            format_str = format.upper()
            if format_str == 'JSON':
                format = ExportFormat.JSON
            elif format_str == 'TEXT':
                format = ExportFormat.TEXT
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        return self.query_exporter.export(query, format, file_path)
