"""Manga CRUD endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_list_manga_empty(client):
    resp = await client.get("/api/v1/manga")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_add_manga(client):
    payload = {
        "title": "One Piece",
        "monitored": True,
        "monitor_status": "all",
        "root_folder_path": "/manga",
    }
    resp = await client.post("/api/v1/manga", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "One Piece"
    assert data["title_slug"] == "one-piece"
    assert data["monitored"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_add_manga_duplicate_mangadex_id(client):
    payload = {
        "title": "Naruto",
        "mangadex_id": "some-uuid-1234",
        "root_folder_path": "/manga",
    }
    resp1 = await client.post("/api/v1/manga", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/manga", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_get_manga(client):
    # Add first
    resp = await client.post("/api/v1/manga", json={"title": "Bleach", "root_folder_path": "/manga"})
    manga_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/manga/{manga_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == manga_id


@pytest.mark.asyncio
async def test_get_manga_not_found(client):
    resp = await client.get("/api/v1/manga/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_manga(client):
    resp = await client.post("/api/v1/manga", json={"title": "HxH", "root_folder_path": "/manga"})
    manga_id = resp.json()["id"]

    resp = await client.put(f"/api/v1/manga/{manga_id}", json={"monitored": False})
    assert resp.status_code == 200
    assert resp.json()["monitored"] is False


@pytest.mark.asyncio
async def test_delete_manga(client):
    resp = await client.post("/api/v1/manga", json={"title": "Berserk", "root_folder_path": "/manga"})
    manga_id = resp.json()["id"]

    resp = await client.delete(f"/api/v1/manga/{manga_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/manga/{manga_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_manga_filter_monitored(client):
    await client.post("/api/v1/manga", json={"title": "A", "monitored": True, "root_folder_path": "/manga"})
    await client.post("/api/v1/manga", json={"title": "B", "monitored": False, "root_folder_path": "/manga"})

    resp = await client.get("/api/v1/manga?monitored=true")
    assert resp.status_code == 200
    titles = [m["title"] for m in resp.json()]
    assert "A" in titles
    assert "B" not in titles
