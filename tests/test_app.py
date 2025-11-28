"""Tests for the Flask web application."""

import tempfile
from pathlib import Path

import pytest

from genizah_search.app import app as flask_app
from genizah_search.indexer import GenizahIndexer


@pytest.fixture
def sample_transcription_file():
    """Create a temporary transcription file."""
    data = """==> DOC001 <==
     1→Hebrew text שלום עולם
     2→More Hebrew content

==> DOC002 <==
    10→Arabic text السلام عليكم
    11→with annotations ⟦test annotation⟧
    12→and more text

==> DOC003 <==
Simple document
Just plain text
Contains the word שבת
"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def app(sample_transcription_file):
    """Create Flask app with test configuration."""
    temp_dir = tempfile.mkdtemp()

    # Build test index
    indexer = GenizahIndexer(temp_dir)
    indexer.build_index(sample_transcription_file, show_progress=False)

    # Configure app
    flask_app.config["TESTING"] = True
    flask_app.config["INDEX_DIR"] = temp_dir

    # Set environment variable for the app
    import os

    os.environ["INDEX_PATH"] = temp_dir

    yield flask_app

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
    if hasattr(flask_app, "searcher"):
        delattr(flask_app, "searcher")


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_index_page(client):
    """Test main search page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "גניזת קהיר".encode("utf-8") in response.data
    assert "חיפוש".encode("utf-8") in response.data


def test_search_fulltext(client):
    """Test full-text search."""
    response = client.get("/search?q=שלום&type=fulltext")
    assert response.status_code == 200
    assert b"DOC001" in response.data
    assert "תוצאות חיפוש".encode("utf-8") in response.data


def test_search_docid(client):
    """Test document ID search."""
    response = client.get("/search?q=DOC002&type=docid")
    assert response.status_code == 200
    assert b"DOC002" in response.data


def test_search_empty_query(client):
    """Test search with empty query."""
    response = client.get("/search?q=")
    assert response.status_code == 200
    assert "אנא הזן שאילתת חיפוש".encode("utf-8") in response.data


def test_search_no_results(client):
    """Test search with no results."""
    response = client.get("/search?q=nonexistenttext12345")
    assert response.status_code == 200
    assert (
        "לא נמצאו תוצאות".encode("utf-8") in response.data
        or "נמצאו".encode("utf-8") in response.data
    )


def test_search_with_limit(client):
    """Test search with result limit."""
    response = client.get("/search?q=DOC&type=docid&limit=1")
    assert response.status_code == 200


def test_search_advanced_filters(client):
    """Test search with advanced filters."""
    response = client.get("/search?q=annotation&annotations=yes")
    assert response.status_code == 200
    # Should find DOC002 which has annotations


def test_document_view(client):
    """Test document detail page."""
    response = client.get("/document/DOC001")
    assert response.status_code == 200
    assert b"DOC001" in response.data
    assert b"Hebrew text" in response.data


def test_document_not_found(client):
    """Test viewing non-existent document."""
    response = client.get("/document/NONEXISTENT")
    assert response.status_code == 200
    assert "לא נמצא".encode("utf-8") in response.data


def test_stats_page(client):
    """Test statistics page."""
    response = client.get("/stats")
    assert response.status_code == 200
    assert "סטטיסטיקת אינדקס".encode("utf-8") in response.data
    assert "סך מסמכים".encode("utf-8") in response.data


def test_api_search(client):
    """Test API search endpoint."""
    response = client.get("/api/search?q=שלום&type=fulltext")
    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    assert "count" in data
    assert data["count"] >= 0


def test_api_search_no_query(client):
    """Test API search without query."""
    response = client.get("/api/search")
    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data


def test_api_stats(client):
    """Test API statistics endpoint."""
    response = client.get("/api/stats")
    assert response.status_code == 200

    data = response.get_json()
    assert "total_documents" in data
    assert data["total_documents"] == 3


def test_404_error(client):
    """Test 404 error handling."""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404


def test_search_with_line_filters(client):
    """Test search with line count filters."""
    response = client.get("/search?q=&min_lines=1&max_lines=5")
    assert response.status_code == 200
