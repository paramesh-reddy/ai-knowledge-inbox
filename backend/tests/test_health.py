"""Tests for health and dashboard endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert "app_name" in data
    assert data["configured_model"] == "gemini-3.8-flash"


@pytest.mark.asyncio
async def test_dashboard_stats_empty(client: AsyncClient):
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 0
    assert data["completed_documents"] == 0
    assert data["recent_documents"] == []
    assert data["recent_jobs"] == []
