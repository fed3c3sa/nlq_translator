"""
Command-line interface for NLQ Translator.

This module provides a command-line interface for using the NLQ Translator library.
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Optional, List, Union

from .core import NLQueryTranslator
from .config import APIKeyManager, ConfigManager
from .export import ExportFormat


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Translate natural language to database queries"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Translate command
    translate_parser = subparsers.add_parser(
        "translate", help="Translate natural language to a database query"
    )
    translate_parser.add_argument(
        "query", help="Natural language query to translate"
    )
    translate_parser.add_argument(
        "--mapping", "-m", help="Path to JSON file containing the database mapping"
    )
    translate_parser.add_argument(
        "--output", "-o", help="Path to output file for the generated query"
    )
    translate_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="json",
        help="Output format (default: json)"
    )
    translate_parser.add_argument(
        "--pretty", "-p", action="store_true", default=True,
        help="Pretty-print the output (default: true)"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate a database query"
    )
    validate_parser.add_argument(
        "query", help="Path to JSON file containing the query to validate"
    )
    validate_parser.add_argument(
        "--mapping", "-m", help="Path to JSON file containing the database mapping"
    )
    
    # Fix command
    fix_parser = subparsers.add_parser(
        "fix", help="Fix errors in a database query"
    )
    fix_parser.add_argument(
        "query", help="Path to JSON file containing the query to fix"
    )
    fix_parser.add_argument(
        "--mapping", "-m", help="Path to JSON file containing the database mapping"
    )
    fix_parser.add_argument(
        "--error", "-e", help="Error message to guide the fix"
    )
    fix_parser.add_argument(
        "--output", "-o", help="Path to output file for the fixed query"
    )
    fix_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="json",
        help="Output format (default: json)"
    )
    fix_parser.add_argument(
        "--pretty", "-p", action="store_true", default=True,
        help="Pretty-print the output (default: true)"
    )
    
    # Improve command
    improve_parser = subparsers.add_parser(
        "improve", help="Improve a database query"
    )
    improve_parser.add_argument(
        "query", help="Path to JSON file containing the query to improve"
    )
    improve_parser.add_argument(
        "--mapping", "-m", help="Path to JSON file containing the database mapping"
    )
    improve_parser.add_argument(
        "--goal", "-g", help="Improvement goal to guide the improvement"
    )
    improve_parser.add_argument(
        "--output", "-o", help="Path to output file for the improved query"
    )
    improve_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="json",
        help="Output format (default: json)"
    )
    improve_parser.add_argument(
        "--pretty", "-p", action="store_true", default=True,
        help="Pretty-print the output (default: true)"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Configure API keys and settings"
    )
    config_parser.add_argument(
        "--set-api-key", "-s", help="Set API key for a provider (format: provider:key)"
    )
    config_parser.add_argument(
        "--get-api-key", "-g", help="Get API key for a provider"
    )
    config_parser.add_argument(
        "--list-api-keys", "-l", action="store_true", help="List all API keys"
    )
    
    return parser.parse_args()


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON from a file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading JSON file: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    if not args.command:
        print("No command specified. Use --help for usage information.")
        sys.exit(1)
    
    # Initialize components
    config_manager = ConfigManager()
    api_key_manager = APIKeyManager(config_manager)
    translator = NLQueryTranslator(api_key_manager=api_key_manager)
    
    if args.command == "translate":
        # Load mapping if provided
        mapping = None
        if args.mapping:
            mapping = load_json_file(args.mapping)
        
        # Translate the query
        try:
            query = translator.translate(args.query, mapping=mapping)
            
            # Export the query
            format_enum = ExportFormat.JSON if args.format == "json" else ExportFormat.TEXT
            result = translator.export(query, format=format_enum, file_path=args.output, pretty=args.pretty)
            
            # Print the result if no output file specified
            if not args.output:
                print(result)
            
            print("Translation successful.")
        except Exception as e:
            print(f"Error translating query: {str(e)}")
            sys.exit(1)
    
    elif args.command == "validate":
        # Load the query
        query = load_json_file(args.query)
        
        # Load mapping if provided
        mapping = None
        if args.mapping:
            mapping = load_json_file(args.mapping)
        
        # Validate the query
        try:
            is_valid, error = translator.validate(query, mapping=mapping)
            
            if is_valid:
                print("Query is valid.")
            else:
                print(f"Query is invalid: {error}")
                sys.exit(1)
        except Exception as e:
            print(f"Error validating query: {str(e)}")
            sys.exit(1)
    
    elif args.command == "fix":
        # Load the query
        query = load_json_file(args.query)
        
        # Load mapping if provided
        mapping = None
        if args.mapping:
            mapping = load_json_file(args.mapping)
        
        # Fix the query
        try:
            fixed_query = translator.fix(query, error_message=args.error, mapping=mapping)
            
            # Export the query
            format_enum = ExportFormat.JSON if args.format == "json" else ExportFormat.TEXT
            result = translator.export(fixed_query, format=format_enum, file_path=args.output, pretty=args.pretty)
            
            # Print the result if no output file specified
            if not args.output:
                print(result)
            
            print("Query fixed successfully.")
        except Exception as e:
            print(f"Error fixing query: {str(e)}")
            sys.exit(1)
    
    elif args.command == "improve":
        # Load the query
        query = load_json_file(args.query)
        
        # Load mapping if provided
        mapping = None
        if args.mapping:
            mapping = load_json_file(args.mapping)
        
        # Improve the query
        try:
            improved_query = translator.improve(query, improvement_goal=args.goal, mapping=mapping)
            
            # Export the query
            format_enum = ExportFormat.JSON if args.format == "json" else ExportFormat.TEXT
            result = translator.export(improved_query, format=format_enum, file_path=args.output, pretty=args.pretty)
            
            # Print the result if no output file specified
            if not args.output:
                print(result)
            
            print("Query improved successfully.")
        except Exception as e:
            print(f"Error improving query: {str(e)}")
            sys.exit(1)
    
    elif args.command == "config":
        if args.set_api_key:
            # Parse provider:key format
            try:
                provider, key = args.set_api_key.split(":", 1)
                api_key_manager.set_api_key(provider, key)
                print(f"API key for {provider} set successfully.")
            except ValueError:
                print("Invalid format for --set-api-key. Use 'provider:key' format.")
                sys.exit(1)
        
        elif args.get_api_key:
            key = api_key_manager.get_api_key(args.get_api_key)
            if key:
                print(f"API key for {args.get_api_key}: {key}")
            else:
                print(f"No API key found for {args.get_api_key}")
                sys.exit(1)
        
        elif args.list_api_keys:
            keys = api_key_manager.get_all_api_keys()
            if keys:
                print("API keys:")
                for provider, key in keys.items():
                    # Mask the key for security
                    masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"
                    print(f"  {provider}: {masked_key}")
            else:
                print("No API keys configured.")
        
        else:
            print("No config action specified. Use --help for usage information.")
            sys.exit(1)


if __name__ == "__main__":
    main()
