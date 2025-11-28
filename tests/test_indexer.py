"""Tests for the Genizah indexer module."""

import tempfile
from pathlib import Path

import pytest
from whoosh import index

from genizah_search.indexer import GenizahIndexer


@pytest.fixture
def sample_transcription_file():
    """Create a temporary transcription file."""
    data = """==> DOC001 <==
     1→First document
     2→with some content
     3→

==> DOC002 <==
    10→Second document
    11→with annotations ⟦test⟧
    12→and more text

==> DOC003 <==
Simple document without line numbers
Just plain text
"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def temp_index_dir():
    """Create a temporary directory for the index."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_indexer_initialization(temp_index_dir):
    """Test indexer initialization."""
    indexer = GenizahIndexer(temp_index_dir)
    assert indexer.index_dir == Path(temp_index_dir)
    assert indexer.schema is not None


def test_create_index(temp_index_dir):
    """Test index creation."""
    indexer = GenizahIndexer(temp_index_dir)
    idx = indexer.create_index()

    assert idx is not None
    assert index.exists_in(temp_index_dir)


def test_build_index(sample_transcription_file, temp_index_dir):
    """Test building the index from a transcription file."""
    indexer = GenizahIndexer(temp_index_dir)

    # Build the index
    doc_count = indexer.build_index(
        sample_transcription_file, strip_line_numbers=True, show_progress=False
    )

    assert doc_count == 3
    assert index.exists_in(temp_index_dir)


def test_index_content(sample_transcription_file, temp_index_dir):
    """Test that index contains the correct documents."""
    indexer = GenizahIndexer(temp_index_dir)
    indexer.build_index(sample_transcription_file, show_progress=False)

    # Open the index and search for documents
    idx = indexer.get_index()

    with idx.searcher() as searcher:
        # Check total documents
        assert searcher.doc_count_all() == 3

        # Check specific document
        doc = searcher.document(doc_id="DOC001")
        assert doc is not None
        assert "First document" in doc["content"]
        assert doc["line_count"] == 2  # Two non-empty lines
        assert doc["has_annotations"] is False

        # Check document with annotations
        doc2 = searcher.document(doc_id="DOC002")
        assert doc2 is not None
        assert "annotations" in doc2["content"]
        assert doc2["has_annotations"] is True

        # Check document without line numbers
        doc3 = searcher.document(doc_id="DOC003")
        assert doc3 is not None
        assert "Simple document" in doc3["content"]


def test_index_with_line_numbers(sample_transcription_file, temp_index_dir):
    """Test building index with line numbers preserved."""
    indexer = GenizahIndexer(temp_index_dir)
    indexer.build_index(sample_transcription_file, strip_line_numbers=False, show_progress=False)

    idx = indexer.get_index()

    with idx.searcher() as searcher:
        doc = searcher.document(doc_id="DOC001")
        # Line numbers should be present
        assert "1→" in doc["content"]


def test_get_index_not_exists(temp_index_dir):
    """Test getting index when it doesn't exist."""
    indexer = GenizahIndexer(temp_index_dir)

    with pytest.raises(FileNotFoundError):
        indexer.get_index()


def test_search_by_doc_id(sample_transcription_file, temp_index_dir):
    """Test searching by document ID."""
    indexer = GenizahIndexer(temp_index_dir)
    indexer.build_index(sample_transcription_file, show_progress=False)

    idx = indexer.get_index()

    with idx.searcher() as searcher:
        from whoosh.query import Term

        # Search for specific document ID
        query = Term("doc_id", "DOC002")
        results = searcher.search(query)

        assert len(results) == 1
        assert results[0]["doc_id"] == "DOC002"


def test_full_text_search(sample_transcription_file, temp_index_dir):
    """Test full-text search."""
    indexer = GenizahIndexer(temp_index_dir)
    indexer.build_index(sample_transcription_file, show_progress=False)

    idx = indexer.get_index()

    with idx.searcher() as searcher:
        from whoosh.qparser import QueryParser

        # Search for content
        parser = QueryParser("content", schema=indexer.schema)
        query = parser.parse("annotations")
        results = searcher.search(query)

        assert len(results) >= 1
        assert results[0]["doc_id"] == "DOC002"


def test_schema_fields():
    """Test that schema has the correct fields."""
    indexer = GenizahIndexer("dummy")
    schema = indexer.schema

    assert "doc_id" in schema
    assert "content" in schema
    assert "line_count" in schema
    assert "has_annotations" in schema


def test_index_reopen(sample_transcription_file, temp_index_dir):
    """Test reopening an existing index."""
    indexer = GenizahIndexer(temp_index_dir)
    indexer.build_index(sample_transcription_file, show_progress=False)

    # Create a new indexer instance with the same directory
    indexer2 = GenizahIndexer(temp_index_dir)
    idx = indexer2.create_index()

    # Should open existing index
    with idx.searcher() as searcher:
        assert searcher.doc_count_all() == 3
