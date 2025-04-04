"""
Unit tests for the export module.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from nlq_translator.export import QueryExporter, ExportFormat


class TestQueryExporter(unittest.TestCase):
    """Test cases for the QueryExporter class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_query = {
            "query": {
                "match": {
                    "content": "test"
                }
            }
        }
        self.test_query_str = json.dumps(self.test_query)
        self.exporter = QueryExporter()

    def tearDown(self):
        """Clean up test environment after each test."""
        self.temp_dir.cleanup()

    def test_export_to_json(self):
        """Test exporting a query to JSON format."""
        # Test with dictionary input
        json_str = self.exporter.export_to_json(self.test_query)
        self.assertEqual(json.loads(json_str), self.test_query)
        
        # Test with string input
        json_str = self.exporter.export_to_json(self.test_query_str)
        self.assertEqual(json.loads(json_str), self.test_query)
        
        # Test pretty printing
        pretty_exporter = QueryExporter(pretty_print=True)
        pretty_json = pretty_exporter.export_to_json(self.test_query)
        self.assertIn("\n", pretty_json)
        
        # Test non-pretty printing
        non_pretty_exporter = QueryExporter(pretty_print=False)
        non_pretty_json = non_pretty_exporter.export_to_json(self.test_query)
        self.assertNotIn("\n", non_pretty_json)

    def test_export_to_json_file(self):
        """Test exporting a query to a JSON file."""
        file_path = Path(self.temp_dir.name) / "test_query.json"
        self.exporter.export_to_json(self.test_query, file_path=file_path)
        
        # Verify the file was created and contains the correct content
        self.assertTrue(file_path.exists())
        with open(file_path, 'r') as f:
            content = f.read()
        self.assertEqual(json.loads(content), self.test_query)

    def test_export_to_text(self):
        """Test exporting a query to text format."""
        # Test with dictionary input
        text_str = self.exporter.export_to_text(self.test_query)
        self.assertEqual(json.loads(text_str), self.test_query)
        
        # Test with string input
        text_str = self.exporter.export_to_text(self.test_query_str)
        self.assertEqual(text_str, self.test_query_str)

    def test_export_to_text_file(self):
        """Test exporting a query to a text file."""
        file_path = Path(self.temp_dir.name) / "test_query.txt"
        self.exporter.export_to_text(self.test_query, file_path=file_path)
        
        # Verify the file was created and contains the correct content
        self.assertTrue(file_path.exists())
        with open(file_path, 'r') as f:
            content = f.read()
        self.assertEqual(json.loads(content), self.test_query)

    def test_export_with_enum(self):
        """Test exporting a query using the ExportFormat enum."""
        # Test JSON format
        json_str = self.exporter.export(self.test_query, ExportFormat.JSON)
        self.assertEqual(json.loads(json_str), self.test_query)
        
        # Test TEXT format
        text_str = self.exporter.export(self.test_query, ExportFormat.TEXT)
        self.assertEqual(json.loads(text_str), self.test_query)

    def test_export_with_string_format(self):
        """Test exporting a query using string format names."""
        # Test JSON format
        json_str = self.exporter.export(self.test_query, "JSON")
        self.assertEqual(json.loads(json_str), self.test_query)
        
        # Test TEXT format
        text_str = self.exporter.export(self.test_query, "TEXT")
        self.assertEqual(json.loads(text_str), self.test_query)
        
        # Test invalid format
        with self.assertRaises(ValueError):
            self.exporter.export(self.test_query, "INVALID_FORMAT")

    def test_export_with_file_handle(self):
        """Test exporting a query using a file handle."""
        file_path = Path(self.temp_dir.name) / "test_query_handle.json"
        with open(file_path, 'w') as f:
            self.exporter.export_to_json(self.test_query, file_handle=f)
        
        # Verify the file contains the correct content
        with open(file_path, 'r') as f:
            content = f.read()
        self.assertEqual(json.loads(content), self.test_query)

    def test_invalid_json(self):
        """Test exporting an invalid JSON string raises an error."""
        invalid_json = "{invalid json"
        with self.assertRaises(ValueError):
            self.exporter.export_to_json(invalid_json)


if __name__ == "__main__":
    unittest.main()
