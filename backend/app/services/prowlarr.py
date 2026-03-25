"""
Prowlarr integration service.
Handles indexer sync and release searching via the Prowlarr API.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.security import decrypt_secret

logger = logging.getLogger(__name__)


def _client(base_url: str, api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"X-Api-Key": api_key, "User-Agent": "Scanarr/0.1.0"},
        timeout=15.0,
    )


async def test_connection(url: str, api_key: str) -> bool:
    try:
        async with _client(url, api_key) as c:
            resp = await c.get("/api/v1/system/status")
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Prowlarr test connection failed: %s", exc)
        return False


async def fetch_indexers(url: str, api_key: str) -> list[dict[str, Any]]:
    """Return list of indexer objects from Prowlarr."""
    async with _client(url, api_key) as c:
        resp = await c.get("/api/v1/indexer")
        resp.raise_for_status()
        return resp.json()


async def sync_indexers_from_prowlarr(db, cfg) -> None:
    """Pull indexers from Prowlarr and upsert into local DB."""
    from sqlalchemy import select

    from app.db import models

    api_key = decrypt_secret(cfg.api_key_enc)
    try:
        raw_indexers = await fetch_indexers(cfg.url, api_key)
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch indexers from Prowlarr: %s", exc)
        return

    for raw in raw_indexers:
        prowlarr_id = raw.get("id")
        if not prowlarr_id:
            continue

        result = await db.execute(
            select(models.Indexer).where(models.Indexer.prowlarr_id == prowlarr_id)
        )
        indexer = result.scalar_one_or_none()

        protocol = "torrent" if raw.get("protocol", "").lower() == "torrent" else "usenet"
        cats = [str(c.get("id", "")) for c in raw.get("capabilities", {}).get("categories", [])]

        if indexer:
            indexer.name = raw.get("name", indexer.name)
            indexer.protocol = protocol
            indexer.enabled = raw.get("enable", True)
        else:
            indexer = models.Indexer(
                prowlarr_id=prowlarr_id,
                name=raw.get("name", f"Indexer {prowlarr_id}"),
                protocol=protocol,
                type="torznab" if protocol == "torrent" else "newznab",
                categories=str(cats),
                enabled=raw.get("enable", True),
            )
            db.add(indexer)

    from datetime import datetime
    cfg.last_sync = datetime.utcnow()
    await db.commit()
    logger.info("Synced %d indexers from Prowlarr", len(raw_indexers))


async def search_releases(
    url: str,
    api_key: str,
    query: str,
    categories: list[int] | None = None,
    indexer_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    """
    Search for releases via Prowlarr's /api/v1/search endpoint.
    Returns a list of release dicts.
    """
    params: dict[str, Any] = {"query": query, "type": "search"}
    if categories:
        params["categories"] = categories
    if indexer_ids:
        params["indexerIds"] = indexer_ids

    try:
        async with _client(url, api_key) as c:
            resp = await c.get("/api/v1/search", params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        logger.error("Prowlarr search failed: %s", exc)
        return []


async def fetch_rss(url: str, api_key: str, indexer_id: int) -> list[dict[str, Any]]:
    """Fetch RSS feed from a specific Prowlarr indexer."""
    try:
        async with _client(url, api_key) as c:
            resp = await c.get(
                "/api/v1/newznab",
                params={"t": "rss", "indexerIds": [indexer_id], "limit": 100},
            )
            resp.raise_for_status()
            import feedparser
            feed = feedparser.parse(resp.text)
            return feed.entries
    except Exception as exc:
        logger.error("RSS fetch failed for indexer %d: %s", indexer_id, exc)
        return []
