# Snippet Atlas

Snippet Atlas is a local-first Markdown code snippet dashboard. It scans a folder of notes, extracts Python and JavaScript fenced blocks, and presents them in a searchable library with safe mock execution.

Code is never executed. Python syntax is checked with `ast.parse`; JavaScript uses a lightweight quote and bracket check. Output is simulated from static `print(...)` and `console.log(...)` calls.

## Setup

Requirements: Python 3.10+.

```bash
cd snippet_dashboard
python -m pip install -r requirements.txt
```

## Run

Use the included notes folder:

```bash
python app.py
```

Or choose another local folder:

```bash
python app.py /path/to/markdown-notes
```

Open <http://127.0.0.1:5000>. The folder can also be changed from the dashboard. Only `.md` and `.markdown` files are scanned, and hidden folders plus `.git`, `node_modules`, and `venv` are skipped.

## Test

```bash
pytest -q
```

The tests cover fenced block parsing, headings, line numbers, nested and unclosed fences, invalid encodings, folder filtering, syntax checks, simulated output, API filters, invalid paths, and the dashboard route.

## API

`GET /api/snippets?folder=...&language=...&q=...` returns extracted snippets. Search matches code, filenames, and nearest headings.

`GET /api/stats?folder=...` returns scanned file, snippet, Python, and JavaScript counts.

`POST /api/run` accepts `{"snippet_id": "...", "folder": "..."}` and returns syntax status, simulated stdout, warnings, and `mock: true`.

## Project layout

```text
app.py                 Flask routes and application entry point
extractor.py           Markdown scanning and fenced block parsing
mock_runner.py         Static syntax checks and simulated output
templates/index.html   Dashboard markup
static/style.css       Responsive dashboard styling
static/app.js          Dashboard interactions
sample_notes/          Demo Markdown notes
tests/                 Backend test suite
```