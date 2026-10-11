"""Flask application for the Markdown snippet dashboard API."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from extractor import Snippet, count_markdown_files, scan_folder
from mock_runner import run_mock


def create_app(default_folder: Path | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["DEFAULT_FOLDER"] = (default_folder or Path("./sample_notes")).resolve()

    @app.get("/")
    def dashboard() -> str:
        """Render the dashboard shell."""
        return render_template("index.html")

    @app.get("/api/snippets")
    def get_snippets() -> tuple[Any, int] | Any:
        """Return snippets filtered by folder, language, and search text."""
        folder, error_response = _folder_from_request(app)
        if error_response is not None:
            return error_response

        snippets = scan_folder(folder)
        language = request.args.get("language", "").strip().lower()
        query = request.args.get("q", "").strip().casefold()
        if language:
            normalized_language = {"py": "python", "js": "javascript"}.get(language, language)
            snippets = [snippet for snippet in snippets if snippet.language == normalized_language]
        if query:
            snippets = [snippet for snippet in snippets if _matches_query(snippet, query)]
        return jsonify([snippet.to_dict() for snippet in snippets])

    @app.get("/api/stats")
    def get_stats() -> tuple[Any, int] | Any:
        """Return file and language counts for the selected folder."""
        folder, error_response = _folder_from_request(app)
        if error_response is not None:
            return error_response

        snippets = scan_folder(folder)
        return jsonify(
            {
                "files": count_markdown_files(folder),
                "snippets": len(snippets),
                "python": sum(snippet.language == "python" for snippet in snippets),
                "javascript": sum(snippet.language == "javascript" for snippet in snippets),
            }
        )

    @app.post("/api/run")
    def run_snippet() -> tuple[Any, int] | Any:
        """Run safe mock analysis for the requested snippet ID."""
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("snippet_id"), str):
            return _json_error("Request JSON must include a snippet_id.", 400)

        folder, error_response = _folder_from_request(app, payload.get("folder"))
        if error_response is not None:
            return error_response
        snippet = next((item for item in scan_folder(folder) if item.id == payload["snippet_id"]), None)
        if snippet is None:
            return _json_error("Snippet not found.", 404)
        return jsonify(run_mock(snippet.code, snippet.language))

    return app


def _folder_from_request(
    app: Flask,
    requested_folder: str | None = None,
) -> tuple[Path, tuple[Any, int] | None]:
    """Resolve and validate a request folder without serving its files."""
    raw_folder = requested_folder or request.args.get("folder")
    folder = Path(raw_folder).expanduser() if raw_folder else app.config["DEFAULT_FOLDER"]
    try:
        resolved_folder = folder.resolve(strict=True)
    except OSError:
        return folder, _json_error("Folder could not be read.", 400)
    if not resolved_folder.is_dir():
        return resolved_folder, _json_error("Folder must be an existing directory.", 400)
    return resolved_folder, None


def _matches_query(snippet: Snippet, query: str) -> bool:
    """Return whether a search query occurs in snippet metadata or code."""
    searchable = " ".join(
        (snippet.file, snippet.code, snippet.nearest_heading or "")
    ).casefold()
    return query in searchable


def _json_error(message: str, status: int) -> tuple[Any, int]:
    """Build a consistent JSON error response."""
    return jsonify({"error": message}), status


app = create_app(Path(sys.argv[1]) if len(sys.argv) > 1 else None)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)