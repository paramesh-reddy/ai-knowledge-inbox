"""Tests for text chunking with configurable overlap."""
from app.services.chunking_service import ChunkingService


def test_chunking_short_text():
    service = ChunkingService(chunk_size=500, chunk_overlap=50)
    pages = [("Short text.", 1)]
    chunks = service.chunk_extracted_pages(pages)

    assert len(chunks) == 1
    assert chunks[0].text == "Short text."
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0


def test_chunking_long_text_overlap():
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    text = (
        "Paragraph one is introducing the core concepts of vector databases. "
        "Paragraph two delves into cosine similarity and nearest neighbor indexing. "
        "Paragraph three covers prompt augmentation and Gemini generation."
    )
    pages = [(text, 1)]
    chunks = service.chunk_extracted_pages(pages)

    assert len(chunks) > 1
    assert all(len(c.text) <= 120 for c in chunks)
    assert chunks[0].page_number == 1
    assert chunks[1].chunk_index == 1


def test_chunking_preserves_page_numbers():
    service = ChunkingService(chunk_size=200, chunk_overlap=30)
    pages = [
        ("Content from page 1 about databases.", 1),
        ("Content from page 2 about retrieval.", 2),
    ]
    chunks = service.chunk_extracted_pages(pages)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
