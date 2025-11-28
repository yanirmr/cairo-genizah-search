"""Parser for Cairo Genizah transcription files.

This module handles parsing of the GenizaTranscriptions.txt file format,
extracting individual documents with their IDs and content.
"""

import re
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class Document:
    """Represents a single Genizah document."""

    doc_id: str
    content: str
    line_count: int
    has_annotations: bool

    @property
    def content_without_line_numbers(self) -> str:
        """Return content with line numbers stripped if present."""
        lines = self.content.split("\n")
        cleaned_lines = []

        for line in lines:
            # Check if line starts with line number format: spaces + number + tab
            match = re.match(r"^\s+\d+→", line)
            if match:
                # Remove the line number prefix
                cleaned_line = line[match.end() :]
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)


class GenizahParser:
    """Parser for Genizah transcription files."""

    # Pattern to match document header: ==> DOCUMENT_ID <==
    DOCUMENT_HEADER_PATTERN = re.compile(r"^==> (.+?) <==\s*$")

    # Pattern to detect annotations
    ANNOTATION_PATTERN = re.compile(r"⟦|⟧|\]\[")

    def __init__(self, file_path: str):
        """Initialize parser with file path.

        Args:
            file_path: Path to the GenizaTranscriptions.txt file
        """
        self.file_path = file_path

    def parse(self, strip_line_numbers: bool = True) -> Iterator[Document]:
        """Parse the transcription file and yield documents.

        Args:
            strip_line_numbers: Whether to strip line numbers from content

        Yields:
            Document objects containing parsed data
        """
        current_doc_id: Optional[str] = None
        current_lines: list[str] = []

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                # Check if this is a document header
                header_match = self.DOCUMENT_HEADER_PATTERN.match(line)

                if header_match:
                    # If we were processing a document, yield it
                    if current_doc_id is not None:
                        yield self._create_document(
                            current_doc_id, current_lines, strip_line_numbers
                        )

                    # Start new document
                    current_doc_id = header_match.group(1)
                    current_lines = []
                else:
                    # Add line to current document (skip empty lines at start)
                    if current_doc_id is not None:
                        current_lines.append(line)

            # Don't forget the last document
            if current_doc_id is not None:
                yield self._create_document(current_doc_id, current_lines, strip_line_numbers)

    def _create_document(self, doc_id: str, lines: list[str], strip_line_numbers: bool) -> Document:
        """Create a Document object from parsed data.

        Args:
            doc_id: Document identifier
            lines: List of content lines
            strip_line_numbers: Whether to strip line numbers

        Returns:
            Document object
        """
        # Optionally strip line numbers from each line before processing
        if strip_line_numbers:
            processed_lines = []
            for line in lines:
                # Check if line starts with line number format: spaces + number + →
                match = re.match(r"^\s+\d+→", line)
                if match:
                    # Remove the line number prefix
                    processed_lines.append(line[match.end() :])
                else:
                    processed_lines.append(line)
            lines = processed_lines

        # Join lines and strip leading/trailing whitespace from the entire content
        content = "\n".join(lines).strip()

        # Count non-empty lines
        line_count = sum(1 for line in lines if line.strip())

        # Check for annotations
        has_annotations = bool(self.ANNOTATION_PATTERN.search(content))

        # Create document
        doc = Document(
            doc_id=doc_id,
            content=content,
            line_count=line_count,
            has_annotations=has_annotations,
        )

        return doc

    def count_documents(self) -> int:
        """Count total number of documents in the file.

        Returns:
            Number of documents
        """
        count = 0
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if self.DOCUMENT_HEADER_PATTERN.match(line):
                    count += 1
        return count
