"""
MangaDex metadata service.
API docs: https://api.mangadex.org/docs/
"""
from __future__ import annotations

import json
import logging

import httpx

from app.schemas.manga import MangaDexResult

logger = logging.getLogger(__name__)

_MANGADEX_BASE = "https://api.mangadex.org"
_COVER_BASE = "https://uploads.mangadex.org/covers"

# httpx client shared within the process (connection pooling)
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=_MANGADEX_BASE,
            timeout=15.0,
            headers={"User-Agent": "Scanarr/0.1.0"},
        )
    return _client


def _extract_localised(obj: dict, langs: tuple = ("fr", "en", "ja-ro", "ja")) -> str:
    for lang in langs:
        if obj.get(lang):
            return obj[lang]
    # Fallback: first available
    for v in obj.values():
        if v:
            return v
    return ""


def _parse_manga_item(item: dict) -> MangaDexResult:
    attrs = item.get("attributes", {})
    rels = item.get("relationships", [])

    # Title
    title = _extract_localised(attrs.get("title", {}))

    # Alt titles
    alt_titles = []
    for alt in attrs.get("altTitles", []):
        for v in alt.values():
            if v and v != title:
                alt_titles.append(v)

    # Author / Artist
    author = artist = None
    for rel in rels:
        if rel["type"] == "author" and rel.get("attributes"):
            author = rel["attributes"].get("name")
        elif rel["type"] == "artist" and rel.get("attributes"):
            artist = rel["attributes"].get("name")

    # Cover
    cover_url = None
    for rel in rels:
        if rel["type"] == "cover_art" and rel.get("attributes"):
            filename = rel["attributes"].get("fileName", "")
            if filename:
                cover_url = f"{_COVER_BASE}/{item['id']}/{filename}.256.jpg"

    # Synopsis
    synopsis = _extract_localised(attrs.get("description", {}))

    # Tags / genres
    genres = []
    for tag in attrs.get("tags", []):
        name = _extract_localised(tag.get("attributes", {}).get("name", {}))
        if name:
            genres.append(name)

    # Status mapping
    status_map = {
        "ongoing": "ongoing",
        "completed": "completed",
        "hiatus": "hiatus",
        "cancelled": "cancelled",
    }
    raw_status = attrs.get("status", "ongoing")
    status = status_map.get(raw_status, "ongoing")

    # Year
    year = attrs.get("year")

    return MangaDexResult(
        mangadex_id=item["id"],
        title=title,
        title_alt=alt_titles[:5],
        author=author,
        artist=artist,
        synopsis=synopsis[:2000] if synopsis else None,
        cover_url=cover_url,
        status=status,
        year=year,
        genres=genres,
    )


