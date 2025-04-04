"""
Database interface for NLQ Translator.

This module defines the interface for database connections used in the NLQ Translator.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union


class DatabaseInterface(ABC):
    """
    Abstract base class for database interfaces.
    
    This class defines the interface that all database implementations
    must follow to be used with the NLQ Translator.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            A boolean indicating whether the connection was successful.
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the database.
        
        Returns:
            A boolean indicating whether the disconnection was successful.
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the database is connected.
        
        Returns:
            A boolean indicating whether the database is connected.
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a query against the database.
        
        Args:
            query: The query to execute (string or dictionary).
            
        Returns:
            A dictionary containing the query results.
            
        Raises:
            Exception: If there is an error executing the query.
        """
        pass
    
    @abstractmethod
    def get_mapping(self, index: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the mapping for the specified index or the current index.
        
        Args:
            index: Optional name of the index to get the mapping for.
                If not provided, will use the current index.
                
        Returns:
            A dictionary containing the mapping information.
            
        Raises:
            Exception: If there is an error getting the mapping.
        """
        pass
