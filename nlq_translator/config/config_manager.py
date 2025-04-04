"""
Configuration manager for NLQ Translator.

This module provides classes for managing configuration settings and API keys
for the NLQ Translator library.
"""

import os
import json
from typing import Dict, Optional, Any, Union
from pathlib import Path


class ConfigManager:
    """
    Manages configuration settings for the NLQ Translator library.
    
    This class handles loading, saving, and accessing configuration settings
    from a JSON file or environment variables.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Optional path to a JSON configuration file.
                If not provided, will look for a file at ~/.nlq_translator/config.json
                or use environment variables.
        """
        self._config: Dict[str, Any] = {}
        self._config_path = config_path
        
        if config_path is None:
            # Default to ~/.nlq_translator/config.json
            home_dir = Path.home()
            self._config_path = home_dir / ".nlq_translator" / "config.json"
        else:
            self._config_path = Path(config_path)
        
        # Load config if file exists
        if Path(self._config_path).exists():
            self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the config file.
        
        Returns:
            The loaded configuration dictionary.
        """
        try:
            with open(self._config_path, 'r') as f:
                self._config = json.load(f)
            return self._config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load config file: {e}")
            return {}
    
    def save_config(self) -> None:
        """
        Save the current configuration to the config file.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        
        try:
            with open(self._config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key to retrieve.
            default: The default value to return if the key is not found.
            
        Returns:
            The configuration value or the default value.
        """
        # First check environment variables
        env_var = f"NLQ_TRANSLATOR_{key.upper()}"
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value
        
        # Then check config file
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key to set.
            value: The value to set.
        """
        self._config[key] = value
    
    def delete(self, key: str) -> None:
        """
        Delete a configuration value.
        
        Args:
            key: The configuration key to delete.
        """
        if key in self._config:
            del self._config[key]
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            A dictionary of all configuration values.
        """
        # Start with config file values
        all_config = dict(self._config)
        
        # Override with environment variables
        for key in os.environ:
            if key.startswith("NLQ_TRANSLATOR_"):
                config_key = key[len("NLQ_TRANSLATOR_"):].lower()
                all_config[config_key] = os.environ[key]
        
        return all_config


class APIKeyManager:
    """
    Manages API keys for different LLM providers.
    
    This class provides methods for setting, getting, and validating API keys
    for various LLM providers such as OpenAI, HuggingFace, etc.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the APIKeyManager.
        
        Args:
            config_manager: Optional ConfigManager instance to use.
                If not provided, a new ConfigManager will be created.
        """
        self._config_manager = config_manager or ConfigManager()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get the API key for a specific provider.
        
        Args:
            provider: The name of the LLM provider (e.g., 'openai', 'huggingface').
            
        Returns:
            The API key or None if not found.
        """
        key = f"{provider.lower()}_api_key"
        return self._config_manager.get(key)
    
    def set_api_key(self, provider: str, api_key: str, save: bool = True) -> None:
        """
        Set the API key for a specific provider.
        
        Args:
            provider: The name of the LLM provider (e.g., 'openai', 'huggingface').
            api_key: The API key to set.
            save: Whether to save the configuration to disk.
        """
        key = f"{provider.lower()}_api_key"
        self._config_manager.set(key, api_key)
        
        if save:
            self._config_manager.save_config()
    
    def delete_api_key(self, provider: str, save: bool = True) -> None:
        """
        Delete the API key for a specific provider.
        
        Args:
            provider: The name of the LLM provider (e.g., 'openai', 'huggingface').
            save: Whether to save the configuration to disk.
        """
        key = f"{provider.lower()}_api_key"
        self._config_manager.delete(key)
        
        if save:
            self._config_manager.save_config()
    
    def get_all_api_keys(self) -> Dict[str, str]:
        """
        Get all API keys.
        
        Returns:
            A dictionary mapping provider names to API keys.
        """
        all_config = self._config_manager.get_all()
        api_keys = {}
        
        for key, value in all_config.items():
            if key.endswith("_api_key"):
                provider = key[:-8]  # Remove "_api_key" suffix
                api_keys[provider] = value
        
        return api_keys
