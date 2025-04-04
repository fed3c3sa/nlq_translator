"""
Database module for NLQ Translator.

This module provides interfaces and implementations for connecting to and
interacting with different database systems.
"""

from .database_interface import DatabaseInterface
from .elasticsearch_client import ElasticsearchClient

__all__ = ['DatabaseInterface', 'ElasticsearchClient']
