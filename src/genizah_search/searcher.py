"""Search functionality for the Genizah index."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from genizah_search.db import GenizahDatabase


@dataclass
class SearchResult:
    """Represents a single search result."""

    doc_id: str
    content: str
    line_count: int
    has_annotations: bool
    score: float
    highlights: Optional[str] = None


class GenizahSearcher:
    """Search engine for Genizah documents."""

    def __init__(self, db_path: str):
        """Initialize searcher with database path.

        Args:
            db_path: Path to the SQLite database file or directory

        Raises:
            FileNotFoundError: If database doesn't exist
        """
        self.db_path = Path(db_path)

        # If path is a directory, look for genizah.db
        if self.db_path.is_dir():
            self.db_path = self.db_path / "genizah.db"

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                f"Please build the index first using the indexer."
            )

        self.db = GenizahDatabase(str(self.db_path), enable_wal=True)
        self.db.connect()

    def search(
        self,
        query: str,
        search_type: str = "fulltext",
        limit: int = 10,
        with_highlights: bool = True,
    ) -> List[SearchResult]:
        """Search the index.

        Args:
            query: Search query string
            search_type: Type of search - 'fulltext', 'docid', 'regex'
            limit: Maximum number of results to return
            with_highlights: Whether to include highlighted snippets

        Returns:
            List of SearchResult objects
        """
        if search_type == "fulltext":
            return self._fulltext_search(query, limit, with_highlights)
        elif search_type == "docid":
            return self._docid_search(query, limit)
        elif search_type == "regex":
            return self._regex_search(query, limit)
        else:
            raise ValueError(
                f"Unknown search type: {search_type}. " f"Use 'fulltext', 'docid', or 'regex'."
            )

    def _fulltext_search(self, query: str, limit: int, with_highlights: bool) -> List[SearchResult]:
        """Perform full-text search using FTS5.

        Args:
            query: Search query string
            limit: Maximum number of results
            with_highlights: Whether to include highlighted snippets

        Returns:
            List of SearchResult objects
        """
        results = []
        cursor = self.db.conn.cursor()

        # Convert query to FTS5 format (mostly pass-through, Whoosh and FTS5 are similar)
        fts_query = self._convert_query_to_fts5(query)

        # Build SQL query with BM25 ranking
        if with_highlights:
            # Use snippet() for highlighting
            sql = """
                SELECT d.doc_id, d.content, d.line_count, d.has_annotations,
                       bm25(documents_fts) as score,
                       snippet(documents_fts, 1, '<b>', '</b>', '...', 15) as snippet
                FROM documents d
                JOIN documents_fts ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """
            cursor.execute(sql, (fts_query, limit))
        else:
            sql = """
                SELECT d.doc_id, d.content, d.line_count, d.has_annotations,
                       bm25(documents_fts) as score
                FROM documents d
                JOIN documents_fts ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """
            cursor.execute(sql, (fts_query, limit))

        for row in cursor.fetchall():
            highlights_text = None
            if with_highlights:
                # Extract snippet from query result
                highlights_text = row["snippet"] if row["snippet"] else None

            results.append(
                SearchResult(
                    doc_id=row["doc_id"],
                    content=row["content"],
                    line_count=row["line_count"],
                    has_annotations=bool(row["has_annotations"]),
                    score=abs(row["score"]),  # BM25 returns negative scores
                    highlights=highlights_text,
                )
            )

        return results

    def _convert_query_to_fts5(self, query: str) -> str:
        """Convert query to FTS5 format.

        Whoosh and FTS5 query syntax are similar, so mostly pass through.
        Both support AND, OR, NOT, wildcards (*).

        Args:
            query: Original query string

        Returns:
            FTS5-compatible query string
        """
        # FTS5 and Whoosh query syntax are very similar
        # Both support: AND, OR, NOT, wildcards (*)
        # Main difference: FTS5 uses double quotes for phrases
        return query

    def _docid_search(self, query: str, limit: int) -> List[SearchResult]:
        """Search by document ID (exact or partial match).

        Args:
            query: Document ID or partial ID
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []
        cursor = self.db.conn.cursor()

        # Use LIKE for partial matching
        like_pattern = f"%{query}%"

        sql = """
            SELECT doc_id, content, line_count, has_annotations
            FROM documents
            WHERE doc_id LIKE ?
            LIMIT ?
        """
        cursor.execute(sql, (like_pattern, limit))

        for row in cursor.fetchall():
            results.append(
                SearchResult(
                    doc_id=row["doc_id"],
                    content=row["content"],
                    line_count=row["line_count"],
                    has_annotations=bool(row["has_annotations"]),
                    score=1.0,  # No relevance scoring for ID search
                )
            )

        return results

    def _regex_search(self, pattern: str, limit: int) -> List[SearchResult]:
        """Search using regex pattern.

        Args:
            pattern: Regular expression pattern
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        cursor = self.db.conn.cursor()

        # Stream all documents and filter with regex
        # This is O(N) but unavoidable for regex search
        cursor.execute("SELECT doc_id, content, line_count, has_annotations FROM documents")

        count = 0
        for row in cursor:
            if count >= limit:
                break

            # Check if content matches the regex
            if regex.search(row["content"]):
                results.append(
                    SearchResult(
                        doc_id=row["doc_id"],
                        content=row["content"],
                        line_count=row["line_count"],
                        has_annotations=bool(row["has_annotations"]),
                        score=1.0,  # Regex doesn't have relevance scoring
                    )
                )
                count += 1

        return results

    def get_document(self, doc_id: str) -> Optional[SearchResult]:
        """Get a specific document by its exact ID.

        Args:
            doc_id: Exact document ID

        Returns:
            SearchResult object or None if not found
        """
        cursor = self.db.conn.cursor()

        sql = """
            SELECT doc_id, content, line_count, has_annotations
            FROM documents
            WHERE doc_id = ?
        """
        cursor.execute(sql, (doc_id,))
        row = cursor.fetchone()

        if row:
            return SearchResult(
                doc_id=row["doc_id"],
                content=row["content"],
                line_count=row["line_count"],
                has_annotations=bool(row["has_annotations"]),
                score=1.0,
            )

        return None

    def get_statistics(self) -> dict:
        """Get statistics about the index.

        Returns:
            Dictionary with index statistics
        """
        cursor = self.db.conn.cursor()

        # Get total document count
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]

        # Count documents with annotations
        cursor.execute("SELECT COUNT(*) FROM documents WHERE has_annotations = 1")
        annotated_count = cursor.fetchone()[0]

        # Get metadata
        cursor.execute("SELECT value FROM index_metadata WHERE key='last_updated'")
        last_updated_row = cursor.fetchone()
        last_updated = last_updated_row[0] if last_updated_row else None

        return {
            "total_documents": total_docs,
            "documents_with_annotations": annotated_count,
            "last_updated": last_updated,
        }

    def advanced_search(
        self,
        query: str,
        has_annotations: Optional[bool] = None,
        min_line_count: Optional[int] = None,
        max_line_count: Optional[int] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """Perform advanced search with filters.

        Args:
            query: Search query string
            has_annotations: Filter by annotation presence (True/False/None)
            min_line_count: Minimum number of lines
            max_line_count: Maximum number of lines
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []
        cursor = self.db.conn.cursor()

        # Build dynamic WHERE clause
        conditions = []
        params = []

        # Add text query if provided
        if query:
            fts_query = self._convert_query_to_fts5(query)
            conditions.append("documents_fts MATCH ?")
            params.append(fts_query)

        # Add annotation filter
        if has_annotations is not None:
            conditions.append("d.has_annotations = ?")
            params.append(1 if has_annotations else 0)

        # Add line count filters
        if min_line_count is not None:
            conditions.append("d.line_count >= ?")
            params.append(min_line_count)

        if max_line_count is not None:
            conditions.append("d.line_count <= ?")
            params.append(max_line_count)

        # Build SQL query
        if query:
            # Use FTS5 for text search
            sql = f"""
                SELECT d.doc_id, d.content, d.line_count, d.has_annotations,
                       bm25(documents_fts) as score
                FROM documents d
                JOIN documents_fts ON d.rowid = documents_fts.rowid
                WHERE {' AND '.join(conditions)}
                ORDER BY score
                LIMIT ?
            """
        else:
            # No text search, just filters
            sql = f"""
                SELECT doc_id, content, line_count, has_annotations,
                       0.0 as score
                FROM documents d
                WHERE {' AND '.join(conditions) if conditions else '1=1'}
                LIMIT ?
            """

        params.append(limit)
        cursor.execute(sql, params)

        for row in cursor.fetchall():
            results.append(
                SearchResult(
                    doc_id=row["doc_id"],
                    content=row["content"],
                    line_count=row["line_count"],
                    has_annotations=bool(row["has_annotations"]),
                    score=abs(row["score"]) if query else 1.0,
                )
            )

        return results

    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
