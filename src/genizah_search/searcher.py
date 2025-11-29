"""Search functionality for the Genizah index."""

import re
import time
from dataclasses import dataclass
from typing import List, Optional

from whoosh import highlight, index
from whoosh.qparser import QueryParser
from whoosh.query import Term

from .logging_config import get_logger

logger = get_logger(__name__)


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

    def __init__(self, index_dir: str):
        """Initialize searcher with index directory.

        Args:
            index_dir: Path to the Whoosh index directory

        Raises:
            FileNotFoundError: If index doesn't exist
        """
        self.index_dir = index_dir
        logger.info(f"Initializing GenizahSearcher with index_dir: {index_dir}")

        if not index.exists_in(index_dir):
            logger.error(f"Index not found in {index_dir}")
            raise FileNotFoundError(
                f"Index not found in {index_dir}. "
                f"Please build the index first using the indexer."
            )
        self.idx = index.open_dir(index_dir)
        logger.info("GenizahSearcher initialized successfully")

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
        start_time = time.time()
        logger.info(
            f"Search request: type={search_type}, query='{query}', limit={limit}, "
            f"highlights={with_highlights}"
        )

        try:
            if search_type == "fulltext":
                results = self._fulltext_search(query, limit, with_highlights)
            elif search_type == "docid":
                results = self._docid_search(query, limit)
            elif search_type == "regex":
                results = self._regex_search(query, limit)
            else:
                logger.warning(f"Unknown search type requested: {search_type}")
                raise ValueError(
                    f"Unknown search type: {search_type}. " f"Use 'fulltext', 'docid', or 'regex'."
                )

            duration = time.time() - start_time
            logger.info(
                f"Search completed: type={search_type}, query='{query}', "
                f"results={len(results)}, duration={duration:.3f}s"
            )
            return results

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Search failed: type={search_type}, query='{query}', "
                f"error={type(e).__name__}: {e}, duration={duration:.3f}s"
            )
            raise

    def _fulltext_search(self, query: str, limit: int, with_highlights: bool) -> List[SearchResult]:
        """Perform full-text search.

        Args:
            query: Search query string
            limit: Maximum number of results
            with_highlights: Whether to include highlighted snippets

        Returns:
            List of SearchResult objects
        """
        logger.debug(f"Executing fulltext search: query='{query}', limit={limit}")
        results = []

        try:
            with self.idx.searcher() as searcher:
                # Create a parser for the content field
                parser = QueryParser("content", schema=self.idx.schema)
                q = parser.parse(query)

                # Search
                search_results = searcher.search(q, limit=limit)
                logger.debug(f"Fulltext search returned {len(search_results)} results")

                # Configure highlighter if needed
                if with_highlights:
                    search_results.highlighter = highlight.Highlighter(
                        fragmenter=highlight.ContextFragmenter(maxchars=200, surround=50)
                    )

                for hit in search_results:
                    # Get highlights if requested
                    highlights_text = None
                    if with_highlights:
                        highlights_text = hit.highlights("content", top=3)

                    results.append(
                        SearchResult(
                            doc_id=hit["doc_id"],
                            content=hit["content"],
                            line_count=hit["line_count"],
                            has_annotations=hit["has_annotations"],
                            score=hit.score,
                            highlights=highlights_text,
                        )
                    )

            return results

        except Exception as e:
            logger.error(f"Fulltext search error: {type(e).__name__}: {e}")
            raise

    def _docid_search(self, query: str, limit: int) -> List[SearchResult]:
        """Search by document ID (exact or partial match).

        Args:
            query: Document ID or partial ID
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        logger.debug(f"Executing docid search: query='{query}', limit={limit}")
        results = []

        try:
            with self.idx.searcher() as searcher:
                # Use wildcard search for partial matches
                if "*" not in query:
                    # Add wildcard to end for partial matches
                    query = f"*{query}*"

                # Parse the query
                parser = QueryParser("doc_id", schema=self.idx.schema)
                q = parser.parse(query)

                # Search
                search_results = searcher.search(q, limit=limit)
                logger.debug(f"Docid search returned {len(search_results)} results")

                for hit in search_results:
                    results.append(
                        SearchResult(
                            doc_id=hit["doc_id"],
                            content=hit["content"],
                            line_count=hit["line_count"],
                            has_annotations=hit["has_annotations"],
                            score=hit.score,
                        )
                    )

            return results

        except Exception as e:
            logger.error(f"Docid search error: {type(e).__name__}: {e}")
            raise

    def _regex_search(self, pattern: str, limit: int) -> List[SearchResult]:
        """Search using regex pattern.

        Args:
            pattern: Regular expression pattern
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        logger.debug(f"Executing regex search: pattern='{pattern}', limit={limit}")
        results = []

        try:
            regex = re.compile(pattern)
        except re.error as e:
            logger.warning(f"Invalid regex pattern: {pattern}, error: {e}")
            raise ValueError(f"Invalid regex pattern: {e}")

        try:
            with self.idx.searcher() as searcher:
                # We need to iterate through all documents for regex search
                count = 0
                docs_checked = 0
                for doc in searcher.documents():
                    docs_checked += 1
                    if count >= limit:
                        break

                    # Check if content matches the regex
                    if regex.search(doc["content"]):
                        results.append(
                            SearchResult(
                                doc_id=doc["doc_id"],
                                content=doc["content"],
                                line_count=doc["line_count"],
                                has_annotations=doc["has_annotations"],
                                score=1.0,  # Regex doesn't have relevance scoring
                            )
                        )
                        count += 1

                logger.debug(
                    f"Regex search completed: checked {docs_checked} documents, "
                    f"found {len(results)} matches"
                )

            return results

        except Exception as e:
            logger.error(f"Regex search error: {type(e).__name__}: {e}")
            raise

    def get_document(self, doc_id: str) -> Optional[SearchResult]:
        """Get a specific document by its exact ID.

        Args:
            doc_id: Exact document ID

        Returns:
            SearchResult object or None if not found
        """
        logger.debug(f"Retrieving document by exact ID: {doc_id}")

        try:
            with self.idx.searcher() as searcher:
                # Use Term query for exact match
                q = Term("doc_id", doc_id)
                results = searcher.search(q, limit=1)

                if results:
                    hit = results[0]
                    logger.info(f"Document found: {doc_id}")
                    return SearchResult(
                        doc_id=hit["doc_id"],
                        content=hit["content"],
                        line_count=hit["line_count"],
                        has_annotations=hit["has_annotations"],
                        score=hit.score,
                    )

            logger.info(f"Document not found: {doc_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {type(e).__name__}: {e}")
            raise

    def get_statistics(self) -> dict:
        """Get statistics about the index.

        Returns:
            Dictionary with index statistics
        """
        logger.debug("Retrieving index statistics")

        try:
            with self.idx.searcher() as searcher:
                total_docs = searcher.doc_count_all()

                # Count documents with annotations
                q = Term("has_annotations", True)
                annotated = searcher.search(q, limit=None)
                annotated_count = len(annotated)

                stats = {
                    "total_documents": total_docs,
                    "documents_with_annotations": annotated_count,
                    "index_version": self.idx.latest_generation(),
                }

                logger.info(
                    f"Index statistics: total={total_docs}, annotated={annotated_count}, "
                    f"version={stats['index_version']}"
                )

                return stats

        except Exception as e:
            logger.error(f"Error retrieving statistics: {type(e).__name__}: {e}")
            raise

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
        start_time = time.time()
        logger.info(
            f"Advanced search: query='{query}', annotations={has_annotations}, "
            f"min_lines={min_line_count}, max_lines={max_line_count}, limit={limit}"
        )

        results = []

        try:
            with self.idx.searcher() as searcher:
                # Build the query
                from whoosh.query import And, NumericRange

                queries = []

                # Add text query if provided
                if query:
                    parser = QueryParser("content", schema=self.idx.schema)
                    queries.append(parser.parse(query))

                # Add annotation filter
                if has_annotations is not None:
                    queries.append(Term("has_annotations", has_annotations))

                # Add line count filters
                if min_line_count is not None or max_line_count is not None:
                    start = min_line_count if min_line_count is not None else 0
                    # Use a very large number instead of infinity (Whoosh limitation)
                    end = max_line_count if max_line_count is not None else 999999
                    queries.append(NumericRange("line_count", start, end))

                # Combine queries
                if len(queries) == 1:
                    final_query = queries[0]
                else:
                    final_query = And(queries)

                # Search
                search_results = searcher.search(final_query, limit=limit)
                logger.debug(f"Advanced search returned {len(search_results)} results")

                for hit in search_results:
                    results.append(
                        SearchResult(
                            doc_id=hit["doc_id"],
                            content=hit["content"],
                            line_count=hit["line_count"],
                            has_annotations=hit["has_annotations"],
                            score=hit.score,
                        )
                    )

            duration = time.time() - start_time
            logger.info(f"Advanced search completed: {len(results)} results in {duration:.3f}s")

            return results

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Advanced search failed: {type(e).__name__}: {e}, duration={duration:.3f}s"
            )
            raise
