"""
Unit tests for the config module.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nlq_translator.config import ConfigManager, APIKeyManager


class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.config_manager = ConfigManager(self.config_path)

    def tearDown(self):
        """Clean up test environment after each test."""
        self.temp_dir.cleanup()

    def test_set_get_config(self):
        """Test setting and getting configuration values."""
        self.config_manager.set("test_key", "test_value")
        self.assertEqual(self.config_manager.get("test_key"), "test_value")

    def test_save_load_config(self):
        """Test saving and loading configuration values."""
        self.config_manager.set("test_key", "test_value")
        self.config_manager.save_config()
        
        # Create a new config manager to load the saved config
        new_config_manager = ConfigManager(self.config_path)
        self.assertEqual(new_config_manager.get("test_key"), "test_value")

    def test_delete_config(self):
        """Test deleting configuration values."""
        self.config_manager.set("test_key", "test_value")
        self.config_manager.delete("test_key")
        self.assertIsNone(self.config_manager.get("test_key"))

    def test_get_all_config(self):
        """Test getting all configuration values."""
        self.config_manager.set("key1", "value1")
        self.config_manager.set("key2", "value2")
        all_config = self.config_manager.get_all()
        self.assertEqual(all_config["key1"], "value1")
        self.assertEqual(all_config["key2"], "value2")

    @patch.dict(os.environ, {"NLQ_TRANSLATOR_ENV_KEY": "env_value"})
    def test_environment_variables(self):
        """Test environment variables override config file values."""
        self.config_manager.set("env_key", "file_value")
        self.assertEqual(self.config_manager.get("env_key"), "env_value")


class TestAPIKeyManager(unittest.TestCase):
    """Test cases for the APIKeyManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.config_manager = ConfigManager(self.config_path)
        self.api_key_manager = APIKeyManager(self.config_manager)

    def tearDown(self):
        """Clean up test environment after each test."""
        self.temp_dir.cleanup()

    def test_set_get_api_key(self):
        """Test setting and getting API keys."""
        self.api_key_manager.set_api_key("openai", "test_api_key")
        self.assertEqual(self.api_key_manager.get_api_key("openai"), "test_api_key")

    def test_delete_api_key(self):
        """Test deleting API keys."""
        self.api_key_manager.set_api_key("openai", "test_api_key")
        self.api_key_manager.delete_api_key("openai")
        self.assertIsNone(self.api_key_manager.get_api_key("openai"))

    def test_get_all_api_keys(self):
        """Test getting all API keys."""
        self.api_key_manager.set_api_key("openai", "openai_key")
        self.api_key_manager.set_api_key("huggingface", "hf_key")
        all_keys = self.api_key_manager.get_all_api_keys()
        self.assertEqual(all_keys["openai"], "openai_key")
        self.assertEqual(all_keys["huggingface"], "hf_key")

    def test_save_load_api_keys(self):
        """Test saving and loading API keys."""
        self.api_key_manager.set_api_key("openai", "test_api_key")
        
        # Create a new API key manager to load the saved keys
        new_api_key_manager = APIKeyManager(self.config_manager)
        self.assertEqual(new_api_key_manager.get_api_key("openai"), "test_api_key")


if __name__ == "__main__":
    unittest.main()
