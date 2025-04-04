# NLQ Translator

A Python library for translating natural language queries into Elasticsearch queries with support for validation, fixing, and improvement.

## Features

- **Natural Language to Elasticsearch**: Translate natural language questions into Elasticsearch queries
- **Multiple LLM Support**: Use OpenAI's GPT models with an extensible interface for other LLMs
- **Database Integration**: Connect directly to Elasticsearch with support for cloud ID, username, and password
- **Context-Aware Mapping**: Pass Elasticsearch mappings as context for more accurate query generation
- **Query Validation**: Validate queries against Elasticsearch schema and mappings
- **Query Fixing**: Automatically fix invalid queries
- **Query Improvement**: Enhance queries for better performance and results
- **Export Functionality**: Export queries as JSON or text files
- **Command-Line Interface**: Use all features directly from the command line
- **Extensible Design**: Designed for future support of additional databases

## Installation

### From PyPI

```bash
pip install nlq-translator
```

### From Source

```bash
git clone https://github.com/nlq-translator/nlq-translator.git
cd nlq-translator
pip install -e .
```

## Quick Start

### Python API

```python
from nlq_translator import NLQueryTranslator

# Initialize the translator
translator = NLQueryTranslator()

# Set your OpenAI API key
translator.set_llm("openai", api_key="your-openai-api-key")

# Translate a natural language query to Elasticsearch
query = translator.translate(
    "Find documents about climate change published after 2020",
    mapping={
        "properties": {
            "content": {"type": "text"},
            "title": {"type": "text"},
            "date": {"type": "date"}
        }
    }
)

# Print the query
print(translator.export(query, format="json", pretty=True))

# Connect to Elasticsearch
translator.set_database_client(
    "elasticsearch",
    cloud_id="your-cloud-id",
    username="your-username",
    password="your-password",
    index="your-index"
)
translator.connect_to_database()

# Execute the query
results = translator.execute(query)
print(f"Found {results['hits']['total']['value']} documents")
```

### Command Line

```bash
# Set your OpenAI API key
nlq-translator config --set-api-key openai:your-openai-api-key

# Translate a query
nlq-translator translate "Find documents about climate change published after 2020" --mapping mapping.json --output query.json

# Validate a query
nlq-translator validate query.json --mapping mapping.json

# Fix a query
nlq-translator fix invalid_query.json --mapping mapping.json --output fixed_query.json

# Improve a query
nlq-translator improve query.json --goal "Add filters for better performance" --output improved_query.json
```

## Configuration

NLQ Translator can be configured using environment variables or a configuration file:

- `NLQ_TRANSLATOR_OPENAI_API_KEY`: OpenAI API key
- `NLQ_TRANSLATOR_CONFIG_PATH`: Path to configuration file

You can also use the CLI to manage configuration:

```bash
# Set API key
nlq-translator config --set-api-key openai:your-openai-api-key

# List API keys
nlq-translator config --list-api-keys
```

## API Reference

### Core Module

#### `NLQueryTranslator`

The main class that integrates all components of the library.

```python
translator = NLQueryTranslator(
    llm=None,                    # Optional LLM interface
    database_client=None,        # Optional database client
    config_manager=None,         # Optional config manager
    api_key_manager=None         # Optional API key manager
)
```

Methods:

- `translate(natural_language, mapping=None, **kwargs)`: Translate natural language to a query
- `validate(query, mapping=None)`: Validate a query
- `fix(query, error_message=None, mapping=None, **kwargs)`: Fix errors in a query
- `improve(query, improvement_goal=None, mapping=None, **kwargs)`: Improve a query
- `execute(query)`: Execute a query against the connected database
- `export(query, format="json", file_path=None, pretty=True)`: Export a query to a file

### LLM Module

#### `LLMInterface`

Abstract base class for language model interfaces.

#### `OpenAILLM`

Implementation of `LLMInterface` using OpenAI's GPT models.

```python
llm = OpenAILLM(
    api_key=None,                # OpenAI API key
    model="gpt-4",               # Model to use
    temperature=0.1,             # Temperature for generation
    max_tokens=2000,             # Maximum tokens to generate
    api_key_manager=None         # Optional API key manager
)
```

### Database Module

#### `DatabaseInterface`

Abstract base class for database interfaces.

#### `ElasticsearchClient`

Implementation of `DatabaseInterface` for Elasticsearch.

```python
client = ElasticsearchClient(
    hosts=None,                  # Host or list of hosts
    cloud_id=None,               # Cloud ID for Elastic Cloud
    username=None,               # Username for authentication
    password=None,               # Password for authentication
    api_key=None,                # API key for authentication
    index=None                   # Default index to use
)
```

### Export Module

#### `QueryExporter`

Class for exporting queries to various formats.

```python
exporter = QueryExporter(
    pretty_print=True            # Whether to format output for readability
)
```

Methods:

- `export_to_json(query, file_path=None, file_handle=None)`: Export to JSON
- `export_to_text(query, file_path=None, file_handle=None)`: Export to text
- `export(query, format, file_path=None, file_handle=None)`: Export to specified format

## Web Interface

A separate web interface is available for NLQ Translator. To install it:

```bash
pip install nlq-translator[web]
```

To run the web interface:

```bash
# Coming in a future release
```

## Development

### Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
nlq_translator/
├── config/            # Configuration management
├── core/              # Core translator functionality
├── database/          # Database connection interfaces
├── elasticsearch/     # Elasticsearch query generation
├── export/            # Query export functionality
├── llm/               # Language model interfaces
└── utils/             # Utility functions
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
