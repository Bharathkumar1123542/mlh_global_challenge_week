"""Tests for Flask API routes."""

from pathlib import Path

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path: Path):
    """Create a test client with a temporary Markdown folder."""
    (tmp_path / "notes.md").write_text(
        "# Demo\n\n```python\nprint('hello')\n```\n\n```js\nconsole.log('ready')\n```\n",
        encoding="utf-8",
    )
    application = create_app(tmp_path)
    application.config["TESTING"] = True
    with application.test_client() as test_client:
        yield test_client


def test_snippets_can_filter_by_language_and_query(client) -> None:
    response = client.get("/api/snippets?language=python&q=hello")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["language"] == "python"


def test_dashboard_route_renders_html(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b"Snippet Atlas" in response.data


def test_stats_count_files_and_languages(client) -> None:
    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.get_json() == {"files": 1, "snippets": 2, "python": 1, "javascript": 1}


def test_run_returns_mock_result(client) -> None:
    snippets = client.get("/api/snippets").get_json()

    response = client.post("/api/run", json={"snippet_id": snippets[0]["id"]})

    assert response.status_code == 200
    assert response.get_json()["mock"] is True
    assert "MOCK OUTPUT" in response.get_json()["warnings"][0]


def test_invalid_folder_returns_json_error(client) -> None:
    response = client.get("/api/snippets?folder=/path/that/does/not/exist")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_missing_snippet_id_is_rejected(client) -> None:
    response = client.post("/api/run", json={})

    assert response.status_code == 400
    assert "snippet_id" in response.get_json()["error"]