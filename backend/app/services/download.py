"""
Download client integration.
Currently supports: qBittorrent, Transmission.
SABnzbd / NZBGet stubs included.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.security import decrypt_secret

logger = logging.getLogger(__name__)


# ── Connection test (dispatcher) ──────────────────────────────────────────────

async def test_client(client_model) -> bool:
    """Test connectivity to a download client."""
    try:
        if client_model.type == "qbittorrent":
            return await _qbit_test(client_model)
        elif client_model.type == "transmission":
            return await _transmission_test(client_model)
        elif client_model.type in ("sabnzbd", "nzbget"):
            return await _nzb_test(client_model)
        else:
            logger.warning("Unknown client type: %s", client_model.type)
            return False
    except Exception as exc:
        logger.warning("Client test failed: %s", exc)
        return False


# ── Add torrent/NZB to client ─────────────────────────────────────────────────

async def add_download(client_model, url: str, magnet: str | None = None) -> str | None:
    """
    Add a download to the client.
    Returns the external ID (torrent hash / nzb ID) or None on failure.
    """
    try:
        if client_model.type == "qbittorrent":
            return await _qbit_add(client_model, url, magnet)
        elif client_model.type == "transmission":
            return await _transmission_add(client_model, url, magnet)
        elif client_model.type == "sabnzbd":
            return await _sabnzbd_add(client_model, url)
        else:
            logger.error("Unsupported client type: %s", client_model.type)
            return None
    except Exception as exc:
        logger.exception("Failed to add download: %s", exc)
        return None


# ── Queue sync (called by scheduler) ─────────────────────────────────────────

async def sync_queue() -> None:
    """Update all active queue items with current progress from their client."""
    from sqlalchemy import select

    from app.db import models
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(models.DownloadQueue).where(
                models.DownloadQueue.status.in_(["queued", "downloading"])
            )
        )
        items = result.scalars().all()

        for item in items:
            if not item.download_client_id or not item.external_id:
                continue
            client = await db.get(models.DownloadClient, item.download_client_id)
            if not client:
                continue
            try:
                status, progress = await _get_download_status(client, item.external_id)
                item.status = status
                item.progress = progress

                if status == "completed":
                    from datetime import datetime
                    item.completed_at = datetime.utcnow()
                    await _handle_completed(db, item)

            except Exception:
                logger.exception("Failed to sync queue item %d", item.id)

        await db.commit()


async def _handle_completed(db, queue_item) -> None:
    """Post-process a completed download."""
    try:
        from app.services.postprocess import process_download
        await process_download(db, queue_item)
    except Exception:
        logger.exception("Post-processing failed for queue item %d", queue_item.id)


# ── qBittorrent ───────────────────────────────────────────────────────────────

def _qbit_base(client) -> str:
    scheme = "https" if client.use_ssl else "http"
    base = client.url_base.rstrip("/") if client.url_base else ""
    return f"{scheme}://{client.host}:{client.port}{base}"


async def _qbit_test(client) -> bool:
    password = decrypt_secret(client.password_enc) if client.password_enc else ""
    async with httpx.AsyncClient(base_url=_qbit_base(client)) as c:
        resp = await c.post(
            "/api/v2/auth/login",
            data={"username": client.username or "", "password": password},
        )
        return resp.text == "Ok."


async def _qbit_add(client, url: str, magnet: str | None = None) -> str | None:
    password = decrypt_secret(client.password_enc) if client.password_enc else ""
    async with httpx.AsyncClient(base_url=_qbit_base(client)) as c:
        await c.post(
            "/api/v2/auth/login",
            data={"username": client.username or "", "password": password},
        )
        payload: dict[str, Any] = {"category": client.category}
        if magnet:
            payload["urls"] = magnet
        else:
            payload["urls"] = url
        resp = await c.post("/api/v2/torrents/add", data=payload)
        if resp.status_code == 200 and resp.text == "Ok.":
            # Return torrent hash by querying last added
            info = await c.get("/api/v2/torrents/info", params={"sort": "added_on", "reverse": True, "limit": 1})
            torrents = info.json()
            if torrents:
                return torrents[0].get("hash")
    return None


# ── Transmission ──────────────────────────────────────────────────────────────

async def _transmission_test(client) -> bool:
    scheme = "https" if client.use_ssl else "http"
    base = f"{scheme}://{client.host}:{client.port}/transmission/rpc"
    async with httpx.AsyncClient() as c:
        resp = await c.get(base)
        return resp.status_code in (200, 409)


async def _transmission_add(client, url: str, magnet: str | None = None) -> str | None:
    scheme = "https" if client.use_ssl else "http"
    base = f"{scheme}://{client.host}:{client.port}/transmission/rpc"
    password = decrypt_secret(client.password_enc) if client.password_enc else ""
    auth = (client.username or "transmission", password) if client.username else None

    async with httpx.AsyncClient(auth=auth) as c:
        # Get session ID
        r = await c.get(base)
        session_id = r.headers.get("X-Transmission-Session-Id", "")

        payload = {
            "method": "torrent-add",
            "arguments": {"filename": magnet or url, "download-dir": f"/downloads/{client.category}"},
        }
        r = await c.post(base, json=payload, headers={"X-Transmission-Session-Id": session_id})
        data = r.json()
        if data.get("result") == "success":
            torrent = (
                data["arguments"].get("torrent-added")
                or data["arguments"].get("torrent-duplicate")
            )
            if torrent:
                return str(torrent.get("hashString"))
    return None


# ── SABnzbd ───────────────────────────────────────────────────────────────────

async def _sabnzbd_add(client, url: str) -> str | None:
    scheme = "https" if client.use_ssl else "http"
    api_key = decrypt_secret(client.api_key_enc) if client.api_key_enc else ""
    base = f"{scheme}://{client.host}:{client.port}"
    async with httpx.AsyncClient(base_url=base) as c:
        resp = await c.get(
            "/api",
            params={"apikey": api_key, "mode": "addurl", "name": url, "cat": client.category, "output": "json"},
        )
        data = resp.json()
        if data.get("status"):
            nzo_ids = data.get("nzo_ids", [])
            return nzo_ids[0] if nzo_ids else None
    return None


async def _nzb_test(client) -> bool:
    scheme = "https" if client.use_ssl else "http"
    api_key = decrypt_secret(client.api_key_enc) if client.api_key_enc else ""
    base = f"{scheme}://{client.host}:{client.port}"
    try:
        async with httpx.AsyncClient(base_url=base, timeout=5.0) as c:
            if client.type == "sabnzbd":
                resp = await c.get("/api", params={"apikey": api_key, "mode": "version", "output": "json"})
            else:  # nzbget
                resp = await c.post("/jsonrpc", json={"method": "version", "id": 1})
            return resp.status_code == 200
    except Exception:
        return False


async def _get_download_status(client, external_id: str):
    """Returns (status_str, progress_float) for the given external_id."""
    if client.type == "qbittorrent":
        return await _qbit_get_status(client, external_id)
    elif client.type == "transmission":
        return await _transmission_get_status(client, external_id)
    return "downloading", 0.0


async def _qbit_get_status(client, torrent_hash: str):
    password = decrypt_secret(client.password_enc) if client.password_enc else ""
    async with httpx.AsyncClient(base_url=_qbit_base(client)) as c:
        await c.post("/api/v2/auth/login", data={"username": client.username or "", "password": password})
        resp = await c.get("/api/v2/torrents/info", params={"hashes": torrent_hash})
        torrents = resp.json()
        if not torrents:
            return "queued", 0.0
        t = torrents[0]
        state = t.get("state", "")
        progress = t.get("progress", 0.0)
        if state in ("uploading", "stalledUP", "forcedUP", "checkingUP"):
            return "completed", 1.0
        elif state in ("downloading", "stalledDL", "forcedDL", "checkingDL"):
            return "downloading", progress
        elif state == "error":
            return "failed", progress
        return "downloading", progress


async def _transmission_get_status(client, torrent_hash: str):
    scheme = "https" if client.use_ssl else "http"
    base = f"{scheme}://{client.host}:{client.port}/transmission/rpc"
    password = decrypt_secret(client.password_enc) if client.password_enc else ""
    auth = (client.username or "transmission", password) if client.username else None

    async with httpx.AsyncClient(auth=auth) as c:
        r = await c.get(base)
        session_id = r.headers.get("X-Transmission-Session-Id", "")
        payload = {
            "method": "torrent-get",
            "arguments": {"fields": ["hashString", "status", "percentDone"], "ids": [torrent_hash]},
        }
        r = await c.post(base, json=payload, headers={"X-Transmission-Session-Id": session_id})
        data = r.json()
        torrents = data.get("arguments", {}).get("torrents", [])
        if not torrents:
            return "queued", 0.0
        t = torrents[0]
        # Transmission status: 0=stopped, 4=downloading, 6=seeding
        ts = t.get("status", 0)
        progress = t.get("percentDone", 0.0)
        if ts == 6:
            return "completed", 1.0
        elif ts == 4:
            return "downloading", progress
        return "downloading", progress
