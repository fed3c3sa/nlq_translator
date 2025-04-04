"""
Unit tests for the LLM module.
"""

import unittest
from unittest.mock import MagicMock, patch

from nlq_translator.llm import LLMInterface, LLMResponse, OpenAILLM
from nlq_translator.config import APIKeyManager


class TestLLMResponse(unittest.TestCase):
    """Test cases for the LLMResponse class."""

    def test_llm_response_init(self):
        """Test initializing an LLMResponse object."""
        response = LLMResponse(
            content="Test content",
            raw_response={"choices": [{"message": {"content": "Test content"}}]},
            usage={"total_tokens": 100},
            model="gpt-4"
        )
        
        self.assertEqual(response.content, "Test content")
        self.assertEqual(response.usage["total_tokens"], 100)
        self.assertEqual(response.model, "gpt-4")


class MockOpenAIResponse:
    """Mock OpenAI response for testing."""
    
    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content
        self.usage = MagicMock()
        self.usage.prompt_tokens = 50
        self.usage.completion_tokens = 50
        self.usage.total_tokens = 100
        self.model = "gpt-4"


class TestOpenAILLM(unittest.TestCase):
    """Test cases for the OpenAILLM class."""

    @patch('nlq_translator.llm.openai_llm.OpenAI')
    def setUp(self, mock_openai):
        """Set up test environment before each test."""
        self.mock_openai = mock_openai
        self.mock_client = MagicMock()
        self.mock_openai.return_value = self.mock_client
        
        # Mock API key manager
        self.api_key_manager = MagicMock(spec=APIKeyManager)
        self.api_key_manager.get_api_key.return_value = "test_api_key"
        
        self.llm = OpenAILLM(api_key="test_api_key")

    def test_init_with_api_key(self):
        """Test initializing with an API key."""
        self.assertEqual(self.llm.api_key, "test_api_key")
        self.assertEqual(self.llm.model, "gpt-4")
        self.assertEqual(self.llm.temperature, 0.1)
        self.assertEqual(self.llm.max_tokens, 2000)

    @patch('nlq_translator.llm.openai_llm.OpenAI')
    def test_init_with_api_key_manager(self, mock_openai):
        """Test initializing with an API key manager."""
        mock_openai.return_value = self.mock_client
        
        llm = OpenAILLM(api_key_manager=self.api_key_manager)
        self.assertEqual(llm.api_key, "test_api_key")

    @patch('nlq_translator.llm.openai_llm.OpenAI')
    def test_init_with_no_api_key(self, mock_openai):
        """Test initializing with no API key raises an error."""
        mock_openai.return_value = self.mock_client
        
        # Mock API key manager that returns None
        api_key_manager = MagicMock(spec=APIKeyManager)
        api_key_manager.get_api_key.return_value = None
        
        with self.assertRaises(ValueError):
            OpenAILLM(api_key_manager=api_key_manager)

    def test_generate_response(self):
        """Test generating a response."""
        # Mock the OpenAI client's chat.completions.create method
        mock_response = MockOpenAIResponse("Generated response")
        self.mock_client.chat.completions.create.return_value = mock_response
        
        response = self.llm.generate_response("Test prompt")
        
        self.assertEqual(response.content, "Generated response")
        self.assertEqual(response.usage["total_tokens"], 100)
        self.assertEqual(response.model, "gpt-4")
        
        # Verify the OpenAI client was called with the correct arguments
        self.mock_client.chat.completions.create.assert_called_once()
        call_args = self.mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4")
        self.assertEqual(call_args["temperature"], 0.1)
        self.assertEqual(call_args["max_tokens"], 2000)
        self.assertEqual(call_args["messages"][0]["role"], "user")
        self.assertEqual(call_args["messages"][0]["content"], "Test prompt")

    def test_translate_to_query(self):
        """Test translating natural language to a query."""
        # Mock the generate_response method
        self.llm.generate_response = MagicMock(return_value=LLMResponse(
            content='{"query": {"match": {"content": "test"}}}',
            raw_response=None
        ))
        
        response = self.llm.translate_to_query(
            natural_language="Find documents about test",
            database_type="elasticsearch",
            mapping={"properties": {"content": {"type": "text"}}}
        )
        
        self.assertEqual(response.content, '{"query": {"match": {"content": "test"}}}')
        
        # Verify generate_response was called with the correct arguments
        self.llm.generate_response.assert_called_once()
        call_args = self.llm.generate_response.call_args
        self.assertIn("Translate the following natural language query", call_args[0][0])
        self.assertIn("Find documents about test", call_args[0][0])
        self.assertIn("elasticsearch", call_args[0][0])
        self.assertEqual(call_args[1]["context"], {"database_type": "elasticsearch"})

    def test_fix_query(self):
        """Test fixing a query."""
        # Mock the generate_response method
        self.llm.generate_response = MagicMock(return_value=LLMResponse(
            content='{"query": {"match": {"content": "test"}}}',
            raw_response=None
        ))
        
        response = self.llm.fix_query(
            query='{"query": {"match_invalid": "test"}}',
            database_type="elasticsearch",
            error_message="Invalid query structure"
        )
        
        self.assertEqual(response.content, '{"query": {"match": {"content": "test"}}}')
        
        # Verify generate_response was called with the correct arguments
        self.llm.generate_response.assert_called_once()
        call_args = self.llm.generate_response.call_args
        self.assertIn("Fix the following elasticsearch query", call_args[0][0])
        self.assertIn("Invalid query structure", call_args[0][0])
        self.assertEqual(call_args[1]["context"], {"database_type": "elasticsearch"})

    def test_improve_query(self):
        """Test improving a query."""
        # Mock the generate_response method
        self.llm.generate_response = MagicMock(return_value=LLMResponse(
            content='{"query": {"bool": {"must": [{"match": {"content": "test"}}]}}}',
            raw_response=None
        ))
        
        response = self.llm.improve_query(
            query='{"query": {"match": {"content": "test"}}}',
            database_type="elasticsearch",
            improvement_goal="Add bool query for better structure"
        )
        
        self.assertEqual(
            response.content,
            '{"query": {"bool": {"must": [{"match": {"content": "test"}}]}}}'
        )
        
        # Verify generate_response was called with the correct arguments
        self.llm.generate_response.assert_called_once()
        call_args = self.llm.generate_response.call_args
        self.assertIn("Improve the following elasticsearch query", call_args[0][0])
        self.assertIn("Add bool query for better structure", call_args[0][0])
        self.assertEqual(call_args[1]["context"], {"database_type": "elasticsearch"})


if __name__ == "__main__":
    unittest.main()
