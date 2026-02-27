file parser cli for agents

## Install

```bash
uv sync
```

To enable OCR for scanned PDFs:

```bash
uv sync --extra ocr
```

## Usage

```bash
uv run file-parser --help
```

Extract PDF content:

```bash
uv run file-parser pdf ./docs/report.pdf
```

Extract selected pages:

```bash
uv run file-parser pdf ./docs/report.pdf --pages 1-2,5
```

Run OCR only when normal PDF text extraction returns nothing:

```bash
uv run file-parser pdf ./docs/scan.pdf --ocr auto
```

Read text files:

```bash
uv run file-parser text ./notes.txt
```

Read JSON files (normalized):

```bash
uv run file-parser json ./payload.json
```
