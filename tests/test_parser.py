"""Tests for the Genizah parser module."""

import tempfile
from pathlib import Path

import pytest

from genizah_search.parser import Document, GenizahParser


@pytest.fixture
def sample_data():
    """Sample transcription data for testing."""
    return """==> 990000412990205171_IE104549337_P000001_FL104549339 <==
     2→כתביך
     3→ת וכ
     4→אדלך
     5→][
     6→][
     7→][
     8→
==> 990000412990205171_IE104549337_P000002_FL104549340 <==
    10→]רת אללסאן ממא ילי אלהלקום דט'ר נגג מחדהא
    11→טרף אללסאן ולהם אלאסנאן ודת אלמרפיין ילצה טרף
    12→אללהאן באלאסנאן ברפק א זסצש מחלהא אלאסנאן [/
    13→]ף מחלהא אלשפתין בף אלמרפיין תשבק א
    14→פראניה מע אלסנאן אלפוקאניה ברפק / אלחרוף
    15→]אל מהא תנבדל בעצהא בבעץ מתל פזר . בזר
    16→]לם יעלץ ונחו דלך ⟦ותגי זואיד ונואיד⟧ ולאילי
    17→אן לא יקאל בדלך לאנה קד ימכן אן יך אלתבדיל
    18→עלי וגר[

==> TEST_SIMPLE_DOC <==
Simple text without line numbers
Second line
Third line
"""


@pytest.fixture
def temp_file(sample_data):
    """Create a temporary file with sample data."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(sample_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


def test_parser_initialization(temp_file):
    """Test parser initialization."""
    parser = GenizahParser(temp_file)
    assert parser.file_path == temp_file


def test_count_documents(temp_file):
    """Test document counting."""
    parser = GenizahParser(temp_file)
    count = parser.count_documents()
    assert count == 3


def test_parse_documents(temp_file):
    """Test parsing documents."""
    parser = GenizahParser(temp_file)
    documents = list(parser.parse())

    assert len(documents) == 3

    # Check first document
    doc1 = documents[0]
    assert doc1.doc_id == "990000412990205171_IE104549337_P000001_FL104549339"
    assert "כתביך" in doc1.content
    assert "אדלך" in doc1.content
    assert doc1.line_count == 6  # Non-empty lines (including the ][ lines)

    # Check second document
    doc2 = documents[1]
    assert doc2.doc_id == "990000412990205171_IE104549337_P000002_FL104549340"
    assert "אללסאן" in doc2.content
    assert doc2.has_annotations is True  # Contains ⟦⟧

    # Check third document (no line numbers)
    doc3 = documents[2]
    assert doc3.doc_id == "TEST_SIMPLE_DOC"
    assert "Simple text" in doc3.content
    assert doc3.line_count == 3


def test_line_number_stripping(temp_file):
    """Test that line numbers are stripped correctly."""
    parser = GenizahParser(temp_file)
    documents = list(parser.parse(strip_line_numbers=True))

    doc1 = documents[0]
    # Line numbers should be removed
    assert "2→" not in doc1.content
    assert "כתביך" in doc1.content

    doc2 = documents[1]
    assert "10→" not in doc2.content
    assert "אללסאן" in doc2.content


def test_no_line_number_stripping(temp_file):
    """Test parsing with line numbers preserved."""
    parser = GenizahParser(temp_file)
    documents = list(parser.parse(strip_line_numbers=False))

    doc1 = documents[0]
    # Line numbers should be preserved
    assert "2→" in doc1.content


def test_annotation_detection():
    """Test annotation detection."""
    # Document with annotations
    doc_with_annot = Document(
        doc_id="test1",
        content="Some text ⟦with annotations⟧ here",
        line_count=1,
        has_annotations=True,
    )
    assert doc_with_annot.has_annotations is True

    # Document with bracket annotations
    doc_with_brackets = Document(
        doc_id="test2", content="Text with ][ brackets", line_count=1, has_annotations=True
    )
    assert doc_with_brackets.has_annotations is True

    # Document without annotations
    doc_without_annot = Document(
        doc_id="test3", content="Plain text", line_count=1, has_annotations=False
    )
    assert doc_without_annot.has_annotations is False


def test_empty_document():
    """Test handling of empty documents."""
    data = """==> EMPTY_DOC <==

==> NEXT_DOC <==
Some content
"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(data)
        temp_path = f.name

    try:
        parser = GenizahParser(temp_path)
        documents = list(parser.parse())

        assert len(documents) == 2
        assert documents[0].doc_id == "EMPTY_DOC"
        assert documents[0].content == ""
        assert documents[0].line_count == 0

        assert documents[1].doc_id == "NEXT_DOC"
        assert documents[1].content == "Some content"
    finally:
        Path(temp_path).unlink()


def test_document_dataclass():
    """Test Document dataclass functionality."""
    doc = Document(doc_id="test_id", content="Test content", line_count=5, has_annotations=False)

    assert doc.doc_id == "test_id"
    assert doc.content == "Test content"
    assert doc.line_count == 5
    assert doc.has_annotations is False


def test_content_without_line_numbers():
    """Test the content_without_line_numbers property."""
    content_with_numbers = """     2→כתביך
     3→ת וכ
     4→אדלך"""

    doc = Document(doc_id="test", content=content_with_numbers, line_count=3, has_annotations=False)

    cleaned = doc.content_without_line_numbers
    assert "2→" not in cleaned
    assert "3→" not in cleaned
    assert "4→" not in cleaned
    assert "כתביך" in cleaned
    assert "ת וכ" in cleaned
    assert "אדלך" in cleaned
