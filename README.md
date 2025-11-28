# Cairo Genizah Search Tool

[![CI](https://github.com/YOUR_USERNAME/cairo_genizah_search/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/cairo_genizah_search/actions/workflows/ci.yml)
[![Lint](https://github.com/YOUR_USERNAME/cairo_genizah_search/workflows/Lint/badge.svg)](https://github.com/YOUR_USERNAME/cairo_genizah_search/actions/workflows/lint.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A comprehensive search tool for exploring Cairo Genizah transcriptions. This project provides full-text search, document lookup, and language-aware search capabilities for Hebrew and Judeo-Arabic texts.

## Features

- **Full-text Search**: Search across all document content with relevance ranking
- **Document ID Lookup**: Find documents by their unique identifiers
- **Hebrew/Arabic Support**: Proper handling of right-to-left text and linguistic features
- **Pattern Matching**: Advanced regex and pattern-based search for research
- **Web Interface**: User-friendly browser-based interface
- **Fast Indexing**: Efficient indexing of large datasets using Whoosh

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Setup

1. Clone or navigate to the repository:
```bash
cd cairo_genizah_search
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- Unix/MacOS:
  ```bash
  source venv/bin/activate
  ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

For development:
```bash
pip install -r requirements-dev.txt
```

## Usage

### Building the Search Index

Before searching, you need to index the transcriptions:

```bash
genizah-index --input GenizaTranscriptions.txt --output index/
```

### Running the Web Interface

Start the web server:

```bash
python -m genizah_search.app
```

Then open your browser to `http://localhost:5000`

### Command Line Search

```bash
genizah-search --query "your search term" --index index/
```

## Development

### Continuous Integration

This project uses GitHub Actions for continuous integration. All pull requests and commits are automatically checked for:
- Code formatting (Black)
- Linting (Ruff)
- Type checking (mypy)
- Test coverage (pytest)

The CI runs on Python 3.9, 3.10, 3.11, and 3.12 to ensure compatibility.

### Running Tests Locally

```bash
pytest
```

With coverage report:
```bash
pytest --cov=src/genizah_search --cov-report=term-missing
```

### Code Formatting

Check formatting:
```bash
black --check src/ tests/
```

Auto-format:
```bash
black src/ tests/
```

### Linting

```bash
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/ --ignore-missing-imports
```

## Project Structure

```
cairo_genizah_search/
├── src/genizah_search/    # Main package
│   ├── __init__.py
│   ├── parser.py          # Parse GenizaTranscriptions.txt
│   ├── indexer.py         # Build search index
│   ├── searcher.py        # Search functionality
│   ├── app.py             # Flask web application
│   └── cli.py             # Command-line interface
├── templates/             # HTML templates for web UI
├── static/                # CSS, JS, and other static assets
├── tests/                 # Test suite
├── data/                  # Sample data or configs
├── index/                 # Generated search index (gitignored)
└── GenizaTranscriptions.txt  # Source data
```

## Data Format

The transcriptions file contains documents in the format:

```
==> DOCUMENT_ID <==
[transcribed text]
```

Document IDs follow the pattern: `{number}_{IE_number}_P{page}_FL{fragment}`

## License

[Specify your license here]

## Contributing

[Add contribution guidelines if applicable]
