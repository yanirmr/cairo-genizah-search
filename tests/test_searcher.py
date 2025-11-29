"""Tests for the Genizah searcher module."""

import tempfile
from pathlib import Path

import pytest

from genizah_search.indexer import GenizahIndexer
from genizah_search.searcher import GenizahSearcher, SearchResult


@pytest.fixture
def sample_transcription_file():
    """Create a temporary transcription file."""
    data = """==> DOC001 <==
     1→Hebrew text שלום עולם
     2→More Hebrew content
     3→

==> DOC002 <==
    10→Arabic text السلام عليكم
    11→with annotations ⟦test annotation⟧
    12→and more text

==> DOC003 <==
Simple document without line numbers
Just plain text
Contains the word שבת

==> DOC004 <==
Long document with many lines
Line 2
Line 3
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10
"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def indexed_data(sample_transcription_file):
    """Create and populate a test database."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    temp_path = temp_file.name

    # Build the index
    indexer = GenizahIndexer(temp_path)
    indexer.build_index(sample_transcription_file, show_progress=False)
    indexer.db.close()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_searcher_initialization(indexed_data):
    """Test searcher initialization."""
    searcher = GenizahSearcher(indexed_data)
    assert searcher.db_path == Path(indexed_data)
    assert searcher.db is not None
    searcher.close()


def test_searcher_initialization_no_index():
    """Test searcher initialization with non-existent index."""
    with pytest.raises(FileNotFoundError):
        GenizahSearcher("nonexistent_index_dir")


def test_fulltext_search(indexed_data):
    """Test full-text search."""
    searcher = GenizahSearcher(indexed_data)

    # Search for Hebrew word
    results = searcher.search("שלום", search_type="fulltext")

    assert len(results) >= 1
    assert results[0].doc_id == "DOC001"
    assert "שלום" in results[0].content
    assert isinstance(results[0].score, float)

    searcher.close()


def test_fulltext_search_with_highlights(indexed_data):
    """Test full-text search with highlights."""
    searcher = GenizahSearcher(indexed_data)

    results = searcher.search("annotation", search_type="fulltext", with_highlights=True)

    assert len(results) >= 1
    assert results[0].doc_id == "DOC002"
    # Check that highlights are included
    assert results[0].highlights is not None

    searcher.close()


def test_fulltext_search_no_highlights(indexed_data):
    """Test full-text search without highlights."""
    searcher = GenizahSearcher(indexed_data)

    results = searcher.search("annotation", search_type="fulltext", with_highlights=False)

    assert len(results) >= 1
    assert results[0].highlights is None

    searcher.close()


def test_docid_search_exact(indexed_data):
    """Test document ID search with exact match."""
    searcher = GenizahSearcher(indexed_data)

    results = searcher.search("DOC002", search_type="docid")

    assert len(results) == 1
    assert results[0].doc_id == "DOC002"

    searcher.close()


def test_docid_search_partial(indexed_data):
    """Test document ID search with partial match."""
    searcher = GenizahSearcher(indexed_data)

    results = searcher.search("DOC", search_type="docid", limit=10)

    # Should match all documents starting with DOC
    assert len(results) >= 3
    doc_ids = [r.doc_id for r in results]
    assert "DOC001" in doc_ids
    assert "DOC002" in doc_ids
    assert "DOC003" in doc_ids

    searcher.close()


def test_regex_search(indexed_data):
    """Test regex search."""
    searcher = GenizahSearcher(indexed_data)

    # Search for documents containing "Line" followed by a digit
    results = searcher.search(r"Line \d+", search_type="regex", limit=10)

    assert len(results) >= 1
    assert results[0].doc_id == "DOC004"

    searcher.close()


def test_regex_search_invalid_pattern(indexed_data):
    """Test regex search with invalid pattern."""
    searcher = GenizahSearcher(indexed_data)

    with pytest.raises(ValueError):
        searcher.search("[invalid(regex", search_type="regex")

    searcher.close()


def test_get_document(indexed_data):
    """Test getting a specific document."""
    searcher = GenizahSearcher(indexed_data)

    doc = searcher.get_document("DOC003")

    assert doc is not None
    assert doc.doc_id == "DOC003"
    assert "Simple document" in doc.content
    assert doc.has_annotations is False

    searcher.close()


def test_get_document_not_found(indexed_data):
    """Test getting a non-existent document."""
    searcher = GenizahSearcher(indexed_data)

    doc = searcher.get_document("NONEXISTENT")

    assert doc is None

    searcher.close()


def test_get_statistics(indexed_data):
    """Test getting index statistics."""
    searcher = GenizahSearcher(indexed_data)

    stats = searcher.get_statistics()

    assert stats["total_documents"] == 4
    assert stats["documents_with_annotations"] == 1
    assert "last_updated" in stats

    searcher.close()


def test_advanced_search_with_annotations(indexed_data):
    """Test advanced search filtering by annotations."""
    searcher = GenizahSearcher(indexed_data)

    # Search for documents with annotations
    results = searcher.advanced_search("", has_annotations=True, limit=10)

    assert len(results) == 1
    assert results[0].doc_id == "DOC002"
    assert results[0].has_annotations is True

    searcher.close()


def test_advanced_search_without_annotations(indexed_data):
    """Test advanced search filtering for documents without annotations."""
    searcher = GenizahSearcher(indexed_data)

    # Search for documents without annotations
    results = searcher.advanced_search("", has_annotations=False, limit=10)

    assert len(results) >= 3
    for result in results:
        assert result.has_annotations is False

    searcher.close()


def test_advanced_search_line_count(indexed_data):
    """Test advanced search filtering by line count."""
    searcher = GenizahSearcher(indexed_data)

    # Search for documents with more than 5 lines
    results = searcher.advanced_search("", min_line_count=5, limit=10)

    assert len(results) >= 1
    for result in results:
        assert result.line_count >= 5

    searcher.close()


def test_advanced_search_line_count_range(indexed_data):
    """Test advanced search filtering by line count range."""
    searcher = GenizahSearcher(indexed_data)

    # Search for documents with 1-3 lines
    results = searcher.advanced_search("", min_line_count=1, max_line_count=3, limit=10)

    assert len(results) >= 1
    for result in results:
        assert 1 <= result.line_count <= 3

    searcher.close()


def test_advanced_search_combined_filters(indexed_data):
    """Test advanced search with combined filters."""
    searcher = GenizahSearcher(indexed_data)

    # Search for specific text with annotation filter
    results = searcher.advanced_search(
        "annotation", has_annotations=True, min_line_count=1, limit=10
    )

    assert len(results) >= 1
    assert results[0].doc_id == "DOC002"
    assert results[0].has_annotations is True

    searcher.close()


def test_search_limit(indexed_data):
    """Test that search respects the limit parameter."""
    searcher = GenizahSearcher(indexed_data)

    # Search with limit
    results = searcher.search("DOC", search_type="docid", limit=2)

    assert len(results) <= 2

    searcher.close()


def test_search_invalid_type(indexed_data):
    """Test search with invalid search type."""
    searcher = GenizahSearcher(indexed_data)

    with pytest.raises(ValueError):
        searcher.search("test", search_type="invalid_type")

    searcher.close()


def test_search_result_dataclass():
    """Test SearchResult dataclass."""
    result = SearchResult(
        doc_id="TEST001",
        content="Test content",
        line_count=5,
        has_annotations=True,
        score=1.5,
        highlights="Test highlights",
    )

    assert result.doc_id == "TEST001"
    assert result.content == "Test content"
    assert result.line_count == 5
    assert result.has_annotations is True
    assert result.score == 1.5
    assert result.highlights == "Test highlights"
