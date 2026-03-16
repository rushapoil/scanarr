"""System endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/v1/system/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_status(client):
    resp = await client.get("/api/v1/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app_name"] == "Scanarr"
    assert "version" in data
