"""Perform safe, static syntax checks and simulated output for snippets."""

from __future__ import annotations

import ast
import re
from typing import Any


MOCK_WARNING = "MOCK OUTPUT: code was not executed"


def run_mock(code: str, language: str) -> dict[str, Any]:
    """Check syntax and simulate stdout without executing the supplied code."""
    if language == "python":
        syntax_ok, error, line = _check_python_syntax(code)
        stdout = _python_stdout(code) if syntax_ok else []
    elif language == "javascript":
        syntax_ok, error, line = _check_javascript_syntax(code)
        stdout = _javascript_stdout(code) if syntax_ok else []
    else:
        return {
            "syntax_ok": False,
            "error": f"Unsupported language: {language}",
            "line": None,
            "stdout": [],
            "warnings": [MOCK_WARNING],
            "mock": True,
        }

    warnings = [MOCK_WARNING]
    if not stdout and syntax_ok:
        warnings.append("No simulated output calls found.")
    return {
        "syntax_ok": syntax_ok,
        "error": error,
        "line": line,
        "stdout": stdout,
        "warnings": warnings,
        "mock": True,
    }


def _check_python_syntax(code: str) -> tuple[bool, str | None, int | None]:
    """Return Python syntax status using the standard-library AST parser."""
    try:
        ast.parse(code)
    except SyntaxError as error:
        return False, error.msg, error.lineno
    return True, None, None


def _check_javascript_syntax(code: str) -> tuple[bool, str | None, int | None]:
    """Check JavaScript quotes and bracket pairs with a lightweight scanner."""
    pairs = {")": "(", "]": "[", "}": "{"}
    opening = set(pairs.values())
    stack: list[tuple[str, int]] = []
    quote: str | None = None
    escaped = False
    line_number = 1

    for character in code:
        if character == "\n":
            line_number += 1
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote is not None:
            escaped = True
            continue
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in {"'", '"', "`"}:
            quote = character
        elif character in opening:
            stack.append((character, line_number))
        elif character in pairs:
            if not stack or stack[-1][0] != pairs[character]:
                return False, f"Unexpected closing bracket: {character}", line_number
            stack.pop()

    if quote is not None:
        return False, f"Unclosed quote: {quote}", line_number
    if stack:
        return False, f"Unclosed bracket: {stack[-1][0]}", stack[-1][1]
    return True, None, None


def _python_stdout(code: str) -> list[str]:
    """Render Python print calls using only AST literals and placeholders."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    output: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_name(node.func, "print"):
            continue
        values = [_render_python_value(argument) for argument in node.args]
        output.append(" ".join(values))
    return output


def _render_python_value(node: ast.AST) -> str:
    """Render a Python literal, f-string, or safe placeholder."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool)):
        return str(node.value)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("<value>")
        return "".join(parts)
    return "<value>"


def _javascript_stdout(code: str) -> list[str]:
    """Render console.log calls from JavaScript source text."""
    output: list[str] = []
    call_pattern = re.compile(r"console\.log\s*\(([^\n;]*)\)")
    for match in call_pattern.finditer(code):
        arguments = _split_arguments(match.group(1))
        output.append(" ".join(_render_javascript_value(argument) for argument in arguments))
    return output


def _split_arguments(arguments: str) -> list[str]:
    """Split a call argument list without splitting inside literals."""
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for character in arguments:
        if escaped:
            current.append(character)
            escaped = False
            continue
        if character == "\\" and quote is not None:
            current.append(character)
            escaped = True
            continue
        if character in {"'", '"', "`"}:
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
        if character == "," and quote is None:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def _render_javascript_value(argument: str) -> str:
    """Render JavaScript string and template literals without evaluation."""
    argument = argument.strip()
    if len(argument) >= 2 and argument[0] == argument[-1] and argument[0] in {"'", '"'}:
        return argument[1:-1]
    if len(argument) >= 2 and argument[0] == "`" and argument[-1] == "`":
        template = argument[1:-1]
        return re.sub(r"\$\{[^}]+\}", "<value>", template)
    literal_parts = re.findall(r"(['\"])(.*?)\1", argument)
    if literal_parts:
        return "".join(part[1] for part in literal_parts) + ("<value>" if "+" in argument else "")
    return "<value>"


def _is_name(node: ast.AST, name: str) -> bool:
    """Return whether an AST node is a simple name with the given value."""
    return isinstance(node, ast.Name) and node.id == name