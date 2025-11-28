"""Indexer for building the Whoosh search index from Genizah transcriptions."""

import sys
from pathlib import Path

import click
from whoosh import index
from whoosh.fields import BOOLEAN, ID, NUMERIC, TEXT, Schema

from genizah_search.parser import GenizahParser


class GenizahIndexer:
    """Builds and manages the Whoosh search index for Genizah documents."""

    def __init__(self, index_dir: str):
        """Initialize indexer with index directory.

        Args:
            index_dir: Directory to store the Whoosh index
        """
        self.index_dir = Path(index_dir)
        self.schema = self._create_schema()

    def _create_schema(self) -> Schema:
        """Create the Whoosh schema for Genizah documents.

        Returns:
            Whoosh Schema object
        """
        return Schema(
            doc_id=ID(stored=True, unique=True),  # Unique document identifier
            content=TEXT(stored=True),  # Full document text (searchable and stored)
            line_count=NUMERIC(stored=True),  # Number of lines in document
            has_annotations=BOOLEAN(stored=True),  # Contains editorial marks
        )

    def create_index(self) -> index.Index:
        """Create a new index or open existing one.

        Returns:
            Whoosh Index object
        """
        # Create directory if it doesn't exist
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Create or open the index
        if index.exists_in(str(self.index_dir)):
            return index.open_dir(str(self.index_dir))
        else:
            return index.create_in(str(self.index_dir), self.schema)

    def build_index(
        self, transcription_file: str, strip_line_numbers: bool = True, show_progress: bool = True
    ) -> int:
        """Build the search index from transcription file.

        Args:
            transcription_file: Path to GenizaTranscriptions.txt
            strip_line_numbers: Whether to strip line numbers from content
            show_progress: Whether to show progress information

        Returns:
            Number of documents indexed
        """
        parser = GenizahParser(transcription_file)
        idx = self.create_index()

        # Get total document count for progress
        if show_progress:
            total_docs = parser.count_documents()
            click.echo(f"Indexing {total_docs} documents...")

        writer = idx.writer()
        doc_count = 0

        try:
            for doc in parser.parse(strip_line_numbers=strip_line_numbers):
                # Add document to index
                writer.add_document(
                    doc_id=doc.doc_id,
                    content=doc.content,
                    line_count=doc.line_count,
                    has_annotations=doc.has_annotations,
                )

                doc_count += 1

                # Show progress every 100 documents
                if show_progress and doc_count % 100 == 0:
                    click.echo(f"Indexed {doc_count}/{total_docs} documents...", nl=False)
                    click.echo("\r", nl=False)  # Carriage return to overwrite line

            writer.commit()

            if show_progress:
                click.echo(f"\nSuccessfully indexed {doc_count} documents!")

        except Exception as e:
            writer.cancel()
            raise e

        return doc_count

    def get_index(self) -> index.Index:
        """Get the existing index.

        Returns:
            Whoosh Index object

        Raises:
            FileNotFoundError: If index doesn't exist
        """
        if not index.exists_in(str(self.index_dir)):
            raise FileNotFoundError(
                f"Index not found in {self.index_dir}. "
                f"Please build the index first using the indexer."
            )
        return index.open_dir(str(self.index_dir))


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
    "output_dir",
    required=True,
    type=click.Path(),
    help="Directory to store the search index",
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
def main(input_file: str, output_dir: str, keep_line_numbers: bool, quiet: bool):
    """Build the Genizah search index from transcription file.

    Example:
        genizah-index -i GenizaTranscriptions.txt -o index/
    """
    try:
        indexer = GenizahIndexer(output_dir)
        strip_line_numbers = not keep_line_numbers
        show_progress = not quiet

        indexer.build_index(
            input_file, strip_line_numbers=strip_line_numbers, show_progress=show_progress
        )

        if not quiet:
            index_size = sum(f.stat().st_size for f in Path(output_dir).rglob("*") if f.is_file())
            click.echo(f"Index size: {index_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
