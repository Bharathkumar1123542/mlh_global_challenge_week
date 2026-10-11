"""Tests for static mock execution."""

from mock_runner import run_mock


def test_python_literal_and_f_string_output_is_simulated() -> None:
    result = run_mock('name = "Ada"\nprint("Hello", f"{name}!")', "python")

    assert result["syntax_ok"] is True
    assert result["stdout"] == ["Hello <value>!"]
    assert result["mock"] is True
    assert result["warnings"] == ["MOCK OUTPUT: code was not executed"]


def test_python_syntax_error_includes_line_number() -> None:
    result = run_mock("value = 1\nif value\n    print(value)", "python")

    assert result["syntax_ok"] is False
    assert result["line"] == 2
    assert result["stdout"] == []


def test_javascript_template_output_is_simulated() -> None:
    result = run_mock("const count = 3;\nconsole.log(`Loaded ${count} items`);", "javascript")

    assert result["syntax_ok"] is True
    assert result["stdout"] == ["Loaded <value> items"]


def test_javascript_unbalanced_brackets_are_rejected() -> None:
    result = run_mock("function greet() {\n  console.log('hi');", "javascript")

    assert result["syntax_ok"] is False
    assert result["line"] == 1
    assert "Unclosed bracket" in result["error"]


def test_non_literal_output_uses_placeholder() -> None:
    result = run_mock("console.log(value);", "javascript")

    assert result["stdout"] == ["<value>"]


def test_unsupported_language_fails_gracefully() -> None:
    result = run_mock("puts 'hello'", "ruby")

    assert result["syntax_ok"] is False
    assert result["stdout"] == []
    assert result["mock"] is True