async def search_mangadex(term: str, limit: int = 20) -> list[MangaDexResult]:
    """Search MangaDex by title, return parsed results."""
    client = _get_client()
    try:
        resp = await client.get(
            "/manga",
            params={
                "title": term,
                "limit": limit,
                "includes[]": ["author", "artist", "cover_art"],
                "order[relevance]": "desc",
                "contentRating[]": ["safe", "suggestive", "erotica"],
                "availableTranslatedLanguage[]": ["fr", "en"],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return [_parse_manga_item(item) for item in data.get("data", [])]
    except httpx.HTTPError as exc:
        logger.error("MangaDex search failed: %s", exc)
        return []


async def fetch_manga_by_id(mangadex_id: str) -> MangaDexResult | None:
    """Fetch a single manga's full metadata."""
    client = _get_client()
    try:
        resp = await client.get(
            f"/manga/{mangadex_id}",
            params={"includes[]": ["author", "artist", "cover_art"]},
        )
        resp.raise_for_status()
        return _parse_manga_item(resp.json()["data"])
    except httpx.HTTPError as exc:
        logger.error("MangaDex fetch %s failed: %s", mangadex_id, exc)
        return None


async def fetch_chapters_for_manga(
    mangadex_id: str,
    languages: list[str] | None = None,
) -> list[dict]:
    """Fetch all chapter metadata for a manga."""
    client = _get_client()
    if languages is None:
        languages = ["fr", "en"]

    chapters = []
    offset = 0
    limit = 100

    while True:
        try:
            resp = await client.get(
                "/chapter",
                params={
                    "manga": mangadex_id,
                    "translatedLanguage[]": languages,
                    "limit": limit,
                    "offset": offset,
                    "order[chapter]": "asc",
                    "includes[]": ["scanlation_group"],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            batch = data.get("data", [])
            chapters.extend(batch)

            total = data.get("total", 0)
            offset += limit
            if offset >= total:
                break
        except httpx.HTTPError as exc:
            logger.error("MangaDex chapter fetch failed: %s", exc)
            break

    return chapters


async def fetch_and_update_manga(db, manga) -> None:
    """Fetch metadata from MangaDex and update the manga ORM object in-place."""
    from app.db import models

    meta = await fetch_manga_by_id(manga.mangadex_id)
    if not meta:
        return

    manga.title = meta.title
    manga.title_alt = json.dumps(meta.title_alt)
    manga.author = meta.author
    manga.artist = meta.artist
    manga.synopsis = meta.synopsis
    manga.cover_url = meta.cover_url
    manga.status = meta.status
    manga.year = meta.year

    # Replace genres
    for g in list(manga.genres):
        await db.delete(g)
    manga.genres = [models.MangaGenre(genre=g) for g in meta.genres]

    # Sync chapters
    await _sync_chapters(db, manga)
    logger.info("Updated metadata for %s (%s)", manga.title, manga.mangadex_id)


async def _sync_chapters(db, manga) -> None:
    """Pull chapters from MangaDex and upsert into the DB."""
    from datetime import datetime

    from sqlalchemy import select

    from app.db import models

    # Determine languages from profile
    languages = ["fr", "en"]
    if manga.language_profile_id:
        lp = await db.get(models.LanguageProfile, manga.language_profile_id)
        if lp:
            languages = json.loads(lp.languages)

    raw_chapters = await fetch_chapters_for_manga(manga.mangadex_id, languages)

    existing_q = await db.execute(
        select(models.Chapter).where(models.Chapter.manga_id == manga.id)
    )
    existing = {
        (c.mangadex_id, c.language): c
        for c in existing_q.scalars().all()
        if c.mangadex_id
    }

    for raw in raw_chapters:
        attrs = raw.get("attributes", {})
        chapter_num_str = attrs.get("chapter")
        if chapter_num_str is None:
            continue
        try:
            chapter_num = float(chapter_num_str)
        except ValueError:
            continue

        lang = attrs.get("translatedLanguage", "en")
        published = attrs.get("publishAt")
        release_date = None
        if published:
            try:
                release_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Scanlation group
        group = None
        for rel in raw.get("relationships", []):
            if rel["type"] == "scanlation_group" and rel.get("attributes"):
                group = rel["attributes"].get("name")

        key = (raw["id"], lang)
        if key in existing:
            ch = existing[key]
            ch.release_date = release_date
            ch.scanlator_group = group
        else:
            ch = models.Chapter(
                manga_id=manga.id,
                chapter_number=chapter_num,
                volume_number=int(attrs["volume"]) if attrs.get("volume") else None,
                title=attrs.get("title") or None,
                mangadex_id=raw["id"],
                language=lang,
                scanlator_group=group,
                release_date=release_date,
                monitored=manga.monitored,
            )
            db.add(ch)

    # Update chapter counts
    await db.flush()
    count_q = await db.execute(
        select(models.Chapter).where(models.Chapter.manga_id == manga.id)
    )
    all_chapters = count_q.scalars().all()
    manga.chapter_count = len(all_chapters)
    manga.monitored_chapter_count = sum(1 for c in all_chapters if c.monitored)
    manga.downloaded_chapter_count = sum(1 for c in all_chapters if c.downloaded)


async def refresh_all_manga_metadata() -> None:
    """Called by the scheduler every METADATA_REFRESH_INTERVAL hours."""
    from sqlalchemy import select

    from app.db import models
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(models.Manga).where(models.Manga.monitored == True, models.Manga.mangadex_id.isnot(None))  # noqa: E712
        )
        mangas = result.scalars().all()
        logger.info("Refreshing metadata for %d mangas", len(mangas))
        for manga in mangas:
            try:
                await fetch_and_update_manga(db, manga)
            except Exception:
                logger.exception("Failed to refresh metadata for manga %d", manga.id)
        await db.commit()
