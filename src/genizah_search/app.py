"""Flask web application for searching Cairo Genizah transcriptions."""

import os
import time
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

from genizah_search.logging_config import get_logger, setup_logging
from genizah_search.searcher import GenizahSearcher

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")

# Configuration
app.config["INDEX_DIR"] = os.environ.get("INDEX_PATH", "index/")

logger.info(f"Flask app initialized with INDEX_DIR: {app.config['INDEX_DIR']}")


# Request/response logging middleware
@app.before_request
def before_request():
    """Log incoming requests and track timing."""
    g.start_time = time.time()
    logger.info(
        f"Request: {request.method} {request.path} | "
        f"Remote: {request.remote_addr} | "
        f"User-Agent: {request.user_agent.string[:100]}"
    )
    if request.query_string:
        logger.debug(f"Query parameters: {request.query_string.decode('utf-8')}")


@app.after_request
def after_request(response):
    """Log response details."""
    if hasattr(g, "start_time"):
        duration = time.time() - g.start_time
        logger.info(
            f"Response: {request.method} {request.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s"
        )
    return response


def get_searcher():
    """Get or create searcher instance."""
    if not hasattr(app, "searcher"):
        logger.info("Creating new GenizahSearcher instance")
        try:
            app.searcher = GenizahSearcher(app.config["INDEX_DIR"])
            logger.info("GenizahSearcher instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create searcher: {type(e).__name__}: {e}")
            raise
    return app.searcher


@app.route("/")
def index():
    """Render the main search page."""
    return render_template("index.html")


@app.route("/search")
def search():
    """Handle search requests."""
    query = request.args.get("q", "").strip()
    search_type = request.args.get("type", "fulltext")
    limit = int(request.args.get("limit", 10))
    has_annotations = request.args.get("annotations")
    min_lines = request.args.get("min_lines", type=int)
    max_lines = request.args.get("max_lines", type=int)

    if not query:
        return render_template("index.html", error="אנא הזן שאילתת חיפוש")

    try:
        searcher = get_searcher()

        # Check if we need advanced search
        use_advanced = has_annotations or min_lines is not None or max_lines is not None

        if use_advanced:
            # Convert annotations filter
            annotation_filter = None
            if has_annotations == "yes":
                annotation_filter = True
            elif has_annotations == "no":
                annotation_filter = False

            results = searcher.advanced_search(
                query=query,
                has_annotations=annotation_filter,
                min_line_count=min_lines,
                max_line_count=max_lines,
                limit=limit,
            )
        else:
            with_highlights = search_type == "fulltext"
            results = searcher.search(
                query=query,
                search_type=search_type,
                limit=limit,
                with_highlights=with_highlights,
            )

        return render_template(
            "results.html",
            query=query,
            search_type=search_type,
            results=results,
            result_count=len(results),
        )

    except FileNotFoundError as e:
        logger.error(f"Search failed - index not found: {e}")
        return render_template(
            "index.html",
            error="אינדקס החיפוש לא נמצא. אנא בנה את האינדקס תחילה.",
        )
    except ValueError as e:
        logger.warning(f"Search failed - invalid query: {e}")
        return render_template("index.html", error=f"שאילתת חיפוש לא תקינה: {e}")
    except Exception as e:
        logger.error(f"Search failed with unexpected error: {type(e).__name__}: {e}", exc_info=True)
        return render_template("index.html", error=f"שגיאת חיפוש: {e}")


@app.route("/document/<doc_id>")
def document(doc_id):
    """Display a specific document."""
    try:
        searcher = get_searcher()
        doc = searcher.get_document(doc_id)

        if not doc:
            logger.info(f"Document not found: {doc_id}")
            return render_template("error.html", error=f"מסמך {doc_id} לא נמצא")

        logger.info(f"Document retrieved successfully: {doc_id}")
        return render_template("document.html", document=doc)

    except FileNotFoundError as e:
        logger.error(f"Document retrieval failed - index not found: {e}")
        return render_template(
            "error.html",
            error="אינדקס החיפוש לא נמצא. אנא בנה את האינדקס תחילה.",
        )
    except Exception as e:
        logger.error(
            f"Document retrieval failed for {doc_id}: {type(e).__name__}: {e}", exc_info=True
        )
        return render_template("error.html", error=f"שגיאה: {e}")


@app.route("/stats")
def stats():
    """Display index statistics."""
    try:
        searcher = get_searcher()
        statistics = searcher.get_statistics()

        logger.info("Statistics page accessed successfully")
        return render_template("stats.html", stats=statistics)

    except FileNotFoundError as e:
        logger.error(f"Statistics retrieval failed - index not found: {e}")
        return render_template(
            "error.html",
            error="אינדקס החיפוש לא נמצא. אנא בנה את האינדקס תחילה.",
        )
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {type(e).__name__}: {e}", exc_info=True)
        return render_template("error.html", error=f"שגיאה: {e}")


@app.route("/api/search")
def api_search():
    """API endpoint for search (returns JSON)."""
    query = request.args.get("q", "").strip()
    search_type = request.args.get("type", "fulltext")
    limit = int(request.args.get("limit", 10))

    if not query:
        return jsonify({"error": "פרמטר שאילתה 'q' נדרש"}), 400

    try:
        searcher = get_searcher()
        results = searcher.search(
            query=query, search_type=search_type, limit=limit, with_highlights=False
        )

        # Convert results to dict
        results_dict = [
            {
                "doc_id": r.doc_id,
                "content": r.content[:500],  # Truncate for API
                "line_count": r.line_count,
                "has_annotations": r.has_annotations,
                "score": r.score,
            }
            for r in results
        ]

        return jsonify({"query": query, "results": results_dict, "count": len(results)})

    except FileNotFoundError as e:
        logger.error(f"API search failed - index not found: {e}")
        return jsonify({"error": "אינדקס לא נמצא"}), 500
    except ValueError as e:
        logger.warning(f"API search failed - invalid parameters: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"API search failed: {type(e).__name__}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """API endpoint for statistics (returns JSON)."""
    try:
        searcher = get_searcher()
        statistics = searcher.get_statistics()
        logger.info("API statistics retrieved successfully")
        return jsonify(statistics)

    except FileNotFoundError as e:
        logger.error(f"API stats failed - index not found: {e}")
        return jsonify({"error": "אינדקס לא נמצא"}), 500
    except Exception as e:
        logger.error(f"API stats failed: {type(e).__name__}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    logger.warning(f"404 Not Found: {request.path}")
    return render_template("error.html", error="העמוד לא נמצא"), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"500 Internal Server Error: {e}", exc_info=True)
    return render_template("error.html", error="שגיאת שרת פנימית"), 500


if __name__ == "__main__":
    # Check if index exists
    index_dir = app.config["INDEX_DIR"]
    if not Path(index_dir).exists():
        warning_msg = f"אזהרה: תיקיית אינדקס '{index_dir}' לא נמצאה."
        print(warning_msg)
        print("אנא בנה את האינדקס תחילה באמצעות:")
        print("  genizah-index -i GenizaTranscriptions.txt -o index/")
        logger.warning(warning_msg)

    logger.info("Starting Flask development server on 0.0.0.0:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
