"""
LLM interface module for NLQ Translator.

This module provides interfaces and implementations for different language models
that can be used to translate natural language queries into database queries.
"""

from .llm_interface import LLMInterface, LLMResponse
from .openai_llm import OpenAILLM

__all__ = ['LLMInterface', 'LLMResponse', 'OpenAILLM']
