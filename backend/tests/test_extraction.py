"""Tests for document text extraction."""
import fitz
from pathlib import Path
import pytest
from app.db.models.document import FileType
from app.services.extraction_service import ExtractionService, ExtractionError


def test_extract_plain_text(tmp_path: Path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Hello, this is a knowledge note about Turium AI.", encoding="utf-8")

    pages = ExtractionService.extract_from_file(txt_file, FileType.TXT)
    assert len(pages) == 1
    text, page_num = pages[0]
    assert "Turium AI" in text
    assert page_num is None


def test_extract_markdown(tmp_path: Path):
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Section 1\n\nAI Knowledge Inbox is fast.\n\n## Sub", encoding="utf-8")

    pages = ExtractionService.extract_from_file(md_file, FileType.MARKDOWN)
    assert len(pages) == 1
    assert "Section 1" in pages[0][0]


def test_extract_pdf(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "First page text content about vector embeddings.")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Second page text content about RAG pipelines.")
    doc.save(str(pdf_path))
    doc.close()

    pages = ExtractionService.extract_from_file(pdf_path, FileType.PDF)
    assert len(pages) == 2
    assert pages[0][1] == 1
    assert "vector embeddings" in pages[0][0]
    assert pages[1][1] == 2
    assert "RAG pipelines" in pages[1][0]


def test_extract_empty_file_fails(tmp_path: Path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(ExtractionError):
        ExtractionService.extract_from_file(empty_file, FileType.TXT)
