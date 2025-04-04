"""
Query exporter for NLQ Translator.

This module provides functionality for exporting queries to various formats,
including JSON and plain text.
"""

import json
import os
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, Union, TextIO, BinaryIO


class ExportFormat(Enum):
    """Enumeration of supported export formats."""
    JSON = auto()
    TEXT = auto()


class QueryExporter:
    """
    Exports queries to various formats.
    
    This class provides methods for exporting queries to different formats,
    including JSON and plain text, and saving them to files.
    """
    
    def __init__(self, pretty_print: bool = True):
        """
        Initialize the query exporter.
        
        Args:
            pretty_print: Whether to format the output for readability (default: True).
        """
        self.pretty_print = pretty_print
    
    def export_to_json(
        self, 
        query: Union[str, Dict[str, Any]],
        file_path: Optional[Union[str, Path]] = None,
        file_handle: Optional[TextIO] = None
    ) -> str:
        """
        Export a query to JSON format.
        
        Args:
            query: The query to export (string or dictionary).
            file_path: Optional path to save the exported query to.
            file_handle: Optional file handle to write the exported query to.
            
        Returns:
            The query as a JSON string.
            
        Raises:
            ValueError: If the query is not valid JSON.
            IOError: If there is an error writing to the file.
        """
        # Convert query to dictionary if it's a string
        if isinstance(query, str):
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON query: {str(e)}")
        else:
            query_dict = query
        
        # Convert to JSON string
        indent = 2 if self.pretty_print else None
        json_str = json.dumps(query_dict, indent=indent)
        
        # Write to file if specified
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(json_str)
            except IOError as e:
                raise IOError(f"Error writing to file {file_path}: {str(e)}")
        
        # Write to file handle if specified
        if file_handle:
            try:
                file_handle.write(json_str)
            except IOError as e:
                raise IOError(f"Error writing to file handle: {str(e)}")
        
        return json_str
    
    def export_to_text(
        self, 
        query: Union[str, Dict[str, Any]],
        file_path: Optional[Union[str, Path]] = None,
        file_handle: Optional[TextIO] = None
    ) -> str:
        """
        Export a query to plain text format.
        
        Args:
            query: The query to export (string or dictionary).
            file_path: Optional path to save the exported query to.
            file_handle: Optional file handle to write the exported query to.
            
        Returns:
            The query as a plain text string.
            
        Raises:
            ValueError: If the query is not valid JSON.
            IOError: If there is an error writing to the file.
        """
        # Convert query to string if it's a dictionary
        if isinstance(query, dict):
            indent = 2 if self.pretty_print else None
            query_str = json.dumps(query, indent=indent)
        else:
            query_str = query
        
        # Write to file if specified
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(query_str)
            except IOError as e:
                raise IOError(f"Error writing to file {file_path}: {str(e)}")
        
        # Write to file handle if specified
        if file_handle:
            try:
                file_handle.write(query_str)
            except IOError as e:
                raise IOError(f"Error writing to file handle: {str(e)}")
        
        return query_str
    
    def export(
        self, 
        query: Union[str, Dict[str, Any]],
        format: ExportFormat,
        file_path: Optional[Union[str, Path]] = None,
        file_handle: Optional[TextIO] = None
    ) -> str:
        """
        Export a query to the specified format.
        
        Args:
            query: The query to export (string or dictionary).
            format: The format to export to (ExportFormat.JSON or ExportFormat.TEXT).
            file_path: Optional path to save the exported query to.
            file_handle: Optional file handle to write the exported query to.
            
        Returns:
            The exported query as a string.
            
        Raises:
            ValueError: If the query is not valid or the format is not supported.
            IOError: If there is an error writing to the file.
        """
        if format == ExportFormat.JSON:
            return self.export_to_json(query, file_path, file_handle)
        elif format == ExportFormat.TEXT:
            return self.export_to_text(query, file_path, file_handle)
        else:
            raise ValueError(f"Unsupported export format: {format}")
