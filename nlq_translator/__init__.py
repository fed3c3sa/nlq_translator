"""
NLQ Translator: A library for translating natural language to database queries.

This library provides functionality for translating natural language queries into
database queries (currently supporting Elasticsearch), with features for validation,
fixing, and improving queries.
"""

from .core import NLQueryTranslator
from .config import ConfigManager, APIKeyManager
from .llm import LLMInterface, OpenAILLM
from .database import DatabaseInterface, ElasticsearchClient
from .export import QueryExporter, ExportFormat
from .elasticsearch import ElasticsearchQueryGenerator, ElasticsearchQueryValidator

__version__ = '0.1.0'

__all__ = [
    'NLQueryTranslator',
    'ConfigManager',
    'APIKeyManager',
    'LLMInterface',
    'OpenAILLM',
    'DatabaseInterface',
    'ElasticsearchClient',
    'QueryExporter',
    'ExportFormat',
    'ElasticsearchQueryGenerator',
    'ElasticsearchQueryValidator',
]
