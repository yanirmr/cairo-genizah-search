"""Tests for the CLI module."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from genizah_search.cli import main
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
"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def indexed_data(sample_transcription_file):
    """Create and populate a test index."""
    temp_dir = tempfile.mkdtemp()

    # Build the index
    indexer = GenizahIndexer(temp_dir)
    indexer.build_index(sample_transcription_file, show_progress=False)

    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_cli_fulltext_search(indexed_data):
    """Test CLI full-text search."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "שלום", "-i", indexed_data])

    assert result.exit_code == 0
    assert "DOC001" in result.output
    assert "Found" in result.output


def test_cli_docid_search(indexed_data):
    """Test CLI document ID search."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "DOC002", "-t", "docid", "-i", indexed_data])

    assert result.exit_code == 0
    assert "DOC002" in result.output


def test_cli_statistics(indexed_data):
    """Test CLI statistics display."""
    runner = CliRunner()
    result = runner.invoke(main, ["--stats", "-i", indexed_data, "-q", "dummy"])

    assert result.exit_code == 0
    assert "Index Statistics" in result.output
    assert "Total Documents" in result.output


def test_cli_with_limit(indexed_data):
    """Test CLI with result limit."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "DOC", "-t", "docid", "-i", indexed_data, "-l", "1"])

    assert result.exit_code == 0
    # Should only show 1 result
    assert "Result 1" in result.output
    assert "Result 2" not in result.output


def test_cli_no_results(indexed_data):
    """Test CLI when no results are found."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "nonexistenttext12345", "-i", indexed_data])

    assert result.exit_code == 0
    assert "No results found" in result.output


def test_cli_invalid_index():
    """Test CLI with invalid index path."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "test", "-i", "nonexistent_index"])

    assert result.exit_code != 0
    assert "Error" in result.output


def test_cli_full_content(indexed_data):
    """Test CLI with full content display."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "DOC001", "-t", "docid", "-i", indexed_data, "--full"])

    assert result.exit_code == 0
    assert "Content:" in result.output
    assert "שלום עולם" in result.output
