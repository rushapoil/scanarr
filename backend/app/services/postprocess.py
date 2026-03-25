"""
Post-processing: rename & move downloaded chapter files into the library.
"""
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')


def sanitise(name: str, replace: bool = True) -> str:
    if replace:
        return _ILLEGAL_CHARS.sub("_", name).strip(". ")
    return name


def _resolve_template(template: str, manga_title: str, chapter_num: float, chapter_title: str | None) -> str:
    """
    Replace template tokens:
      {Manga Title}      → manga title
      {Chapter}          → chapter number (e.g. 1)
      {Chapter:00}       → zero-padded (e.g. 001)
      {Chapter Title}    → chapter title (empty string if None)
    """
    num_int = int(chapter_num)
    num_str = str(num_int) if chapter_num == num_int else str(chapter_num)

    result = template
    result = result.replace("{Manga Title}", manga_title)
    result = result.replace("{Chapter:00}", f"{num_int:03d}")
    result = result.replace("{Chapter}", num_str)
    result = result.replace("{Chapter Title}", chapter_title or "")
    # Clean up trailing dashes/spaces from empty tokens
    result = re.sub(r"\s*-\s*$", "", result).strip()
    return result


async def process_download(db, queue_item) -> None:
    """
    Called after a download is marked completed.
    1. Find the downloaded file(s) in the client's download dir.
    2. Rename according to NamingConfig.
    3. Move to library folder.
    4. Create ChapterFile record, mark Chapter as downloaded.
    5. Add History entry.
    6. Trigger notifications.
    """
    from sqlalchemy import select

    from app.db import models

    if not queue_item.chapter_id:
        logger.warning("Queue item %d has no chapter_id, skipping post-process", queue_item.id)
        return

    chapter = await db.get(models.Chapter, queue_item.chapter_id)
    if not chapter:
        return

    manga = await db.get(models.Manga, chapter.manga_id)
    if not manga:
        return

    # Get naming config
    nc_result = await db.execute(select(models.NamingConfig).where(models.NamingConfig.id == 1))
    nc = nc_result.scalar_one_or_none()
    folder_fmt = nc.folder_format if nc else "{Manga Title}"
    chapter_fmt = nc.chapter_format if nc else "{Manga Title} - Chapitre {Chapter:00}"
    rename = nc.rename_chapters if nc else True
    replace_illegal = nc.replace_illegal_chars if nc else True

    manga_title = sanitise(manga.title, replace=replace_illegal)
    folder_name = sanitise(
        _resolve_template(folder_fmt, manga_title, chapter.chapter_number, None),
        replace=replace_illegal,
    )
    chapter_name = sanitise(
        _resolve_template(chapter_fmt, manga_title, chapter.chapter_number, chapter.title),
        replace=replace_illegal,
    )

    dest_dir = Path(manga.root_folder_path) / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Find downloaded file — look in a conventional temp directory
    # The actual path depends on the download client setup; we look for files
    # matching the queue title in the expected download directory.
    src_file = _find_downloaded_file(queue_item)
    if not src_file:
        logger.warning("Could not find downloaded file for queue item %d", queue_item.id)
        queue_item.status = "failed"
        queue_item.error_message = "Downloaded file not found on disk"
        return

    ext = src_file.suffix.lower()
    if rename:
        dest_file = dest_dir / f"{chapter_name}{ext}"
    else:
        dest_file = dest_dir / src_file.name

    # Move file
    try:
        shutil.move(str(src_file), str(dest_file))
        logger.info("Moved %s → %s", src_file, dest_file)
    except OSError as exc:
        logger.error("File move failed: %s", exc)
        queue_item.status = "failed"
        queue_item.error_message = str(exc)
        return

    # Create ChapterFile record
    chapter_file = models.ChapterFile(
        chapter_id=chapter.id,
        path=str(dest_file),
        size=dest_file.stat().st_size,
        format=ext.lstrip("."),
        language=queue_item.language,
        scanlator_group=queue_item.scanlator_group,
    )
    db.add(chapter_file)

    # Mark chapter downloaded
    from datetime import datetime
    chapter.downloaded = True
    chapter.download_date = datetime.utcnow()
    chapter.language = queue_item.language
    chapter.scanlator_group = queue_item.scanlator_group

    # Update manga counter
    manga.downloaded_chapter_count = (manga.downloaded_chapter_count or 0) + 1

    # History entry
    db.add(models.History(
        manga_id=manga.id,
        chapter_id=chapter.id,
        event_type="downloadImported",
        source_title=queue_item.title,
        download_client=str(queue_item.download_client_id),
        quality=queue_item.quality,
        language=queue_item.language,
        size=dest_file.stat().st_size,
    ))

    await db.flush()

    # Notify
    try:
        from app.services.notify import dispatch
        await dispatch("on_download", manga=manga, chapter=chapter)
    except Exception:
        logger.exception("Notification failed after import")


def _find_downloaded_file(queue_item) -> Path | None:
    """
    Best-effort: look for a file matching the queue title in /downloads/<category>/.
    In production this would be configured per-client.
    """
    Path("/downloads") / (queue_item.download_url or "").split("/")[-1]
    # Simplified: just return None if we can't find it.
    # A real implementation would query the client for the save path.
    return None
