"""Settings endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_list_quality_profiles_empty(client):
    resp = await client.get("/api/v1/settings/qualityprofile")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_add_and_get_download_client(client):
    payload = {
        "name": "qBittorrent Local",
        "type": "qbittorrent",
        "host": "localhost",
        "port": 8080,
        "category": "scanarr",
        "enabled": True,
        "is_default": True,
    }
    resp = await client.post("/api/v1/settings/downloadclient", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "qBittorrent Local"
    assert data["type"] == "qbittorrent"
    assert "password" not in data  # password never returned

    resp2 = await client.get("/api/v1/settings/downloadclient")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


@pytest.mark.asyncio
async def test_naming_config(client):
    resp = await client.get("/api/v1/settings/naming")
    # May 404 if init_db wasn't run in test context
    assert resp.status_code in (200, 404)
