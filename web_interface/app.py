"""
Web interface for NLQ Translator.

This module provides a Flask web application that serves as a user-friendly
interface for the NLQ Translator library.
"""

import json
import os
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from nlq_translator import NLQueryTranslator
from nlq_translator.config import APIKeyManager, ConfigManager

app = Flask(__name__)
CORS(app)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize components
config_manager = ConfigManager(f"{project_root}/config.json")

# Initialize the translator
api_key_manager = APIKeyManager(config_manager)
translator = NLQueryTranslator(api_key_manager=api_key_manager)

# Track connection state
elasticsearch_connected = False
current_mapping = None


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/translate', methods=['POST'])
def translate():
    """Translate natural language to Elasticsearch query."""
    try:
        data = request.json
        
        # Get natural language query
        natural_language = data.get('query', '')
        if not natural_language:
            return jsonify({'error': 'No query provided'}), 400
        
        # Get mapping
        mapping = data.get('mapping')
        if mapping and isinstance(mapping, str):
            try:
                mapping = json.loads(mapping)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid mapping JSON'}), 400
        
        # Set OpenAI API key if provided
        api_key = data.get('api_key')
        if api_key:
            translator.set_llm('openai', api_key=api_key)
        
        # Translate the query
        query = translator.translate(natural_language, mapping=mapping)
        
        # Format the query as JSON
        formatted_query = json.dumps(query, indent=2)
        
        return jsonify({
            'query': formatted_query,
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate an Elasticsearch query."""
    try:
        data = request.json
        
        # Get query
        query_str = data.get('query', '')
        if not query_str:
            return jsonify({'error': 'No query provided'}), 400
        
        # Parse query
        try:
            query = json.loads(query_str)
        except json.JSONDecodeError as e:
            return jsonify({
                'valid': False,
                'error': f'Invalid JSON: {str(e)}'
            })
        
        # Get mapping
        mapping = data.get('mapping')
        if mapping and isinstance(mapping, str):
            try:
                mapping = json.loads(mapping)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid mapping JSON'}), 400
        
        # Validate the query
        is_valid, error = translator.validate(query, mapping=mapping)
        
        return jsonify({
            'valid': is_valid,
            'error': error
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fix', methods=['POST'])
def fix():
    """Fix errors in an Elasticsearch query."""
    try:
        data = request.json
        
        # Get query
        query_str = data.get('query', '')
        if not query_str:
            return jsonify({'error': 'No query provided'}), 400
        
        # Parse query
        try:
            query = json.loads(query_str)
        except json.JSONDecodeError as e:
            return jsonify({
                'error': f'Invalid JSON: {str(e)}'
            }), 400
        
        # Get mapping
        mapping = data.get('mapping')
        if mapping and isinstance(mapping, str):
            try:
                mapping = json.loads(mapping)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid mapping JSON'}), 400
        
        # Get error message
        error_message = data.get('error')
        
        # Set OpenAI API key if provided
        api_key = data.get('api_key')
        if api_key:
            translator.set_llm('openai', api_key=api_key)
        
        # Fix the query
        fixed_query = translator.fix(query, error_message=error_message, mapping=mapping)
        
        # Format the query as JSON
        formatted_query = json.dumps(fixed_query, indent=2)
        
        return jsonify({
            'query': formatted_query,
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/improve', methods=['POST'])
def improve():
    """Improve an Elasticsearch query."""
    try:
        data = request.json
        
        # Get query
        query_str = data.get('query', '')
        if not query_str:
            return jsonify({'error': 'No query provided'}), 400
        
        # Parse query
        try:
            query = json.loads(query_str)
        except json.JSONDecodeError as e:
            return jsonify({
                'error': f'Invalid JSON: {str(e)}'
            }), 400
        
        # Get mapping
        mapping = data.get('mapping')
        if mapping and isinstance(mapping, str):
            try:
                mapping = json.loads(mapping)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid mapping JSON'}), 400
        
        # Get improvement goal
        improvement_goal = data.get('goal')
        
        # Set OpenAI API key if provided
        api_key = data.get('api_key')
        if api_key:
            translator.set_llm('openai', api_key=api_key)
        
        # Improve the query
        improved_query = translator.improve(query, improvement_goal=improvement_goal, mapping=mapping)
        
        # Format the query as JSON
        formatted_query = json.dumps(improved_query, indent=2)
        
        return jsonify({
            'query': formatted_query,
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to Elasticsearch."""
    global elasticsearch_connected, current_mapping
    
    try:
        data = request.json
        
        # Get connection parameters
        cloud_id = data.get('cloud_id')
        username = data.get('username')
        password = data.get('password')
        hosts = data.get('hosts')
        index = data.get('index')
        
        if not index:
            return jsonify({'error': 'Index name is required'}), 400
        
        if not (cloud_id or hosts):
            return jsonify({'error': 'Either cloud ID or hosts is required'}), 400
        
        # Disconnect if already connected
        if elasticsearch_connected:
            translator.disconnect_from_database()
            elasticsearch_connected = False
            current_mapping = None
        
        # Set database client
        if cloud_id:
            translator.set_database_client(
                'elasticsearch',
                cloud_id=cloud_id,
                username=username,
                password=password,
                index=index
            )
        else:
            translator.set_database_client(
                'elasticsearch',
                hosts=hosts.split(',') if isinstance(hosts, str) else hosts,
                username=username,
                password=password,
                index=index
            )
        
        # Connect to the database
        connected = translator.connect_to_database()
        
        if connected:
            elasticsearch_connected = True
            
            # Get mapping
            try:
                current_mapping = translator.database_client.get_mapping()
                mapping_str = json.dumps(current_mapping, indent=2)
            except Exception as e:
                return jsonify({
                    'connected': True,
                    'mapping': None,
                    'error': f'Connected but failed to get mapping: {str(e)}'
                })
            
            return jsonify({
                'connected': True,
                'mapping': mapping_str
            })
        else:
            return jsonify({
                'connected': False,
                'error': 'Failed to connect to Elasticsearch'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/execute', methods=['POST'])
def execute():
    """Execute an Elasticsearch query."""
    global elasticsearch_connected
    
    try:
        if not elasticsearch_connected:
            return jsonify({'error': 'Not connected to Elasticsearch'}), 400
        
        data = request.json
        
        # Get query
        query_str = data.get('query', '')
        if not query_str:
            return jsonify({'error': 'No query provided'}), 400
        
        # Parse query
        try:
            query = json.loads(query_str)
        except json.JSONDecodeError as e:
            return jsonify({
                'error': f'Invalid JSON: {str(e)}'
            }), 400
        
        # Execute the query
        results = translator.execute(query)
        
        # Format the results as JSON
        formatted_results = json.dumps(results, indent=2)
        
        return jsonify({
            'results': formatted_results,
            'success': True,
            'hit_count': results.get('hits', {}).get('total', {}).get('value', 0)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from Elasticsearch."""
    global elasticsearch_connected, current_mapping
    
    try:
        if not elasticsearch_connected:
            return jsonify({'success': True, 'message': 'Already disconnected'})
        
        disconnected = translator.disconnect_from_database()
        
        if disconnected:
            elasticsearch_connected = False
            current_mapping = None
            return jsonify({
                'success': True,
                'message': 'Disconnected from Elasticsearch'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to disconnect from Elasticsearch'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True)
