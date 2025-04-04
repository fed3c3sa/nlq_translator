"""
Unit tests for the core module.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from nlq_translator.core import NLQueryTranslator
from nlq_translator.config import ConfigManager, APIKeyManager
from nlq_translator.llm import LLMInterface, OpenAILLM
from nlq_translator.database import DatabaseInterface, ElasticsearchClient
from nlq_translator.elasticsearch import ElasticsearchQueryGenerator, ElasticsearchQueryValidator
from nlq_translator.export import QueryExporter, ExportFormat


class TestNLQueryTranslator(unittest.TestCase):
    """Test cases for the NLQueryTranslator class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Mock dependencies
        self.mock_llm = MagicMock(spec=LLMInterface)
        self.mock_database_client = MagicMock(spec=DatabaseInterface)
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_api_key_manager = MagicMock(spec=APIKeyManager)
        
        # Sample query and mapping
        self.sample_query = {"query": {"match": {"content": "test"}}}
        self.sample_mapping = {
            "properties": {
                "content": {"type": "text"},
                "title": {"type": "text"}
            }
        }
        
        # Configure mocks
        self.mock_llm.translate_to_query.return_value = MagicMock(
            content=json.dumps(self.sample_query)
        )
        self.mock_database_client.is_connected.return_value = True
        self.mock_database_client.get_mapping.return_value = self.sample_mapping
        
        # Create translator instance
        self.translator = NLQueryTranslator(
            llm=self.mock_llm,
            database_client=self.mock_database_client,
            config_manager=self.mock_config_manager,
            api_key_manager=self.mock_api_key_manager
        )

    def test_init(self):
        """Test initializing the NLQueryTranslator."""
        self.assertEqual(self.translator.llm, self.mock_llm)
        self.assertEqual(self.translator.database_client, self.mock_database_client)
        self.assertEqual(self.translator.config_manager, self.mock_config_manager)
        self.assertEqual(self.translator.api_key_manager, self.mock_api_key_manager)
        self.assertIsInstance(self.translator.query_generator, ElasticsearchQueryGenerator)
        self.assertIsInstance(self.translator.query_validator, ElasticsearchQueryValidator)
        self.assertIsInstance(self.translator.query_exporter, QueryExporter)

    def test_init_with_defaults(self):
        """Test initializing with default values."""
        with patch('nlq_translator.core.translator.OpenAILLM') as mock_openai_llm:
            translator = NLQueryTranslator()
            self.assertIsInstance(translator.config_manager, ConfigManager)
            self.assertIsInstance(translator.api_key_manager, APIKeyManager)
            mock_openai_llm.assert_called_once()
            self.assertIsNone(translator.database_client)

    def test_set_llm(self):
        """Test setting the language model."""
        new_mock_llm = MagicMock(spec=LLMInterface)
        self.translator.set_llm(new_mock_llm)
        self.assertEqual(self.translator.llm, new_mock_llm)
        
        # Test with string name
        with patch('nlq_translator.core.translator.OpenAILLM') as mock_openai_llm:
            self.translator.set_llm("openai", model="gpt-4")
            mock_openai_llm.assert_called_once_with(
                api_key_manager=self.mock_api_key_manager, 
                model="gpt-4"
            )
        
        # Test with invalid string name
        with self.assertRaises(ValueError):
            self.translator.set_llm("invalid_llm")

    def test_set_database_client(self):
        """Test setting the database client."""
        new_mock_client = MagicMock(spec=DatabaseInterface)
        self.translator.set_database_client(new_mock_client)
        self.assertEqual(self.translator.database_client, new_mock_client)
        
        # Test with string name
        with patch('nlq_translator.core.translator.ElasticsearchClient') as mock_es_client:
            self.translator.set_database_client("elasticsearch", hosts=["localhost:9200"])
            mock_es_client.assert_called_once_with(hosts=["localhost:9200"])
        
        # Test with invalid string name
        with self.assertRaises(ValueError):
            self.translator.set_database_client("invalid_client")

    def test_connect_to_database(self):
        """Test connecting to the database."""
        self.mock_database_client.connect.return_value = True
        result = self.translator.connect_to_database()
        self.assertTrue(result)
        self.mock_database_client.connect.assert_called_once()
        
        # Test with no database client
        self.translator.database_client = None
        with self.assertRaises(ValueError):
            self.translator.connect_to_database()

    def test_disconnect_from_database(self):
        """Test disconnecting from the database."""
        self.mock_database_client.disconnect.return_value = True
        result = self.translator.disconnect_from_database()
        self.assertTrue(result)
        self.mock_database_client.disconnect.assert_called_once()
        
        # Test with no database client
        self.translator.database_client = None
        with self.assertRaises(ValueError):
            self.translator.disconnect_from_database()

    def test_is_connected_to_database(self):
        """Test checking if connected to the database."""
        self.mock_database_client.is_connected.return_value = True
        result = self.translator.is_connected_to_database()
        self.assertTrue(result)
        self.mock_database_client.is_connected.assert_called_once()
        
        # Test with no database client
        self.translator.database_client = None
        with self.assertRaises(ValueError):
            self.translator.is_connected_to_database()

    def test_translate(self):
        """Test translating natural language to a query."""
        # Patch the query generator
        self.translator.query_generator.generate_query = MagicMock(
            return_value=self.sample_query
        )
        
        result = self.translator.translate(
            natural_language="Find documents about test",
            mapping=self.sample_mapping
        )
        
        self.assertEqual(result, self.sample_query)
        self.translator.query_generator.generate_query.assert_called_once_with(
            "Find documents about test", 
            self.sample_mapping
        )
        
        # Test with no mapping provided but database client available
        self.translator.query_generator.generate_query.reset_mock()
        result = self.translator.translate("Find documents about test")
        
        self.assertEqual(result, self.sample_query)
        self.translator.query_generator.generate_query.assert_called_once_with(
            "Find documents about test", 
            self.sample_mapping
        )
        self.mock_database_client.get_mapping.assert_called_once()

    def test_validate(self):
        """Test validating a query."""
        # Patch the query validator
        self.translator.query_validator.validate = MagicMock(
            return_value=(True, None)
        )
        
        is_valid, error = self.translator.validate(
            query=self.sample_query,
            mapping=self.sample_mapping
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Test with invalid query
        self.translator.query_validator.validate = MagicMock(
            return_value=(False, "Invalid query structure")
        )
        
        is_valid, error = self.translator.validate(self.sample_query)
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Invalid query structure")

    def test_fix(self):
        """Test fixing a query."""
        # Patch the query generator
        self.translator.query_generator.fix_query = MagicMock(
            return_value=self.sample_query
        )
        
        result = self.translator.fix(
            query={"query": {"invalid": "structure"}},
            error_message="Invalid query structure",
            mapping=self.sample_mapping
        )
        
        self.assertEqual(result, self.sample_query)
        self.translator.query_generator.fix_query.assert_called_once_with(
            {"query": {"invalid": "structure"}},
            "Invalid query structure",
            self.sample_mapping
        )
        
        # Test with no error message but validation error
        self.translator.query_validator.validate = MagicMock(
            return_value=(False, "Validation error")
        )
        self.translator.query_generator.fix_query.reset_mock()
        
        result = self.translator.fix(
            query={"query": {"invalid": "structure"}},
            mapping=self.sample_mapping
        )
        
        self.assertEqual(result, self.sample_query)
        self.translator.query_generator.fix_query.assert_called_once_with(
            {"query": {"invalid": "structure"}},
            "Validation error",
            self.sample_mapping
        )

    def test_improve(self):
        """Test improving a query."""
        # Patch the query generator
        improved_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"content": "test"}}
                    ]
                }
            }
        }
        self.translator.query_generator.improve_query = MagicMock(
            return_value=improved_query
        )
        
        result = self.translator.improve(
            query=self.sample_query,
            improvement_goal="Add bool query for better structure",
            mapping=self.sample_mapping
        )
        
        self.assertEqual(result, improved_query)
        self.translator.query_generator.improve_query.assert_called_once_with(
            self.sample_query,
            "Add bool query for better structure",
            self.sample_mapping
        )

    def test_execute(self):
        """Test executing a query."""
        # Mock database client response
        mock_response = {
            "took": 5,
            "hits": {
                "total": {"value": 1, "relation": "eq"},
                "hits": [{"_source": {"content": "test"}}]
            }
        }
        self.mock_database_client.execute_query.return_value = mock_response
        
        result = self.translator.execute(self.sample_query)
        
        self.assertEqual(result, mock_response)
        self.mock_database_client.execute_query.assert_called_once_with(self.sample_query)
        
        # Test with no database client
        self.translator.database_client = None
        with self.assertRaises(ValueError):
            self.translator.execute(self.sample_query)
        
        # Test with database client not connected
        self.translator.database_client = self.mock_database_client
        self.mock_database_client.is_connected.return_value = False
        with self.assertRaises(ValueError):
            self.translator.execute(self.sample_query)

    def test_export(self):
        """Test exporting a query."""
        # Patch the query exporter
        self.translator.query_exporter.export = MagicMock(
            return_value=json.dumps(self.sample_query, indent=2)
        )
        
        result = self.translator.export(
            query=self.sample_query,
            format=ExportFormat.JSON,
            file_path="/path/to/file.json",
            pretty=True
        )
        
        self.assertEqual(result, json.dumps(self.sample_query, indent=2))
        self.translator.query_exporter.export.assert_called_once_with(
            self.sample_query,
            ExportFormat.JSON,
            "/path/to/file.json"
        )
        self.assertTrue(self.translator.query_exporter.pretty_print)
        
        # Test with string format
        self.translator.query_exporter.export.reset_mock()
        self.translator.query_exporter.pretty_print = False
        
        result = self.translator.export(
            query=self.sample_query,
            format="json",
            pretty=True
        )
        
        self.assertEqual(result, json.dumps(self.sample_query, indent=2))
        self.translator.query_exporter.export.assert_called_once()
        self.assertTrue(self.translator.query_exporter.pretty_print)
        
        # Test with invalid format
        with self.assertRaises(ValueError):
            self.translator.export(self.sample_query, format="invalid_format")


if __name__ == "__main__":
    unittest.main()
