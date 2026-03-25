"""
Monitor service: searches for missing chapters and grabs matching releases.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def run_rss_monitor() -> None:
    """Scheduled job: scan RSS feeds and grab matching releases."""
    from sqlalchemy import select

    from app.core.security import decrypt_secret
    from app.db import models
    from app.db.database import AsyncSessionLocal
    from app.services.prowlarr import fetch_rss

    async with AsyncSessionLocal() as db:
        # Get Prowlarr config
        result = await db.execute(
            select(models.ProwlarrConfig).where(models.ProwlarrConfig.id == 1)
        )
        prowlarr_cfg = result.scalar_one_or_none()
        if not prowlarr_cfg or not prowlarr_cfg.enabled:
            return

        api_key = decrypt_secret(prowlarr_cfg.api_key_enc)

        # Get enabled indexers
        indexers_q = await db.execute(
            select(models.Indexer).where(models.Indexer.enabled == True)  # noqa: E712
        )
        indexers = indexers_q.scalars().all()

        for indexer in indexers:
            if not indexer.prowlarr_id:
                continue
            entries = await fetch_rss(prowlarr_cfg.url, api_key, indexer.prowlarr_id)
            for entry in entries:
                await _process_rss_entry(db, entry, indexer)

        await db.commit()


async def _process_rss_entry(db, entry: dict, indexer) -> None:
    """Check if an RSS entry matches a monitored manga/chapter and grab it."""
    title = entry.get("title", "")
    if not title:
        return

    from sqlalchemy import select

    from app.db import models

    # Find monitored mangas that match this title
    mangas_q = await db.execute(
        select(models.Manga).where(models.Manga.monitored == True)  # noqa: E712
    )
    for manga in mangas_q.scalars().all():
        if manga.title.lower() not in title.lower():
            continue
        # Check if this looks like a chapter release and which chapter it might be
        chapter_num = _extract_chapter_number(title)
        if chapter_num is None:
            continue

        # Find the chapter
        chapter_q = await db.execute(
            select(models.Chapter).where(
                models.Chapter.manga_id == manga.id,
                models.Chapter.chapter_number == chapter_num,
                models.Chapter.monitored == True,  # noqa: E712
                models.Chapter.downloaded == False,  # noqa: E712
            )
        )
        chapter = chapter_q.scalar_one_or_none()
        if not chapter:
            continue

        # Grab it
        await _grab_release(db, manga, chapter, entry, indexer)
        return


def _extract_chapter_number(title: str) -> float | None:
    """Heuristic: extract chapter number from a release title."""
    import re
    patterns = [
        r"[Cc]h(?:apter|ap)?[\s._-]*(\d+(?:\.\d+)?)",
        r"[Cc]hapitre[\s._-]*(\d+(?:\.\d+)?)",
        r"[\s._-][Cc](\d+(?:\.\d+)?)[\s._-]",
        r"#(\d+(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, title)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


async def _grab_release(db, manga, chapter, entry: dict, indexer) -> None:
    """Add a release to the download queue and send it to the download client."""
    from datetime import datetime

    from sqlalchemy import select

    from app.db import models

    # Avoid duplicate grabs
    existing_q = await db.execute(
        select(models.DownloadQueue).where(
            models.DownloadQueue.chapter_id == chapter.id,
            models.DownloadQueue.status.in_(["queued", "downloading"]),
        )
    )
    if existing_q.scalar_one_or_none():
        return

    download_url = entry.get("link") or entry.get("enclosures", [{}])[0].get("url", "")
    if not download_url:
        return

    # Find default download client
    client_q = await db.execute(
        select(models.DownloadClient).where(
            models.DownloadClient.enabled == True,  # noqa: E712
            models.DownloadClient.is_default == True,  # noqa: E712
        )
    )
    client = client_q.scalar_one_or_none()
    if not client:
        # Fall back to any enabled client
        client_q = await db.execute(
            select(models.DownloadClient).where(models.DownloadClient.enabled == True)  # noqa: E712
        )
        client = client_q.scalar_one_or_none()

    queue_item = models.DownloadQueue(
        manga_id=manga.id,
        chapter_id=chapter.id,
        title=entry.get("title", ""),
        indexer_id=indexer.id,
        download_url=download_url,
        protocol=indexer.protocol,
        language=chapter.language,
        status="queued",
        added_at=datetime.utcnow(),
    )

    if client:
        from app.services.download import add_download
        external_id = await add_download(client, download_url)
        if external_id:
            queue_item.download_client_id = client.id
            queue_item.external_id = external_id
            queue_item.status = "downloading"
            queue_item.started_at = datetime.utcnow()

    db.add(queue_item)

    # History: grabbed
    db.add(models.History(
        manga_id=manga.id,
        chapter_id=chapter.id,
        event_type="grabbed",
        source_title=entry.get("title", ""),
        indexer=indexer.name,
        download_client=client.name if client else None,
        language=chapter.language,
    ))

    # Notify
    try:
        from app.services.notify import dispatch
        await dispatch("on_grab", manga=manga, chapter=chapter)
    except Exception:
        logger.exception("Grab notification failed")

    logger.info("Grabbed: %s (chapter %.1f)", manga.title, chapter.chapter_number)


async def search_missing_chapters(db, manga) -> None:
    """Trigger a manual Prowlarr search for all missing monitored chapters."""
    from sqlalchemy import select

    from app.core.security import decrypt_secret
    from app.db import models
    from app.services.prowlarr import search_releases

    prowlarr_q = await db.execute(
        select(models.ProwlarrConfig).where(models.ProwlarrConfig.id == 1)
    )
    cfg = prowlarr_q.scalar_one_or_none()
    if not cfg:
        logger.warning("Prowlarr not configured, skipping manual search")
        return

    api_key = decrypt_secret(cfg.api_key_enc)

    missing_q = await db.execute(
        select(models.Chapter).where(
            models.Chapter.manga_id == manga.id,
            models.Chapter.monitored == True,  # noqa: E712
            models.Chapter.downloaded == False,  # noqa: E712
            models.Chapter.ignored == False,  # noqa: E712
        )
    )
    missing = missing_q.scalars().all()
    if not missing:
        return

    query = f"{manga.title}"
    results = await search_releases(cfg.url, api_key, query)
    logger.info("Manual search for %s: %d results", manga.title, len(results))
    # TODO: score results against quality/language profile and grab best match


async def search_chapter(db, chapter) -> None:
    """Trigger a manual search for a single chapter."""

    from app.db import models

    manga = await db.get(models.Manga, chapter.manga_id)
    if manga:
        await search_missing_chapters(db, manga)
