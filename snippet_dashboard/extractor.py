"""Scan Markdown files and extract supported fenced code blocks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Iterable


SUPPORTED_LANGUAGES: dict[str, str] = {
    "js": "javascript",
    "javascript": "javascript",
    "py": "python",
    "python": "python",
}
SKIPPED_DIRECTORIES = {".git", "node_modules", "venv"}
FENCE_PATTERN = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")


@dataclass(frozen=True)
class Snippet:
    """A supported code block and its location in a Markdown file."""

    id: str
    file: str
    language: str
    code: str
    start_line: int
    end_line: int
    nearest_heading: str | None

    def to_dict(self) -> dict[str, object]:
        """Return the snippet as a JSON-serializable dictionary."""
        return asdict(self)


def parse_markdown(content: str, relative_file: str) -> list[Snippet]:
    """Extract supported fenced blocks from Markdown content.

    Fence characters and lengths are tracked so a shorter fence inside a
    longer fence remains part of the code. Unclosed fences are accepted and
    read through the end of the file.
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    snippets: list[Snippet] = []
    nearest_heading: str | None = None
    open_fence: tuple[str, int, str, int] | None = None
    code_lines: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if open_fence is None:
            heading_match = HEADING_PATTERN.match(line)
            if heading_match:
                nearest_heading = heading_match.group(1).strip()

            fence_match = FENCE_PATTERN.match(line)
            if fence_match:
                marker = fence_match.group(1)
                language = _normalise_language(fence_match.group(2))
                open_fence = (marker[0], len(marker), language, line_number)
                code_lines = []
            continue

        marker_character, marker_length, language, start_marker_line = open_fence
        if _is_closing_fence(line, marker_character, marker_length):
            if language and any(code_line.strip() for code_line in code_lines):
                snippets.append(
                    _build_snippet(
                        relative_file,
                        language,
                        code_lines,
                        start_marker_line + 1,
                        line_number - 1,
                        nearest_heading,
                        len(snippets),
                    )
                )
            open_fence = None
            code_lines = []
        else:
            code_lines.append(line)

    if open_fence is not None:
        marker_character, marker_length, language, start_marker_line = open_fence
        del marker_character, marker_length
        if language and any(code_line.strip() for code_line in code_lines):
            snippets.append(
                _build_snippet(
                    relative_file,
                    language,
                    code_lines,
                    start_marker_line + 1,
                    len(lines),
                    nearest_heading,
                    len(snippets),
                )
            )

    return snippets


def scan_folder(folder: Path) -> list[Snippet]:
    """Recursively scan a folder for readable Markdown snippets."""
    snippets: list[Snippet] = []
    for path in _markdown_files(folder):
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
        relative_file = path.relative_to(folder).as_posix()
        snippets.extend(parse_markdown(content, relative_file))
    return snippets


def count_markdown_files(folder: Path) -> int:
    """Count readable Markdown paths eligible for scanning."""
    return sum(1 for _ in _markdown_files(folder))


def _markdown_files(folder: Path) -> Iterable[Path]:
    """Yield Markdown files while skipping hidden and excluded directories."""
    for path in folder.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".markdown"}:
            continue
        relative_parts = path.relative_to(folder).parts
        if any(part.startswith(".") or part in SKIPPED_DIRECTORIES for part in relative_parts[:-1]):
            continue
        yield path


def _normalise_language(info_string: str) -> str | None:
    """Normalize the first fence info token to a supported language."""
    language = info_string.strip().split(maxsplit=1)[0].lower() if info_string.strip() else ""
    return SUPPORTED_LANGUAGES.get(language)


def _is_closing_fence(line: str, marker_character: str, marker_length: int) -> bool:
    """Return whether a line closes a fence of the given character and size."""
    match = re.match(r"^\s{0,3}(`+|~+)[ \t]*$", line)
    return bool(
        match
        and match.group(1)[0] == marker_character
        and len(match.group(1)) >= marker_length
    )


def _build_snippet(
    relative_file: str,
    language: str,
    code_lines: list[str],
    start_line: int,
    end_line: int,
    nearest_heading: str | None,
    index: int,
) -> Snippet:
    """Build a stable snippet record from parsed block data."""
    return Snippet(
        id=f"{relative_file}:{start_line}:{index}",
        file=relative_file,
        language=language,
        code="\n".join(code_lines),
        start_line=start_line,
        end_line=end_line,
        nearest_heading=nearest_heading,
    )