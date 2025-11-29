"""Tests for the Genizah indexer module."""

import tempfile
from pathlib import Path

import pytest

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
def temp_db_path():
    """Create a temporary database file path."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    temp_path = temp_file.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_indexer_initialization(temp_db_path):
    """Test indexer initialization."""
    indexer = GenizahIndexer(temp_db_path)
    assert indexer.db_path == Path(temp_db_path)
    assert indexer.db is not None


def test_indexer_with_directory_path():
    """Test indexer with directory path creates genizah.db."""
    import tempfile

    temp_dir = tempfile.mkdtemp()
    indexer = GenizahIndexer(temp_dir)

    assert indexer.db_path == Path(temp_dir) / "genizah.db"

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_create_database(temp_db_path):
    """Test database creation."""
    indexer = GenizahIndexer(temp_db_path)
    db = indexer.create_database()

    assert db is not None
    assert indexer.db_path.exists()

    db.close()


def test_build_index(sample_transcription_file, temp_db_path):
    """Test building the index from a transcription file."""
    indexer = GenizahIndexer(temp_db_path)

    # Build the index
    doc_count = indexer.build_index(
        sample_transcription_file, strip_line_numbers=True, show_progress=False
    )

    assert doc_count == 3
    assert indexer.db_path.exists()

    indexer.db.close()


def test_index_content(sample_transcription_file, temp_db_path):
    """Test that index contains the correct documents."""
    indexer = GenizahIndexer(temp_db_path)
    indexer.build_index(sample_transcription_file, show_progress=False)

    # Get the database
    db = indexer.get_database()
    cursor = db.conn.cursor()

    # Check total documents
    cursor.execute("SELECT COUNT(*) FROM documents")
    assert cursor.fetchone()[0] == 3

    # Check specific document
    cursor.execute("SELECT * FROM documents WHERE doc_id='DOC001'")
    row = cursor.fetchone()
    assert row is not None
    assert "First document" in row["content"]
    assert row["line_count"] == 2  # Two non-empty lines
    assert row["has_annotations"] == 0  # False

    # Check document with annotations
    cursor.execute("SELECT * FROM documents WHERE doc_id='DOC002'")
    row = cursor.fetchone()
    assert row is not None
    assert "annotations" in row["content"]
    assert row["has_annotations"] == 1  # True

    # Check document without line numbers
    cursor.execute("SELECT * FROM documents WHERE doc_id='DOC003'")
    row = cursor.fetchone()
    assert row is not None
    assert "Simple document" in row["content"]

    db.close()
    indexer.db.close()


def test_index_with_line_numbers(sample_transcription_file, temp_db_path):
    """Test building index with line numbers preserved."""
    indexer = GenizahIndexer(temp_db_path)
    indexer.build_index(sample_transcription_file, strip_line_numbers=False, show_progress=False)

    db = indexer.get_database()
    cursor = db.conn.cursor()

    cursor.execute("SELECT content FROM documents WHERE doc_id='DOC001'")
    row = cursor.fetchone()
    # Line numbers should be present
    assert "1→" in row["content"]

    db.close()
    indexer.db.close()


def test_get_database_not_exists():
    """Test getting database when it doesn't exist."""
    import tempfile

    # Use a path that doesn't exist (don't create the file)
    temp_path = str(Path(tempfile.gettempdir()) / "nonexistent_db_test.db")

    # Make sure it doesn't exist
    Path(temp_path).unlink(missing_ok=True)

    indexer = GenizahIndexer(temp_path)

    with pytest.raises(FileNotFoundError):
        indexer.get_database()


def test_fts_search(sample_transcription_file, temp_db_path):
    """Test FTS5 full-text search."""
    indexer = GenizahIndexer(temp_db_path)
    indexer.build_index(sample_transcription_file, show_progress=False)

    db = indexer.get_database()
    cursor = db.conn.cursor()

    # Search for content using FTS5
    cursor.execute(
        """
        SELECT doc_id FROM documents_fts
        WHERE documents_fts MATCH 'annotations'
    """
    )
    results = cursor.fetchall()

    assert len(results) >= 1
    assert results[0]["doc_id"] == "DOC002"

    db.close()
    indexer.db.close()


def test_database_schema():
    """Test that database has the correct schema."""
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    try:
        indexer = GenizahIndexer(temp_path)
        db = indexer.create_database()
        cursor = db.conn.cursor()

        # Check documents table exists with correct columns
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "doc_id" in columns
        assert "content" in columns
        assert "line_count" in columns
        assert "has_annotations" in columns

        # Check FTS table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents_fts'")
        assert cursor.fetchone() is not None

        db.close()
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_index_reopen(sample_transcription_file, temp_db_path):
    """Test reopening an existing database."""
    indexer = GenizahIndexer(temp_db_path)
    indexer.build_index(sample_transcription_file, show_progress=False)

    # Create a new indexer instance with the same path
    indexer2 = GenizahIndexer(temp_db_path)
    db = indexer2.get_database()
    cursor = db.conn.cursor()

    # Should open existing database
    cursor.execute("SELECT COUNT(*) FROM documents")
    assert cursor.fetchone()[0] == 3

    db.close()
    indexer.db.close()
    indexer2.db.close()


def test_metadata_tracking(sample_transcription_file, temp_db_path):
    """Test that metadata is tracked correctly."""
    indexer = GenizahIndexer(temp_db_path)
    indexer.build_index(sample_transcription_file, show_progress=False)

    db = indexer.get_database()
    cursor = db.conn.cursor()

    # Check document count metadata
    cursor.execute("SELECT value FROM index_metadata WHERE key='document_count'")
    row = cursor.fetchone()
    assert row is not None
    assert int(row[0]) == 3

    # Check last_updated metadata
    cursor.execute("SELECT value FROM index_metadata WHERE key='last_updated'")
    row = cursor.fetchone()
    assert row is not None

    db.close()
    indexer.db.close()


def test_fts_triggers(sample_transcription_file, temp_db_path):
    """Test that FTS triggers keep tables in sync."""
    indexer = GenizahIndexer(temp_db_path)
    indexer.build_index(sample_transcription_file, show_progress=False)

    db = indexer.get_database()
    cursor = db.conn.cursor()

    # Check that FTS table has same number of documents
    cursor.execute("SELECT COUNT(*) FROM documents")
    main_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents_fts")
    fts_count = cursor.fetchone()[0]

    assert main_count == fts_count == 3

    # Verify FTS content matches main table
    cursor.execute("SELECT doc_id, content FROM documents WHERE doc_id='DOC001'")
    main_doc = cursor.fetchone()

    cursor.execute("SELECT doc_id, content FROM documents_fts WHERE doc_id='DOC001'")
    fts_doc = cursor.fetchone()

    assert main_doc["content"] == fts_doc["content"]

    db.close()
    indexer.db.close()
