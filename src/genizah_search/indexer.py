"""Indexer for building the SQLite FTS5 search database from Genizah transcriptions."""

import sys
from pathlib import Path

import click

from genizah_search.db import GenizahDatabase
from genizah_search.parser import GenizahParser


class GenizahIndexer:
    """Builds and manages the SQLite FTS5 search database for Genizah documents."""

    def __init__(self, db_path: str):
        """Initialize indexer with database path.

        Args:
            db_path: Path to SQLite database file or directory
                    If directory, uses genizah.db as filename
        """
        self.db_path = Path(db_path)

        # If path is a directory, use default filename
        if self.db_path.is_dir() or not self.db_path.suffix:
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.db_path = self.db_path / "genizah.db"
        else:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db = GenizahDatabase(str(self.db_path))

    def create_database(self) -> GenizahDatabase:
        """Create a new database or open existing one.

        Returns:
            GenizahDatabase object
        """
        self.db.connect()
        self.db.initialize_schema()
        return self.db

    def build_index(
        self,
        transcription_file: str,
        strip_line_numbers: bool = True,
        show_progress: bool = True,
    ) -> int:
        """Build the search database from transcription file.

        Args:
            transcription_file: Path to GenizaTranscriptions.txt
            strip_line_numbers: Whether to strip line numbers from content
            show_progress: Whether to show progress information

        Returns:
            Number of documents indexed
        """
        parser = GenizahParser(transcription_file)
        db = self.create_database()
        conn = db.connect()

        # Get total document count for progress
        if show_progress:
            total_docs = parser.count_documents()
            click.echo(f"Indexing {total_docs} documents...")

        cursor = conn.cursor()
        doc_count = 0

        # Use transaction for better performance
        cursor.execute("BEGIN TRANSACTION")

        try:
            for doc in parser.parse(strip_line_numbers=strip_line_numbers):
                # Insert document (triggers will update FTS table automatically)
                cursor.execute(
                    """
                    INSERT INTO documents (doc_id, content, line_count, has_annotations)
                    VALUES (?, ?, ?, ?)
                """,
                    (doc.doc_id, doc.content, doc.line_count, doc.has_annotations),
                )

                doc_count += 1

                # Show progress every 100 documents
                if show_progress and doc_count % 100 == 0:
                    click.echo(f"Indexed {doc_count}/{total_docs} documents...", nl=False)
                    click.echo("\r", nl=False)  # Carriage return to overwrite line

                # Commit every 1000 documents to avoid huge transactions
                if doc_count % 1000 == 0:
                    conn.commit()
                    cursor.execute("BEGIN TRANSACTION")

            # Final commit
            conn.commit()

            # Update metadata
            cursor.execute(
                """
                INSERT OR REPLACE INTO index_metadata (key, value)
                VALUES ('document_count', ?)
            """,
                (str(doc_count),),
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO index_metadata (key, value)
                VALUES ('last_updated', datetime('now'))
            """
            )

            conn.commit()

            # Optimize FTS index
            if show_progress:
                click.echo("\nOptimizing search index...")
            cursor.execute("INSERT INTO documents_fts(documents_fts) VALUES('optimize')")
            conn.commit()

            if show_progress:
                click.echo(f"Successfully indexed {doc_count} documents!")

        except Exception as e:
            conn.rollback()
            raise e

        return doc_count

    def get_database(self) -> GenizahDatabase:
        """Get the existing database.

        Returns:
            GenizahDatabase object

        Raises:
            FileNotFoundError: If database doesn't exist
        """
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                f"Please build the index first using the indexer."
            )

        db = GenizahDatabase(str(self.db_path))
        db.connect()
        return db


@click.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to GenizaTranscriptions.txt",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    required=True,
    type=click.Path(),
    help="Path to SQLite database file or directory (default filename: genizah.db)",
)
@click.option(
    "--keep-line-numbers",
    is_flag=True,
    help="Keep line numbers in indexed content (default: strip them)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress progress output",
)
def main(input_file: str, output_path: str, keep_line_numbers: bool, quiet: bool):
    """Build the Genizah search database from transcription file.

    Example:
        genizah-index -i GenizaTranscriptions.txt -o index/genizah.db
    """
    try:
        indexer = GenizahIndexer(output_path)
        strip_line_numbers = not keep_line_numbers
        show_progress = not quiet

        indexer.build_index(
            input_file, strip_line_numbers=strip_line_numbers, show_progress=show_progress
        )

        if not quiet:
            db_size = indexer.db_path.stat().st_size
            click.echo(f"Database size: {db_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
