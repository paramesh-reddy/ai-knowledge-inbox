"""Tests for Document upload, note creation, retry, and deletion endpoints."""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_note_success(client: AsyncClient):
    payload = {
        "title": "Architectural Guidelines",
        "content": "Turium AI focuses on robust, production-grade applications.",
    }
    response = await client.post("/api/documents/notes", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["title"] == "Architectural Guidelines"
    assert data["file_type"] == "note"
    assert data["processing_status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_note_empty_content_validation(client: AsyncClient):
    payload = {"title": "Empty Note", "content": "   "}
    response = await client.post("/api/documents/notes", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_txt_file(client: AsyncClient):
    file_bytes = b"This is a raw text file for upload testing."
    files = {"file": ("manual.txt", io.BytesIO(file_bytes), "text/plain")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 202
    data = response.json()
    assert data["original_filename"] == "manual.txt"
    assert data["file_type"] == "txt"
    assert data["processing_status"] == "pending"


@pytest.mark.asyncio
async def test_upload_unsupported_extension_rejected(client: AsyncClient):
    file_bytes = b"executable code"
    files = {"file": ("malicious.exe", io.BytesIO(file_bytes), "application/octet-stream")}
    response = await client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient):
    # 1. Create a note
    res = await client.post(
        "/api/documents/notes",
        json={"title": "Temporary Note", "content": "Content to be deleted."},
    )
    doc_id = res.json()["id"]

    # 2. Delete it
    del_res = await client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200

    # 3. Confirm 404
    get_res = await client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == 404
