"""Flask web application for searching Cairo Genizah transcriptions."""

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from genizah_search.searcher import GenizahSearcher

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")

# Configuration
app.config["INDEX_DIR"] = os.environ.get("INDEX_PATH", "index/")


def get_searcher():
    """Get or create searcher instance."""
    if not hasattr(app, "searcher"):
        app.searcher = GenizahSearcher(app.config["INDEX_DIR"])
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

    except FileNotFoundError:
        return render_template(
            "index.html",
            error="אינדקס החיפוש לא נמצא. אנא בנה את האינדקס תחילה.",
        )
    except ValueError as e:
        return render_template("index.html", error=f"שאילתת חיפוש לא תקינה: {e}")
    except Exception as e:
        return render_template("index.html", error=f"שגיאת חיפוש: {e}")


@app.route("/document/<doc_id>")
def document(doc_id):
    """Display a specific document."""
    try:
        searcher = get_searcher()
        doc = searcher.get_document(doc_id)

        if not doc:
            return render_template("error.html", error=f"מסמך {doc_id} לא נמצא")

        return render_template("document.html", document=doc)

    except FileNotFoundError:
        return render_template(
            "error.html",
            error="אינדקס החיפוש לא נמצא. אנא בנה את האינדקס תחילה.",
        )
    except Exception as e:
        return render_template("error.html", error=f"שגיאה: {e}")


@app.route("/stats")
def stats():
    """Display index statistics."""
    try:
        searcher = get_searcher()
        statistics = searcher.get_statistics()

        return render_template("stats.html", stats=statistics)

    except FileNotFoundError:
        return render_template(
            "error.html",
            error="אינדקס החיפוש לא נמצא. אנא בנה את האינדקס תחילה.",
        )
    except Exception as e:
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

    except FileNotFoundError:
        return jsonify({"error": "אינדקס לא נמצא"}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """API endpoint for statistics (returns JSON)."""
    try:
        searcher = get_searcher()
        statistics = searcher.get_statistics()
        return jsonify(statistics)

    except FileNotFoundError:
        return jsonify({"error": "אינדקס לא נמצא"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template("error.html", error="העמוד לא נמצא"), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return render_template("error.html", error="שגיאת שרת פנימית"), 500


if __name__ == "__main__":
    # Check if index exists
    index_dir = app.config["INDEX_DIR"]
    if not Path(index_dir).exists():
        print(f"אזהרה: תיקיית אינדקס '{index_dir}' לא נמצאה.")
        print("אנא בנה את האינדקס תחילה באמצעות:")
        print("  genizah-index -i GenizaTranscriptions.txt -o index/")

    app.run(debug=True, host="0.0.0.0", port=5000)
