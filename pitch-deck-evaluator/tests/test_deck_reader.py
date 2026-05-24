from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deck_reader import DeckReaderError, read_deck


def make_pdf(path: Path, pages: list[str]) -> None:
    c = canvas.Canvas(str(path))
    for page in pages:
        c.drawString(72, 720, page)
        c.showPage()
    c.save()


def test_read_pdf_extracts_one_slide_per_page(tmp_path: Path) -> None:
    pdf = tmp_path / "sample.pdf"
    make_pdf(pdf, ["Slide 1 Problem: hotels are disconnected", "Slide 2 Solution: book rooms with locals"])
    slides = read_deck(pdf)
    assert len(slides) == 2
    assert slides[0]["slide_num"] == 1
    assert "Problem" in slides[0]["text"]


def test_read_text_deck_delimited_blocks(tmp_path: Path) -> None:
    deck = tmp_path / "slides.md"
    deck.write_text("Slide 1:\nProblem\n---\nSlide 2:\nSolution", encoding="utf-8")
    slides = read_deck(deck)
    assert len(slides) == 2
    assert slides[1]["slide_ref"] == "slide_02"


def test_image_only_directory_errors_clearly(tmp_path: Path) -> None:
    (tmp_path / "slide_01.png").write_bytes(b"not-really-an-image")
    with pytest.raises(DeckReaderError, match="image-only deck not supported in v1"):
        read_deck(tmp_path)


def test_malformed_input_errors(tmp_path: Path) -> None:
    with pytest.raises(DeckReaderError, match="does not exist"):
        read_deck(tmp_path / "missing.pdf")
