# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a single large data file with transcriptions from the Cairo Genizah collection. The Cairo Genizah is a collection of Jewish manuscript fragments found in the genizah (storeroom) of the Ben Ezra Synagogue in Cairo, Egypt.

## Data Structure

### GenizaTranscriptions.txt

- **Format**: UTF-8 encoded text file (~390 MB)
- **Language**: Primarily Hebrew and Judeo-Arabic (Arabic written in Hebrew script)
- **Structure**: Documents are separated by headers in the format:
  ```
  ==> DOCUMENT_ID <==
  [transcribed text lines]
  ```
- **Document ID Format**: `{number}_{IE_number}_P{page}_FL{fragment}`
  - Example: `990000412990205171_IE104549337_P000001_FL104549339`
- **Content**: Historical texts including religious commentaries, Mishnah, legal documents, letters, and other manuscripts

### Text Characteristics

- Mixed Hebrew and Judeo-Arabic content
- Includes editorial marks and annotations:
  - `⟦/⟧` - likely indicates deletions or corrections
  - `][` - brackets for uncertain or damaged text
  - Numbers on the left indicate line numbers (appears to use cat -n format)
- Contains both biblical and rabbinic texts (Mishnah, commentaries)
- Some texts include phonetic/linguistic analysis (visible in early sections discussing Hebrew letter pronunciation)

## Expected Development Tasks

When building tools for this repository, typical tasks might include:

1. **Search/Query Tools**: Searching across documents by ID, content, or keywords
2. **Parsing**: Extracting document IDs, separating individual documents
3. **Text Processing**: Handling right-to-left Hebrew/Arabic text, Unicode normalization
4. **Indexing**: Creating searchable indices of documents
5. **Analysis**: Text analysis, linguistic studies, or digital humanities research

## Technical Considerations

- **Encoding**: Always handle files as UTF-8
- **Text Direction**: Content is right-to-left (Hebrew/Arabic)
- **Line Numbers**: If present (from cat -n), they appear at the start of each line
- **Document Boundaries**: Use the `==> ... <==` pattern to identify document starts
- **File Size**: The main data file is very large (~390 MB); consider streaming or chunked processing for efficiency

## Search Tool Architecture

### Design Decisions

1. **No Hebrew Stemming**: Initial version uses exact text matching without morphological analysis (planned for future version)
2. **Simple Schema**: No automatic document type classification; keep metadata minimal
3. **Multi-user, No Auth**: Support concurrent users without login system
4. **Deployment**: Local development first, server deployment later

### Technology Stack

- **Search Engine**: Whoosh (pure Python, good for file size, handles multi-user with locking)
- **Web Framework**: Flask
- **Text Processing**: python-bidi, arabic-reshaper for RTL handling
- **Frontend**: Simple HTML/CSS/JS with RTL support

### Index Schema

```python
{
    'doc_id': ID,           # Unique document identifier
    'content': TEXT,        # Full document text (stored, searchable)
    'line_count': NUMERIC,  # Number of lines in document
    'has_annotations': BOOLEAN  # Contains editorial marks (⟦/⟧)
}
```

### Module Structure

- `parser.py`: Extract documents from GenizaTranscriptions.txt
- `indexer.py`: Build Whoosh search index
- `searcher.py`: Search functionality (full-text, ID lookup, regex)
- `app.py`: Flask web application
- `cli.py`: Command-line interface

### Common Commands

Build the search index:
```bash
python -m genizah_search.indexer --input GenizaTranscriptions.txt --output index/
```

Run the web application:
```bash
python -m genizah_search.app
# Or: flask --app genizah_search.app run
```

Run tests:
```bash
pytest
```

### Development Workflow

**IMPORTANT**: After any code change, ALWAYS run the following checks:

1. **Linting**: Run code formatter and linter
   ```bash
   black src/ tests/
   ruff src/ tests/
   ```

2. **Testing**: Run the test suite to ensure nothing broke
   ```bash
   pytest
   ```

3. **Fix Issues**: If linting or tests fail, fix the issues immediately before proceeding.

This ensures code quality and catches regressions early.
