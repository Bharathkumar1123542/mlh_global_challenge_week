"""Tests for Markdown snippet extraction."""

from pathlib import Path

from extractor import parse_markdown, scan_folder


def test_extracts_languages_headings_and_line_numbers() -> None:
    content = "# Guide\n\n## Example\n\n```py\nprint('hello')\n```\n"

    snippets = parse_markdown(content, "guide.md")

    assert len(snippets) == 1
    assert snippets[0].language == "python"
    assert snippets[0].nearest_heading == "Example"
    assert snippets[0].start_line == 6
    assert snippets[0].end_line == 6


def test_supports_tilde_fences_and_windows_line_endings() -> None:
    snippets = parse_markdown("# JS\r\n\r\n~~~javascript\r\nconsole.log('ok')\r\n~~~\r\n", "x.md")

    assert snippets[0].language == "javascript"
    assert snippets[0].code == "console.log('ok')"


def test_ignores_other_languages_and_empty_blocks() -> None:
    content = "```sql\nSELECT 1;\n```\n```python\n\n```\n"

    assert parse_markdown(content, "x.md") == []


def test_unclosed_fence_is_read_to_end() -> None:
    snippets = parse_markdown("```python\nvalue = 1\nprint(value)", "x.md")

    assert snippets[0].code == "value = 1\nprint(value)"
    assert snippets[0].end_line == 3


def test_longer_fence_allows_shorter_nested_fence() -> None:
    content = "````python\n```\nprint('inside')\n```\n````\n"

    snippets = parse_markdown(content, "x.md")

    assert snippets[0].code == "```\nprint('inside')\n```"


def test_scan_folder_skips_hidden_and_excluded_directories(tmp_path: Path) -> None:
    (tmp_path / "visible.md").write_text("```python\nprint(1)\n```", encoding="utf-8")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "hidden.md").write_text("```python\nprint(2)\n```", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.md").write_text("```js\nconsole.log(3)\n```", encoding="utf-8")

    snippets = scan_folder(tmp_path)

    assert [snippet.file for snippet in snippets] == ["visible.md"]


def test_scan_folder_falls_back_for_bad_utf8(tmp_path: Path) -> None:
    markdown_file = tmp_path / "legacy.md"
    markdown_file.write_bytes(b"```python\nprint('caf\xff')\n```")

    snippets = scan_folder(tmp_path)

    assert len(snippets) == 1
    assert "caf" in snippets[0].code