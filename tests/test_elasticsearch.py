"""
Unit tests for the Elasticsearch module.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from nlq_translator.elasticsearch import ElasticsearchQueryGenerator, ElasticsearchQueryValidator
from nlq_translator.llm import LLMInterface, LLMResponse


class MockLLM(LLMInterface):
    """Mock LLM implementation for testing."""
    
    def __init__(self, response_content):
        self.response_content = response_content
        self.last_prompt = None
        self.last_context = None
    
    def generate_response(self, prompt, context=None, **kwargs):
        self.last_prompt = prompt
        self.last_context = context
        return LLMResponse(content=self.response_content, raw_response=None)
    
    def translate_to_query(self, natural_language, database_type, mapping=None, **kwargs):
        self.last_prompt = f"Translate: {natural_language}"
        self.last_context = {"database_type": database_type, "mapping": mapping}
        return LLMResponse(content=self.response_content, raw_response=None)
    
    def fix_query(self, query, database_type, error_message=None, mapping=None, **kwargs):
        self.last_prompt = f"Fix: {query}"
        self.last_context = {"database_type": database_type, "error": error_message, "mapping": mapping}
        return LLMResponse(content=self.response_content, raw_response=None)
    
    def improve_query(self, query, database_type, improvement_goal=None, mapping=None, **kwargs):
        self.last_prompt = f"Improve: {query}"
        self.last_context = {"database_type": database_type, "goal": improvement_goal, "mapping": mapping}
        return LLMResponse(content=self.response_content, raw_response=None)


class TestElasticsearchQueryGenerator(unittest.TestCase):
    """Test cases for the ElasticsearchQueryGenerator class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.valid_query = {
            "query": {
                "match": {
                    "content": "test"
                }
            }
        }
        self.valid_query_str = json.dumps(self.valid_query)
        self.mock_llm = MockLLM(self.valid_query_str)
        self.query_generator = ElasticsearchQueryGenerator(self.mock_llm)

    def test_generate_query(self):
        """Test generating a query from natural language."""
        query = self.query_generator.generate_query(
            natural_language="Find documents about test",
            mapping={"properties": {"content": {"type": "text"}}}
        )
        
        self.assertEqual(query, self.valid_query)
        self.assertEqual(self.mock_llm.last_context["database_type"], "elasticsearch")

    def test_generate_query_with_json_response(self):
        """Test generating a query when LLM returns a JSON string."""
        query = self.query_generator.generate_query("Find documents about test")
        self.assertEqual(query, self.valid_query)

    def test_generate_query_with_markdown_response(self):
        """Test generating a query when LLM returns markdown with JSON."""
        markdown_llm = MockLLM(f"```json\n{self.valid_query_str}\n```")
        generator = ElasticsearchQueryGenerator(markdown_llm)
        query = generator.generate_query("Find documents about test")
        self.assertEqual(query, self.valid_query)

    def test_fix_query(self):
        """Test fixing a query."""
        invalid_query = {"query": {"match_invalid": "test"}}
        fixed_query = self.query_generator.fix_query(
            query=invalid_query,
            error_message="Invalid query structure",
            mapping={"properties": {"content": {"type": "text"}}}
        )
        
        self.assertEqual(fixed_query, self.valid_query)
        self.assertEqual(self.mock_llm.last_context["database_type"], "elasticsearch")
        self.assertIn("Invalid query structure", self.mock_llm.last_context["error"])

    def test_improve_query(self):
        """Test improving a query."""
        improved_query = self.query_generator.improve_query(
            query=self.valid_query,
            improvement_goal="Add bool query for better structure",
            mapping={"properties": {"content": {"type": "text"}}}
        )
        
        self.assertEqual(improved_query, self.valid_query)  # In this test, the mock returns the same query
        self.assertEqual(self.mock_llm.last_context["database_type"], "elasticsearch")
        self.assertEqual(self.mock_llm.last_context["goal"], "Add bool query for better structure")


class TestElasticsearchQueryValidator(unittest.TestCase):
    """Test cases for the ElasticsearchQueryValidator class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.mapping = {
            "properties": {
                "content": {"type": "text"},
                "title": {"type": "text"},
                "date": {"type": "date"},
                "nested_field": {
                    "type": "nested",
                    "properties": {
                        "nested_content": {"type": "text"}
                    }
                }
            }
        }
        self.validator = ElasticsearchQueryValidator(self.mapping)

    def test_validate_valid_query(self):
        """Test validating a valid query."""
        valid_query = {
            "query": {
                "match": {
                    "content": "test"
                }
            }
        }
        
        is_valid, error = self.validator.validate(valid_query)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_invalid_json(self):
        """Test validating an invalid JSON string."""
        invalid_json = "{invalid json"
        
        is_valid, error = self.validator.validate(invalid_json)
        self.assertFalse(is_valid)
        self.assertIn("Invalid JSON", error)

    def test_validate_invalid_query_structure(self):
        """Test validating a query with invalid structure."""
        invalid_query = {
            "query": "not an object"
        }
        
        is_valid, error = self.validator.validate(invalid_query)
        self.assertFalse(is_valid)
        self.assertIn("'query' must be a JSON object", error)

    def test_validate_unknown_query_type(self):
        """Test validating a query with unknown query type."""
        invalid_query = {
            "query": {
                "unknown_type": {
                    "content": "test"
                }
            }
        }
        
        is_valid, error = self.validator.validate(invalid_query)
        self.assertFalse(is_valid)
        self.assertIn("Unknown query type", error)

    def test_validate_against_mapping(self):
        """Test validating a query against a mapping."""
        # Valid query with fields from mapping
        valid_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"content": "test"}},
                        {"match": {"title": "test"}}
                    ],
                    "filter": [
                        {"range": {"date": {"gte": "2020-01-01"}}}
                    ]
                }
            }
        }
        
        is_valid, error = self.validator.validate(valid_query)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Invalid query with fields not in mapping
        invalid_query = {
            "query": {
                "match": {
                    "unknown_field": "test"
                }
            }
        }
        
        is_valid, error = self.validator.validate(invalid_query)
        self.assertFalse(is_valid)
        self.assertIn("Unknown fields in query", error)

    def test_validate_nested_query(self):
        """Test validating a nested query."""
        nested_query = {
            "query": {
                "nested": {
                    "path": "nested_field",
                    "query": {
                        "match": {
                            "nested_field.nested_content": "test"
                        }
                    }
                }
            }
        }
        
        is_valid, error = self.validator.validate(nested_query)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Invalid nested query missing path
        invalid_nested_query = {
            "query": {
                "nested": {
                    "query": {
                        "match": {
                            "nested_field.nested_content": "test"
                        }
                    }
                }
            }
        }
        
        is_valid, error = self.validator.validate(invalid_nested_query)
        self.assertFalse(is_valid)
        self.assertIn("'nested' query must have a 'path' field", error)


if __name__ == "__main__":
    unittest.main()
