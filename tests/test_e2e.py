"""End-to-end tests for the Cairo Genizah Search application.

This test suite validates the entire workflow from raw data file through
parsing, indexing, searching, and web interface interaction.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from genizah_search.app import app as flask_app
from genizah_search.indexer import GenizahIndexer
from genizah_search.parser import GenizahParser
from genizah_search.searcher import GenizahSearcher


@pytest.fixture(scope="module")
def sample_data_file():
    """Get the path to the sample data file."""
    test_dir = Path(__file__).parent
    sample_file = test_dir / "sample_genizah_data.txt"
    assert sample_file.exists(), f"Sample data file not found: {sample_file}"
    return str(sample_file)


@pytest.fixture(scope="module")
def test_index_dir(sample_data_file):
    """Create a test index from the sample data file."""
    # Create temporary directory for index
    temp_dir = tempfile.mkdtemp(prefix="genizah_e2e_test_")

    # Build index from sample data
    indexer = GenizahIndexer(temp_dir)
    indexer.build_index(sample_data_file, show_progress=False)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def searcher(test_index_dir):
    """Create a searcher instance."""
    return GenizahSearcher(test_index_dir)


@pytest.fixture
def app(test_index_dir):
    """Create Flask app with test configuration."""
    import os

    # Configure app
    flask_app.config["TESTING"] = True
    flask_app.config["INDEX_DIR"] = test_index_dir

    # Set environment variable for the app
    os.environ["INDEX_PATH"] = test_index_dir

    yield flask_app

    # Cleanup
    if hasattr(flask_app, "searcher"):
        delattr(flask_app, "searcher")


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestE2EDataParsing:
    """Test the parsing of sample data file."""

    def test_parse_sample_data(self, sample_data_file):
        """Test that sample data can be parsed correctly."""
        parser = GenizahParser(sample_data_file)
        documents = list(parser.parse())

        # Should have 11 documents based on our sample
        assert len(documents) == 11

        # Check first document
        assert documents[0].doc_id == "990000412990205171_IE104549337_P000001_FL104549339"
        assert "כתביך" in documents[0].content
        assert documents[0].line_count >= 1

    def test_parse_with_annotations(self, sample_data_file):
        """Test parsing detects annotations correctly."""
        parser = GenizahParser(sample_data_file)
        documents = list(parser.parse())

        # Find documents with annotations
        docs_with_annotations = [doc for doc in documents if doc.has_annotations]
        assert len(docs_with_annotations) > 0

        # Check specific documents we know have annotations
        talmud_doc = next((doc for doc in documents if "TALMUD" in doc.doc_id), None)
        assert talmud_doc is not None
        assert talmud_doc.has_annotations

    def test_parse_different_document_types(self, sample_data_file):
        """Test parsing handles different document types."""
        parser = GenizahParser(sample_data_file)
        documents = list(parser.parse())

        # Check we have the test documents
        doc_ids = [doc.doc_id for doc in documents]
        assert "TEST_DOCUMENT_WITH_MISHNAH" in doc_ids
        assert "TEST_DOCUMENT_WITH_TALMUD" in doc_ids
        assert "JUDEO_ARABIC_LETTER" in doc_ids

    def test_document_count(self, sample_data_file):
        """Test counting documents in file."""
        parser = GenizahParser(sample_data_file)
        count = parser.count_documents()
        assert count == 11


class TestE2EIndexing:
    """Test the indexing of sample data."""

    def test_index_created(self, test_index_dir):
        """Test that index was created successfully."""
        index_path = Path(test_index_dir)
        assert index_path.exists()
        assert index_path.is_dir()

        # Check for SQLite database file
        db_file = index_path / "genizah.db"
        assert db_file.exists(), "No database file found"

    def test_index_statistics(self, test_index_dir):
        """Test index statistics."""
        searcher = GenizahSearcher(test_index_dir)
        stats = searcher.get_statistics()

        assert stats["total_documents"] == 11
        assert "last_updated" in stats

        searcher.close()

    def test_index_contains_all_documents(self, test_index_dir, sample_data_file):
        """Test that index contains all documents from source file."""
        parser = GenizahParser(sample_data_file)
        source_docs = list(parser.parse())
        source_doc_ids = {doc.doc_id for doc in source_docs}

        searcher = GenizahSearcher(test_index_dir)

        # Verify each document is searchable by ID
        for doc_id in source_doc_ids:
            result = searcher.get_document(doc_id)
            assert result is not None
            assert result.doc_id == doc_id


class TestE2ESearching:
    """Test search functionality end-to-end."""

    def test_fulltext_search_hebrew(self, searcher):
        """Test full-text search with Hebrew terms."""
        results = searcher.search("משנה", search_type="fulltext", limit=10)
        assert len(results) > 0

        # Check we found the Mishnah document
        mishnah_docs = [r for r in results if "MISHNAH" in r.doc_id]
        assert len(mishnah_docs) > 0

    def test_fulltext_search_judeo_arabic(self, searcher):
        """Test full-text search with Judeo-Arabic terms."""
        results = searcher.search("אללה", search_type="fulltext", limit=10)
        assert len(results) > 0

        # Should find the Judeo-Arabic letter
        letter_docs = [r for r in results if "JUDEO_ARABIC" in r.doc_id]
        assert len(letter_docs) > 0

    def test_fulltext_search_common_term(self, searcher):
        """Test full-text search with common term across documents."""
        results = searcher.search("אלחרוף", search_type="fulltext", limit=20)
        # This term appears in multiple documents
        assert len(results) >= 2

    def test_search_by_document_id(self, searcher):
        """Test searching by document ID."""
        doc_id = "TEST_DOCUMENT_WITH_MISHNAH"
        results = searcher.search(doc_id, search_type="docid", limit=1)

        assert len(results) == 1
        assert results[0].doc_id == doc_id
        assert "משנה" in results[0].content

    def test_search_by_partial_document_id(self, searcher):
        """Test searching with partial document ID."""
        results = searcher.search("IE104549337", search_type="docid", limit=10)
        # Should find all documents with this IE number
        assert len(results) >= 3

    def test_search_with_annotations_filter(self, searcher):
        """Test searching with annotation filter."""
        results = searcher.advanced_search("", has_annotations=True, limit=20)
        # All results should have annotations
        for result in results:
            assert result.has_annotations

    def test_search_with_line_count_filter(self, searcher):
        """Test searching with line count filters."""
        results = searcher.advanced_search("", min_line_count=10, max_line_count=30, limit=20)
        # All results should be within the line count range
        for result in results:
            assert 10 <= result.line_count <= 30

    def test_search_no_results(self, searcher):
        """Test search that returns no results."""
        results = searcher.search("xyznotexistingterm999", search_type="fulltext", limit=10)
        assert len(results) == 0

    def test_search_empty_query(self, searcher):
        """Test search with empty query and filters returns results."""
        # Empty query but with a filter should return documents matching the filter
        results = searcher.advanced_search("", min_line_count=1, limit=20)
        # Should return documents with at least 1 line
        assert len(results) > 0


class TestE2EWebInterface:
    """Test the web interface end-to-end."""

    def test_homepage_loads(self, client):
        """Test that homepage loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "גניזת קהיר".encode("utf-8") in response.data
        assert "חיפוש".encode("utf-8") in response.data

    def test_search_page_hebrew_query(self, client):
        """Test search page with Hebrew query."""
        response = client.get("/search?q=משנה&type=fulltext")
        assert response.status_code == 200
        assert b"TEST_DOCUMENT_WITH_MISHNAH" in response.data

    def test_search_page_docid_query(self, client):
        """Test search page with document ID query."""
        response = client.get("/search?q=TEST_DOCUMENT_WITH_TALMUD&type=docid")
        assert response.status_code == 200
        assert b"TEST_DOCUMENT_WITH_TALMUD" in response.data
        assert "תנו רבנן".encode("utf-8") in response.data

    def test_search_with_filters(self, client):
        """Test search with various filters."""
        response = client.get("/search?q=&type=fulltext&annotations=yes&min_lines=5&max_lines=20")
        assert response.status_code == 200
        # Should return some results
        assert "תוצאות".encode("utf-8") in response.data or b"results" in response.data

    def test_document_detail_page(self, client):
        """Test viewing a specific document."""
        response = client.get("/document/TEST_DOCUMENT_WITH_MISHNAH")
        assert response.status_code == 200
        assert b"TEST_DOCUMENT_WITH_MISHNAH" in response.data
        assert "משנה מסכת שבת".encode("utf-8") in response.data
        assert "יציאות השבת".encode("utf-8") in response.data

    def test_document_not_found(self, client):
        """Test viewing non-existent document."""
        response = client.get("/document/NONEXISTENT_DOCUMENT_ID_12345")
        assert response.status_code == 200
        assert "לא נמצא".encode("utf-8") in response.data

    def test_stats_page(self, client):
        """Test statistics page."""
        response = client.get("/stats")
        assert response.status_code == 200
        assert "סטטיסטיקת".encode("utf-8") in response.data
        # Should show 11 documents
        assert b"11" in response.data

    def test_api_search_endpoint(self, client):
        """Test API search endpoint."""
        response = client.get("/api/search?q=משנה&type=fulltext")
        assert response.status_code == 200

        data = response.get_json()
        assert "results" in data
        assert "count" in data
        assert data["count"] > 0

        # Check result structure
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "doc_id" in result
            assert "content" in result
            assert "line_count" in result

    def test_api_search_with_limit(self, client):
        """Test API search with result limit."""
        response = client.get("/api/search?q=אלחרוף&type=fulltext&limit=5")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data["results"]) <= 5

    def test_api_stats_endpoint(self, client):
        """Test API statistics endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200

        data = response.get_json()
        assert data["total_documents"] == 11

    def test_api_error_handling(self, client):
        """Test API error handling."""
        # Missing query parameter
        response = client.get("/api/search")
        assert response.status_code == 400

        data = response.get_json()
        assert "error" in data

    def test_search_pagination(self, client):
        """Test search with different limits."""
        # Search with small limit
        response = client.get("/search?q=&type=fulltext&limit=3")
        assert response.status_code == 200

        # Search with larger limit
        response = client.get("/search?q=&type=fulltext&limit=20")
        assert response.status_code == 200


class TestE2ECompleteWorkflow:
    """Test complete workflows from start to finish."""

    def test_workflow_find_mishnah_documents(self, client):
        """Test workflow: User searches for Mishnah documents."""
        # Step 1: Load homepage
        response = client.get("/")
        assert response.status_code == 200

        # Step 2: Search for Mishnah
        response = client.get("/search?q=משנה&type=fulltext")
        assert response.status_code == 200
        assert b"TEST_DOCUMENT_WITH_MISHNAH" in response.data

        # Step 3: View document details
        response = client.get("/document/TEST_DOCUMENT_WITH_MISHNAH")
        assert response.status_code == 200
        assert "יציאות השבת".encode("utf-8") in response.data

    def test_workflow_find_documents_with_annotations(self, client, searcher):
        """Test workflow: User finds all documents with annotations."""
        # Step 1: Search with annotation filter
        results = searcher.advanced_search("", has_annotations=True, limit=20)
        assert len(results) > 0

        # Step 2: Verify all have annotations
        for result in results:
            assert result.has_annotations

        # Step 3: View one via web interface
        if results:
            doc_id = results[0].doc_id
            response = client.get(f"/document/{doc_id}")
            assert response.status_code == 200

    def test_workflow_search_by_collection_number(self, client):
        """Test workflow: User searches by collection number."""
        # Search for documents from a specific collection (IE number)
        response = client.get("/search?q=IE104549337&type=docid")
        assert response.status_code == 200

        # Should find multiple documents from this collection
        # Based on our sample data, there are 3 documents with this IE number
        assert "990000412990205171_IE104549337".encode("utf-8") in response.data

    def test_workflow_api_integration(self, client):
        """Test workflow: External tool uses API."""
        # Step 1: Get statistics
        response = client.get("/api/stats")
        data = response.get_json()
        total_docs = data["total_documents"]
        assert total_docs == 11

        # Step 2: Search via API
        response = client.get("/api/search?q=שבת&type=fulltext")
        data = response.get_json()
        assert data["count"] > 0

        # Step 3: Get specific document via API search
        if data["results"]:
            doc_id = data["results"][0]["doc_id"]
            response = client.get(f"/api/search?q={doc_id}&type=docid")
            data = response.get_json()
            assert data["count"] >= 1


class TestE2ERobustness:
    """Test system robustness and edge cases."""

    def test_special_characters_in_search(self, client):
        """Test search handles special characters."""
        # Test with annotation markers
        response = client.get("/search?q=⟦&type=fulltext")
        assert response.status_code == 200

        # Test with brackets
        response = client.get("/search?q=][&type=fulltext")
        assert response.status_code == 200

    def test_very_long_query(self, client):
        """Test system handles very long queries."""
        long_query = "א" * 1000
        response = client.get(f"/search?q={long_query}&type=fulltext")
        assert response.status_code == 200

    def test_concurrent_searches(self, searcher):
        """Test multiple searches work correctly."""
        # Simulate multiple searches
        results1 = searcher.search("משנה", search_type="fulltext", limit=10)
        results2 = searcher.search("TEST_DOCUMENT", search_type="docid", limit=10)
        results3 = searcher.search("אללה", search_type="fulltext", limit=10)

        # All should succeed
        assert isinstance(results1, list)
        assert isinstance(results2, list)
        assert isinstance(results3, list)

    def test_empty_filter_combinations(self, client):
        """Test various empty filter combinations."""
        # Empty query with filters
        response = client.get("/search?q=&min_lines=100&max_lines=200")
        assert response.status_code == 200

        # Only annotation filter
        response = client.get("/search?q=&annotations=yes")
        assert response.status_code == 200

    def test_rtl_text_handling(self, client):
        """Test that RTL text is handled correctly throughout."""
        # Hebrew search
        response = client.get("/search?q=משנה&type=fulltext")
        assert response.status_code == 200
        assert "משנה".encode("utf-8") in response.data

        # Judeo-Arabic search
        response = client.get("/search?q=בשם&type=fulltext")
        assert response.status_code == 200
