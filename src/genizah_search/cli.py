"""Command-line interface for searching the Genizah index."""

import sys

import click

from genizah_search.searcher import GenizahSearcher


@click.command()
@click.option(
    "--query",
    "-q",
    required=True,
    help="Search query string",
)
@click.option(
    "--index",
    "-i",
    "index_dir",
    default="index/",
    type=click.Path(exists=True),
    help="Path to the search index directory (default: index/)",
)
@click.option(
    "--type",
    "-t",
    "search_type",
    type=click.Choice(["fulltext", "docid", "regex"], case_sensitive=False),
    default="fulltext",
    help="Type of search: fulltext, docid, or regex (default: fulltext)",
)
@click.option(
    "--limit",
    "-l",
    default=10,
    type=int,
    help="Maximum number of results to return (default: 10)",
)
@click.option(
    "--no-highlights",
    is_flag=True,
    help="Disable highlighting in results",
)
@click.option(
    "--full",
    "-f",
    is_flag=True,
    help="Show full document content instead of snippets",
)
@click.option(
    "--annotations",
    type=click.Choice(["yes", "no", "any"], case_sensitive=False),
    default="any",
    help="Filter by annotation presence: yes, no, or any (default: any)",
)
@click.option(
    "--min-lines",
    type=int,
    help="Minimum number of lines in document",
)
@click.option(
    "--max-lines",
    type=int,
    help="Maximum number of lines in document",
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show index statistics instead of searching",
)
def main(
    query,
    index_dir,
    search_type,
    limit,
    no_highlights,
    full,
    annotations,
    min_lines,
    max_lines,
    stats,
):
    """Search the Cairo Genizah transcriptions.

    Examples:

        # Full-text search
        genizah-search -q "שבת"

        # Search by document ID
        genizah-search -q "IE104549337" -t docid

        # Regex search
        genizah-search -q "Line \\d+" -t regex

        # Advanced search with filters
        genizah-search -q "מעשרות" --annotations yes --min-lines 5

        # Show index statistics
        genizah-search --stats
    """
    try:
        searcher = GenizahSearcher(index_dir)

        # Show statistics if requested
        if stats:
            show_statistics(searcher)
            return

        # Determine if we need advanced search
        has_annotation_filter = annotations != "any"
        has_line_filter = min_lines is not None or max_lines is not None

        if has_annotation_filter or has_line_filter:
            # Use advanced search
            annotation_value = None
            if annotations == "yes":
                annotation_value = True
            elif annotations == "no":
                annotation_value = False

            results = searcher.advanced_search(
                query=query,
                has_annotations=annotation_value,
                min_line_count=min_lines,
                max_line_count=max_lines,
                limit=limit,
            )
        else:
            # Use regular search
            with_highlights = not no_highlights and search_type == "fulltext"
            results = searcher.search(
                query=query,
                search_type=search_type,
                limit=limit,
                with_highlights=with_highlights,
            )

        # Display results
        display_results(results, full=full, show_highlights=not no_highlights)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "\nPlease build the index first using: "
            "genizah-index -i GenizaTranscriptions.txt -o index/",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def show_statistics(searcher):
    """Display index statistics."""
    stats = searcher.get_statistics()

    click.echo("\n=== Index Statistics ===\n")
    click.echo(f"Total Documents: {stats['total_documents']:,}")
    click.echo(f"Documents with Annotations: {stats['documents_with_annotations']:,}")
    pct = stats["documents_with_annotations"] / stats["total_documents"] * 100
    click.echo(f"Percentage with Annotations: {pct:.1f}%")
    if "last_updated" in stats and stats["last_updated"]:
        click.echo(f"Last Updated: {stats['last_updated']}")
    click.echo()


def display_results(results, full=False, show_highlights=True):
    """Display search results."""
    if not results:
        click.echo("\nNo results found.")
        return

    click.echo(f"\nFound {len(results)} result(s):\n")

    for i, result in enumerate(results, 1):
        click.echo(f"--- Result {i} ---")
        click.echo(f"Document ID: {result.doc_id}")
        click.echo(f"Lines: {result.line_count}")
        click.echo(f"Has Annotations: {'Yes' if result.has_annotations else 'No'}")
        click.echo(f"Relevance Score: {result.score:.2f}")

        if show_highlights and result.highlights and not full:
            click.echo("\nSnippet:")
            click.echo(result.highlights)
        elif full:
            click.echo("\nContent:")
            # Truncate very long documents
            content = result.content
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            click.echo(content)

        click.echo()


if __name__ == "__main__":
    main()
