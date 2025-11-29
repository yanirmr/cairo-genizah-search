# Test Suite Documentation

This directory contains the test suite for the Cairo Genizah Search application.

## Test Files

### Unit Tests

- **test_parser.py** - Tests for the GenizahParser module
  - Document parsing and extraction
  - Line number stripping
  - Annotation detection
  - Document counting

- **test_indexer.py** - Tests for the GenizahIndexer module
  - Index creation and building
  - Index schema validation
  - Index reopening
  - Basic search functionality

- **test_searcher.py** - Tests for the GenizahSearcher module
  - Full-text search
  - Document ID search
  - Regex search
  - Advanced search with filters
  - Highlight generation
  - Statistics retrieval

- **test_app.py** - Tests for the Flask web application
  - Web page rendering
  - Search endpoints
  - API endpoints
  - Error handling

- **test_cli.py** - Tests for the command-line interface
  - CLI commands
  - Output formatting
  - Error handling

### End-to-End Tests

- **test_e2e.py** - Comprehensive end-to-end tests
  - **TestE2EDataParsing**: Tests parsing the sample data file
  - **TestE2EIndexing**: Tests building an index from sample data
  - **TestE2ESearching**: Tests all search functionality with realistic data
  - **TestE2EWebInterface**: Tests the complete web interface workflow
  - **TestE2ECompleteWorkflow**: Tests realistic user workflows
  - **TestE2ERobustness**: Tests edge cases and error handling

## Sample Data

### sample_genizah_data.txt

This file contains a representative sample of the Cairo Genizah transcription data for testing purposes. It includes:

- **11 documents total**:
  - 8 authentic documents from the actual GenizaTranscriptions.txt file
  - 3 test documents with known content for targeted testing

- **Document Types**:
  - Linguistic analysis documents (in Judeo-Arabic)
  - Test Mishnah document (Hebrew)
  - Test Talmud document (Hebrew with annotations)
  - Test Judeo-Arabic letter

- **Features Represented**:
  - Line numbers (using → separator)
  - Editorial annotations (⟦/⟧)
  - Brackets for uncertain text (][)
  - Mixed Hebrew and Judeo-Arabic content
  - Various document lengths (from 6 to 32 lines)

The sample data is used by the end-to-end tests to verify the complete workflow without requiring the large (390 MB) GenizaTranscriptions.txt file.

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Run only e2e tests
pytest tests/test_e2e.py

# Run only parser tests
pytest tests/test_parser.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Coverage

```bash
pytest --cov=src/genizah_search --cov-report=term-missing
```

### Run Without Coverage (faster)

```bash
pytest --no-cov
```

## Test Coverage

The test suite aims for comprehensive coverage:

- **Parser**: Line-by-line parsing, annotation detection, document extraction
- **Indexer**: Index creation, schema validation, document indexing
- **Searcher**: All search types (fulltext, docid, regex), filters, statistics
- **Web App**: All routes, API endpoints, error handling
- **CLI**: Command-line interface functionality
- **End-to-End**: Complete workflows from data file to search results

## Continuous Integration

Tests are automatically run on GitHub Actions for every push and pull request:

- **Python versions tested**: 3.9, 3.10, 3.11, 3.12
- **Linting**: Black (formatting) and Ruff (linting)
- **Type checking**: mypy (continue-on-error)
- **Coverage**: Codecov integration

See `.github/workflows/ci.yml` for the full CI configuration.

## Adding New Tests

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Use descriptive test names that explain what is being tested
3. Include docstrings for test functions
4. Use fixtures for shared setup (see conftest.py if created)
5. Run `black tests/` and `ruff check tests/` before committing
6. Ensure all tests pass with `pytest`

## Test Data Maintenance

The `sample_genizah_data.txt` file should be updated if:

- New document format variations are discovered
- New edge cases need to be tested
- Additional document types need representation

Keep the file reasonably small (currently ~11 documents) to maintain fast test execution.
