"""
Elasticsearch client for NLQ Translator.

This module provides an implementation of the database interface for Elasticsearch,
with support for cloud ID, username, and password authentication.
"""

import json
from typing import Dict, Any, Optional, List, Union, Tuple

try:
    from elasticsearch import Elasticsearch, NotFoundError, RequestError, AuthenticationException
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

from .database_interface import DatabaseInterface


class ElasticsearchClient(DatabaseInterface):
    """
    Elasticsearch implementation of the database interface.
    
    This class provides methods for connecting to and interacting with
    Elasticsearch databases, with support for cloud ID, username, and password.
    """
    
    def __init__(
        self,
        hosts: Optional[Union[str, List[str]]] = None,
        cloud_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[Union[str, Tuple[str, str]]] = None,
        index: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Elasticsearch client.
        
        Args:
            hosts: Optional host or list of hosts to connect to.
                If not provided, will use localhost:9200.
            cloud_id: Optional cloud ID for Elastic Cloud.
            username: Optional username for authentication.
            password: Optional password for authentication.
            api_key: Optional API key for authentication.
            index: Optional default index to use for queries.
            **kwargs: Additional arguments to pass to the Elasticsearch client.
            
        Raises:
            ImportError: If the elasticsearch package is not installed.
        """
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError(
                "The elasticsearch package is required to use ElasticsearchClient. "
                "Please install it with: pip install elasticsearch"
            )
        
        self.hosts = hosts or ["localhost:9200"]
        self.cloud_id = cloud_id
        self.username = username
        self.password = password
        self.api_key = api_key
        self.index = index
        self.kwargs = kwargs
        self.client = None
    
    def connect(self) -> bool:
        """
        Connect to the Elasticsearch database.
        
        Returns:
            A boolean indicating whether the connection was successful.
            
        Raises:
            Exception: If there is an error connecting to the database.
        """
        try:
            # Prepare connection parameters
            conn_params = {}
            
            # Add authentication if provided
            if self.cloud_id:
                conn_params["cloud_id"] = self.cloud_id
            else:
                conn_params["hosts"] = self.hosts
            
            if self.username and self.password:
                conn_params["basic_auth"] = (self.username, self.password)
            elif self.api_key:
                conn_params["api_key"] = self.api_key
            
            # Add additional parameters
            conn_params.update(self.kwargs)
            
            # Create the client
            self.client = Elasticsearch(**conn_params)
            
            # Test the connection
            info = self.client.info()
            return True
        except Exception as e:
            self.client = None
            raise Exception(f"Error connecting to Elasticsearch: {str(e)}")
    
    def disconnect(self) -> bool:
        """
        Disconnect from the Elasticsearch database.
        
        Returns:
            A boolean indicating whether the disconnection was successful.
        """
        if self.client:
            try:
                self.client.close()
                self.client = None
                return True
            except Exception:
                return False
        return True
    
    def is_connected(self) -> bool:
        """
        Check if the Elasticsearch database is connected.
        
        Returns:
            A boolean indicating whether the database is connected.
        """
        if self.client:
            try:
                self.client.info()
                return True
            except Exception:
                return False
        return False
    
    def execute_query(self, query: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a query against the Elasticsearch database.
        
        Args:
            query: The query to execute (string or dictionary).
            
        Returns:
            A dictionary containing the query results.
            
        Raises:
            Exception: If there is an error executing the query.
        """
        if not self.is_connected():
            raise Exception("Not connected to Elasticsearch")
        
        if not self.index:
            raise Exception("No index specified")
        
        # Convert query to dictionary if it's a string
        if isinstance(query, str):
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON query: {str(e)}")
        else:
            query_dict = query
        
        try:
            # Execute the search
            response = self.client.search(index=self.index, body=query_dict)
            return response
        except RequestError as e:
            raise Exception(f"Error executing Elasticsearch query: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error executing Elasticsearch query: {str(e)}")
    
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
        if not self.is_connected():
            raise Exception("Not connected to Elasticsearch")
        
        index_name = index or self.index
        if not index_name:
            raise Exception("No index specified")
        
        try:
            mapping = self.client.indices.get_mapping(index=index_name)
            return mapping
        except NotFoundError:
            raise Exception(f"Index '{index_name}' not found")
        except Exception as e:
            raise Exception(f"Error getting mapping for index '{index_name}': {str(e)}")
    
    def set_index(self, index: str) -> None:
        """
        Set the default index to use for queries.
        
        Args:
            index: The name of the index to use.
        """
        self.index = index
    
    def list_indices(self) -> List[str]:
        """
        List all indices in the Elasticsearch database.
        
        Returns:
            A list of index names.
            
        Raises:
            Exception: If there is an error listing indices.
        """
        if not self.is_connected():
            raise Exception("Not connected to Elasticsearch")
        
        try:
            indices = self.client.indices.get_alias(index="*")
            return list(indices.keys())
        except Exception as e:
            raise Exception(f"Error listing indices: {str(e)}")
