"""
Unit tests for the database module.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from nlq_translator.database import DatabaseInterface, ElasticsearchClient


class TestElasticsearchClient(unittest.TestCase):
    """Test cases for the ElasticsearchClient class."""

    @patch('nlq_translator.database.elasticsearch_client.Elasticsearch')
    def setUp(self, mock_elasticsearch):
        """Set up test environment before each test."""
        self.mock_elasticsearch = mock_elasticsearch
        self.mock_client = MagicMock()
        self.mock_elasticsearch.return_value = self.mock_client
        
        # Mock Elasticsearch.info() method
        self.mock_client.info.return_value = {"version": {"number": "7.10.0"}}
        
        # Create ElasticsearchClient instance
        self.es_client = ElasticsearchClient(
            hosts=["localhost:9200"],
            username="test_user",
            password="test_password",
            index="test_index"
        )

    def test_init(self):
        """Test initializing the ElasticsearchClient."""
        self.assertEqual(self.es_client.hosts, ["localhost:9200"])
        self.assertEqual(self.es_client.username, "test_user")
        self.assertEqual(self.es_client.password, "test_password")
        self.assertEqual(self.es_client.index, "test_index")
        self.assertIsNone(self.es_client.client)  # Client is initialized in connect()

    def test_connect(self):
        """Test connecting to Elasticsearch."""
        result = self.es_client.connect()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.es_client.client)
        self.mock_elasticsearch.assert_called_once()
        
        # Verify connection parameters
        call_kwargs = self.mock_elasticsearch.call_args[1]
        self.assertEqual(call_kwargs["hosts"], ["localhost:9200"])
        self.assertEqual(call_kwargs["basic_auth"], ("test_user", "test_password"))

    def test_connect_with_cloud_id(self):
        """Test connecting to Elasticsearch with cloud ID."""
        es_client = ElasticsearchClient(
            cloud_id="test_cloud_id",
            username="test_user",
            password="test_password"
        )
        result = es_client.connect()
        
        self.assertTrue(result)
        self.assertIsNotNone(es_client.client)
        self.mock_elasticsearch.assert_called()
        
        # Verify connection parameters
        call_kwargs = self.mock_elasticsearch.call_args[1]
        self.assertEqual(call_kwargs["cloud_id"], "test_cloud_id")
        self.assertEqual(call_kwargs["basic_auth"], ("test_user", "test_password"))

    def test_connect_with_api_key(self):
        """Test connecting to Elasticsearch with API key."""
        es_client = ElasticsearchClient(
            hosts=["localhost:9200"],
            api_key="test_api_key"
        )
        result = es_client.connect()
        
        self.assertTrue(result)
        self.assertIsNotNone(es_client.client)
        self.mock_elasticsearch.assert_called()
        
        # Verify connection parameters
        call_kwargs = self.mock_elasticsearch.call_args[1]
        self.assertEqual(call_kwargs["hosts"], ["localhost:9200"])
        self.assertEqual(call_kwargs["api_key"], "test_api_key")

    def test_connect_error(self):
        """Test handling connection errors."""
        # Mock Elasticsearch.info() to raise an exception
        self.mock_client.info.side_effect = Exception("Connection error")
        
        with self.assertRaises(Exception) as context:
            self.es_client.connect()
        
        self.assertIn("Error connecting to Elasticsearch", str(context.exception))
        self.assertIsNone(self.es_client.client)

    def test_disconnect(self):
        """Test disconnecting from Elasticsearch."""
        # First connect
        self.es_client.connect()
        self.assertIsNotNone(self.es_client.client)
        
        # Then disconnect
        result = self.es_client.disconnect()
        
        self.assertTrue(result)
        self.assertIsNone(self.es_client.client)
        self.mock_client.close.assert_called_once()

    def test_is_connected(self):
        """Test checking if connected to Elasticsearch."""
        # Not connected initially
        self.assertFalse(self.es_client.is_connected())
        
        # Connect
        self.es_client.connect()
        self.assertTrue(self.es_client.is_connected())
        
        # Test when info() raises an exception
        self.mock_client.info.side_effect = Exception("Connection lost")
        self.assertFalse(self.es_client.is_connected())

    def test_execute_query(self):
        """Test executing a query."""
        # Connect first
        self.es_client.connect()
        
        # Mock search response
        mock_response = {
            "took": 5,
            "hits": {
                "total": {"value": 1, "relation": "eq"},
                "hits": [{"_source": {"content": "test"}}]
            }
        }
        self.mock_client.search.return_value = mock_response
        
        # Execute query
        query = {"query": {"match": {"content": "test"}}}
        result = self.es_client.execute_query(query)
        
        self.assertEqual(result, mock_response)
        self.mock_client.search.assert_called_once_with(index="test_index", body=query)

    def test_execute_query_not_connected(self):
        """Test executing a query when not connected."""
        query = {"query": {"match": {"content": "test"}}}
        
        with self.assertRaises(Exception) as context:
            self.es_client.execute_query(query)
        
        self.assertIn("Not connected to Elasticsearch", str(context.exception))

    def test_execute_query_no_index(self):
        """Test executing a query with no index specified."""
        # Connect first
        self.es_client.connect()
        
        # Set index to None
        self.es_client.index = None
        
        query = {"query": {"match": {"content": "test"}}}
        
        with self.assertRaises(Exception) as context:
            self.es_client.execute_query(query)
        
        self.assertIn("No index specified", str(context.exception))

    def test_execute_query_string(self):
        """Test executing a query provided as a string."""
        # Connect first
        self.es_client.connect()
        
        # Mock search response
        mock_response = {
            "took": 5,
            "hits": {
                "total": {"value": 1, "relation": "eq"},
                "hits": [{"_source": {"content": "test"}}]
            }
        }
        self.mock_client.search.return_value = mock_response
        
        # Execute query as string
        query_str = '{"query": {"match": {"content": "test"}}}'
        result = self.es_client.execute_query(query_str)
        
        self.assertEqual(result, mock_response)
        self.mock_client.search.assert_called_once()
        
        # Verify the query was parsed correctly
        call_kwargs = self.mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["body"]["query"]["match"]["content"], "test")

    def test_get_mapping(self):
        """Test getting the mapping for an index."""
        # Connect first
        self.es_client.connect()
        
        # Mock get_mapping response
        mock_mapping = {
            "test_index": {
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "date": {"type": "date"}
                    }
                }
            }
        }
        self.mock_client.indices.get_mapping.return_value = mock_mapping
        
        # Get mapping
        result = self.es_client.get_mapping()
        
        self.assertEqual(result, mock_mapping)
        self.mock_client.indices.get_mapping.assert_called_once_with(index="test_index")

    def test_get_mapping_specific_index(self):
        """Test getting the mapping for a specific index."""
        # Connect first
        self.es_client.connect()
        
        # Mock get_mapping response
        mock_mapping = {
            "other_index": {
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "tags": {"type": "keyword"}
                    }
                }
            }
        }
        self.mock_client.indices.get_mapping.return_value = mock_mapping
        
        # Get mapping for specific index
        result = self.es_client.get_mapping("other_index")
        
        self.assertEqual(result, mock_mapping)
        self.mock_client.indices.get_mapping.assert_called_once_with(index="other_index")

    def test_get_mapping_not_connected(self):
        """Test getting mapping when not connected."""
        with self.assertRaises(Exception) as context:
            self.es_client.get_mapping()
        
        self.assertIn("Not connected to Elasticsearch", str(context.exception))

    def test_get_mapping_no_index(self):
        """Test getting mapping with no index specified."""
        # Connect first
        self.es_client.connect()
        
        # Set index to None
        self.es_client.index = None
        
        with self.assertRaises(Exception) as context:
            self.es_client.get_mapping()
        
        self.assertIn("No index specified", str(context.exception))

    def test_set_index(self):
        """Test setting the default index."""
        self.es_client.set_index("new_index")
        self.assertEqual(self.es_client.index, "new_index")

    def test_list_indices(self):
        """Test listing all indices."""
        # Connect first
        self.es_client.connect()
        
        # Mock get_alias response
        mock_indices = {
            "index1": {"aliases": {}},
            "index2": {"aliases": {}},
            "index3": {"aliases": {}}
        }
        self.mock_client.indices.get_alias.return_value = mock_indices
        
        # List indices
        result = self.es_client.list_indices()
        
        self.assertEqual(sorted(result), ["index1", "index2", "index3"])
        self.mock_client.indices.get_alias.assert_called_once_with(index="*")

    def test_list_indices_not_connected(self):
        """Test listing indices when not connected."""
        with self.assertRaises(Exception) as context:
            self.es_client.list_indices()
        
        self.assertIn("Not connected to Elasticsearch", str(context.exception))


if __name__ == "__main__":
    unittest.main()
