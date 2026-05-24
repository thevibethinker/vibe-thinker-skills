#!/usr/bin/env python3
"""Deck ingestion adapters for pitch-deck-evaluator."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("pitch_deck_evaluator.deck_reader")
IMAGE_ONLY_ERROR = "image-only deck not supported in v1; OCR or text-layer required"
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}


class DeckReaderError(ValueError):
    """Raised when a deck cannot be read safely."""


@dataclass(frozen=True)
class Slide:
    """Normalized slide object used by downstream scorers."""

    slide_num: int
    text: str
    notes: str | None = None
    source_path: str | None = None
    extraction_confidence: str = "high"

    @property
    def slide_ref(self) -> str:
        """Return stable slide reference for reports."""
        return f"slide_{self.slide_num:02d}"

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable slide data with both slide_num and slide_ref."""
        data = asdict(self)
        data["slide_ref"] = self.slide_ref
        return data


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped stderr logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    logging.Formatter.converter = time_gmt


def time_gmt(*_: Any) -> tuple[int, ...]:
    """UTC time tuple for log formatter."""
    return datetime.now(timezone.utc).timetuple()


def natural_sort_key(path: Path) -> list[Any]:
    """Sort paths so slide_10 follows slide_9."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def display_path(path: str | Path) -> str:
    """Return a portable source label for reports without leaking local absolute paths."""
    resolved = Path(path).expanduser().resolve()
    try:
        return resolved.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return resolved.name


def read_deck(deck_path: str | Path) -> list[dict[str, Any]]:
    """Read a supported deck path and return normalized slide dictionaries."""
    slides = _read_deck_objects(Path(deck_path).expanduser().resolve())
    return [slide.to_dict() for slide in slides]


def _read_deck_objects(deck_path: Path) -> list[Slide]:
    if not deck_path.exists():
        raise DeckReaderError(f"Deck path does not exist: {deck_path}")
    if deck_path.is_dir():
        return read_directory(deck_path)
    suffix = deck_path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(deck_path)
    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        return read_text_deck(deck_path)
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        raise DeckReaderError(IMAGE_ONLY_ERROR)
    raise DeckReaderError(
        f"Unsupported deck type '{suffix or '<none>'}'. Supported: PDF, .txt/.md slide text, or directory of text/PDF."
    )


def read_directory(deck_dir: Path) -> list[Slide]:
    """Read a directory bundle by preferring PDF, then text, then image detection."""
    candidates = sorted(deck_dir.iterdir(), key=natural_sort_key)
    for name in ("deck.pdf", "slides.pdf"):
        candidate = deck_dir / name
        if candidate.exists():
            return read_pdf(candidate)
    pdfs = [p for p in candidates if p.is_file() and p.suffix.lower() == ".pdf"]
    if pdfs:
        return read_pdf(pdfs[0])
    for name in ("slides.md", "deck.md", "slides.txt", "deck.txt"):
        candidate = deck_dir / name
        if candidate.exists():
            return read_text_deck(candidate)
    texts = [p for p in candidates if p.is_file() and p.suffix.lower() in SUPPORTED_TEXT_EXTENSIONS]
    if texts:
        return read_text_deck(texts[0])
    images = [p for p in candidates if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]
    if images:
        raise DeckReaderError(IMAGE_ONLY_ERROR)
    raise DeckReaderError(f"No supported deck files found in directory: {deck_dir}")


def read_pdf(pdf_path: Path) -> list[Slide]:
    """Extract one slide object per PDF page using pdfplumber."""
    try:
        import pdfplumber
    except ImportError as exc:
        raise DeckReaderError("pdfplumber is required for PDF extraction. Install with `pip install pdfplumber`.") from exc

    slides: list[Slide] = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text(x_tolerance=1, y_tolerance=3) or "").strip()
                confidence = "high" if len(text) >= 20 else "low"
                slides.append(
                    Slide(
                        slide_num=index,
                        text=text,
                        notes=None if confidence == "high" else "low_text_layer_confidence",
                        source_path=display_path(pdf_path),
                        extraction_confidence=confidence,
                    )
                )
    except Exception as exc:  # pdfplumber raises several backend-specific exceptions.
        raise DeckReaderError(f"Failed to read PDF {pdf_path}: {exc}") from exc
    if not slides:
        raise DeckReaderError(f"PDF contains no pages: {pdf_path}")
    if all(not slide.text.strip() for slide in slides):
        raise DeckReaderError(IMAGE_ONLY_ERROR)
    return slides


def read_text_deck(text_path: Path) -> list[Slide]:
    """Read a plain-text or markdown deck with one slide per delimited block."""
    try:
        raw = text_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DeckReaderError(f"Text deck is not UTF-8 decodable: {text_path}") from exc
    blocks = split_slide_blocks(raw)
    if not blocks:
        raise DeckReaderError(f"Text deck contains no slide text: {text_path}")
    return [
        Slide(slide_num=index, text=block.strip(), source_path=display_path(text_path), extraction_confidence="high")
        for index, block in enumerate(blocks, start=1)
        if block.strip()
    ]


def split_slide_blocks(raw: str) -> list[str]:
    """Split markdown/text into slide blocks using common deck delimiters."""
    normalized = raw.replace("\r\n", "\n")
    marker_pattern = re.compile(r"(?im)^\s*(?:---+|={3,}|#{1,3}\s*slide\s+\d+\b|slide\s+\d+\s*[:.-])\s*$")
    parts = [part.strip() for part in marker_pattern.split(normalized) if part.strip()]
    if len(parts) > 1:
        return parts
    heading_matches = list(re.finditer(r"(?im)^#{1,2}\s+slide\s+\d+\b.*$", normalized))
    if len(heading_matches) > 1:
        blocks: list[str] = []
        for idx, match in enumerate(heading_matches):
            start = match.start()
            end = heading_matches[idx + 1].start() if idx + 1 < len(heading_matches) else len(normalized)
            blocks.append(normalized[start:end].strip())
        return [block for block in blocks if block]
    return [normalized.strip()] if normalized.strip() else []


def main(argv: list[str] | None = None) -> int:
    """CLI for validating deck extraction."""
    parser = argparse.ArgumentParser(description="Extract normalized slide text from a deck.")
    parser.add_argument("deck_path", help="PDF, text/markdown deck, or directory bundle")
    parser.add_argument("--out", help="Optional JSON output path")
    parser.add_argument("--dry-run", action="store_true", help="Validate extraction and print a summary only")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    try:
        slides = read_deck(args.deck_path)
        LOGGER.info("extracted %s slides from %s", len(slides), args.deck_path)
        if args.dry_run:
            print(json.dumps({"slide_count": len(slides), "first_slide_chars": len(slides[0]["text"])}, indent=2))
        elif args.out:
            out_path = Path(args.out).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(slides, indent=2), encoding="utf-8")
            if not out_path.exists():
                raise DeckReaderError(f"Failed to verify write: {out_path}")
            print(str(out_path))
        else:
            print(json.dumps(slides, indent=2))
        return 0
    except DeckReaderError as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
