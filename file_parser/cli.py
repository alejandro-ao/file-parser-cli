from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Sequence

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError


def _ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")


def _parse_pages(page_spec: str | None, total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if page_spec is None:
        return list(range(total_pages))

    selected: set[int] = set()
    for chunk in page_spec.split(","):
        token = chunk.strip()
        if not token:
            continue
        if "-" in token:
            start_raw, end_raw = token.split("-", maxsplit=1)
            start = int(start_raw)
            end = int(end_raw)
            if start < 1 or end < 1 or end < start:
                raise ValueError(f"Invalid page range: {token}")
            if end > total_pages:
                raise ValueError(
                    f"Page range {token} is out of bounds for {total_pages} pages"
                )
            selected.update(range(start - 1, end))
            continue

        page_num = int(token)
        if page_num < 1 or page_num > total_pages:
            raise ValueError(f"Page {page_num} is out of bounds for {total_pages} pages")
        selected.add(page_num - 1)

    if not selected:
        raise ValueError("No pages selected")
    return sorted(selected)


def _ocr_pdf_pages(
    pdf_path: Path, page_indexes: Sequence[int], dpi: int = 200
) -> dict[int, str]:
    try:
        import pypdfium2 as pdfium
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies are missing. Install with `uv sync --extra ocr`."
        ) from exc

    engine = RapidOCR()
    doc = pdfium.PdfDocument(str(pdf_path))
    scale = dpi / 72.0
    text_by_page: dict[int, str] = {}

    for page_index in page_indexes:
        page = doc[page_index]
        bitmap = page.render(scale=scale)
        image = bitmap.to_numpy()
        results, _ = engine(image)

        lines: list[str] = []
        for item in results or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                line = str(item[1]).strip()
                if line:
                    lines.append(line)
        text_by_page[page_index] = "\n".join(lines).strip()

    return text_by_page


def extract_pdf_text(
    pdf_path: Path,
    pages: str | None = None,
    ocr: str = "never",
    ocr_dpi: int = 200,
) -> str:
    _ensure_file(pdf_path)

    try:
        with contextlib.redirect_stderr(io.StringIO()):
            reader = PdfReader(str(pdf_path))
    except (PdfReadError, PdfStreamError) as exc:
        raise ValueError(f"Could not read PDF: {pdf_path}") from exc
    page_indexes = _parse_pages(pages, total_pages=len(reader.pages))
    if not page_indexes:
        return ""

    text_by_page: dict[int, str] = {}
    for page_index in page_indexes:
        raw_text = reader.pages[page_index].extract_text() or ""
        text_by_page[page_index] = raw_text.strip()

    ocr_targets: list[int] = []
    if ocr == "always":
        ocr_targets = list(page_indexes)
    elif ocr == "auto":
        ocr_targets = [idx for idx in page_indexes if not text_by_page[idx]]

    if ocr_targets:
        try:
            ocr_text_by_page = _ocr_pdf_pages(pdf_path, ocr_targets, dpi=ocr_dpi)
        except RuntimeError:
            if ocr == "always":
                raise
        else:
            for idx, ocr_text in ocr_text_by_page.items():
                if ocr_text:
                    text_by_page[idx] = ocr_text

    rendered_pages: list[str] = []
    for page_index in page_indexes:
        text = text_by_page.get(page_index, "").strip()
        if text:
            rendered_pages.append(f"[page {page_index + 1}]\n{text}")

    return "\n\n".join(rendered_pages)


def _read_text(path: Path, encoding: str = "utf-8") -> str:
    _ensure_file(path)
    return path.read_text(encoding=encoding)


def _read_json(path: Path, compact: bool = False, encoding: str = "utf-8") -> str:
    _ensure_file(path)
    payload = json.loads(path.read_text(encoding=encoding))
    if compact:
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _write_output(text: str) -> int:
    if not text:
        return 0
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def _handle_pdf(args: argparse.Namespace) -> int:
    text = extract_pdf_text(
        pdf_path=Path(args.path),
        pages=args.pages,
        ocr=args.ocr,
        ocr_dpi=args.ocr_dpi,
    )
    return _write_output(text)


def _handle_text(args: argparse.Namespace) -> int:
    return _write_output(_read_text(Path(args.path), encoding=args.encoding))


def _handle_json(args: argparse.Namespace) -> int:
    return _write_output(
        _read_json(Path(args.path), compact=args.compact, encoding=args.encoding)
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-parser",
        description="Extract content from common file formats.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pdf_parser = subparsers.add_parser("pdf", help="Extract text from a PDF file")
    pdf_parser.add_argument("path", help="Path to the PDF file")
    pdf_parser.add_argument(
        "--pages",
        default=None,
        help="Page selection like '1-3,7'. Pages are 1-indexed.",
    )
    pdf_parser.add_argument(
        "--ocr",
        choices=("never", "auto", "always"),
        default="never",
        help="OCR mode. Use 'auto' for image-only pages.",
    )
    pdf_parser.add_argument(
        "--ocr-dpi",
        type=int,
        default=200,
        help="Render DPI when OCR is enabled.",
    )
    pdf_parser.set_defaults(handler=_handle_pdf)

    text_parser = subparsers.add_parser("text", help="Read a plain text file")
    text_parser.add_argument("path", help="Path to the text file")
    text_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding. Defaults to utf-8.",
    )
    text_parser.set_defaults(handler=_handle_text)

    json_parser = subparsers.add_parser("json", help="Read and normalize a JSON file")
    json_parser.add_argument("path", help="Path to the JSON file")
    json_parser.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON with no whitespace.",
    )
    json_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding. Defaults to utf-8.",
    )
    json_parser.set_defaults(handler=_handle_json)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(2)

    try:
        code = handler(args)
    except (FileNotFoundError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        parser.exit(status=2, message=f"error: {exc}\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
