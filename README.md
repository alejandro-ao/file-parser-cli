# file-parser-cli

Lightweight local CLI for AI agents and automation scripts to extract text content from files.

## What This Project Does

`file-parser` is designed for one job: read files and print machine-usable content to stdout with minimal overhead.

Current commands:

- `pdf`: extract text from PDF files, with optional OCR for scanned/image-only documents
- `text`: read plain text files
- `json`: read and normalize JSON files

## Why Use It

- Fast, local-first parsing (no external API calls)
- Scriptable output for agent pipelines
- Optional OCR support without forcing heavy dependencies in the default install

## Requirements

- Python `>=3.14`
- `uv`

## Install

Install base dependencies:

```bash
uv sync
```

Install OCR dependencies (for scanned PDFs):

```bash
uv sync --extra ocr
```

## Quick Start

Show help:

```bash
uv run file-parser --help
```

Extract PDF text:

```bash
uv run file-parser pdf ./docs/report.pdf
```

Read text:

```bash
uv run file-parser text ./notes.txt
```

Normalize JSON:

```bash
uv run file-parser json ./payload.json
```

## Command Reference

### `pdf`

Extract text from a PDF file.

```bash
uv run file-parser pdf PATH [--pages PAGE_SPEC] [--ocr MODE] [--ocr-dpi DPI]
```

Options:

- `--pages`: Page selection, 1-indexed. Example: `1-3,7`
- `--ocr`: `never` (default), `auto`, or `always`
- `--ocr-dpi`: render DPI used by OCR (default: `200`)

Examples:

```bash
# Full document extraction
uv run file-parser pdf ./docs/report.pdf

# Selected pages
uv run file-parser pdf ./docs/report.pdf --pages 1-2,5

# OCR only on pages where direct extraction is empty
uv run file-parser pdf ./docs/scan.pdf --ocr auto

# Force OCR on all selected pages
uv run file-parser pdf ./docs/scan.pdf --ocr always
```

### `text`

Read a plain text file.

```bash
uv run file-parser text PATH [--encoding ENCODING]
```

Example:

```bash
uv run file-parser text ./notes.txt --encoding utf-8
```

### `json`

Read and normalize JSON.

```bash
uv run file-parser json PATH [--compact] [--encoding ENCODING]
```

Examples:

```bash
# Pretty-printed JSON (default)
uv run file-parser json ./payload.json

# Compact JSON (single line)
uv run file-parser json ./payload.json --compact
```

## OCR Notes

- OCR is optional by design to keep default installs lightweight.
- If you run `--ocr always` without OCR dependencies installed, the command exits with an error.
- `--ocr auto` gracefully falls back to non-OCR output when OCR extras are not installed.

## Exit Behavior

- Successful runs exit `0`.
- Input/parse errors exit non-zero and print an `error:` message to stderr.

## Development

Run locally during development:

```bash
uv run file-parser --help
```
