"""
Manga endpoints — mirrors Sonarr's /api/v3/series pattern.
"""
from __future__ import annotations

import json
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.db import models
from app.schemas.manga import MangaCreate, MangaDetail, MangaOut, MangaUpdate, MangaDexResult

router = APIRouter()


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:100]


# ── GET /manga ────────────────────────────────────────────────────────────────

@router.get("", response_model=List[MangaOut])
async def list_manga(
    monitored: Optional[bool] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    q = select(models.Manga).options(
        selectinload(models.Manga.genres),
    ).order_by(models.Manga.title)

    if monitored is not None:
        q = q.where(models.Manga.monitored == monitored)
    if status:
        q = q.where(models.Manga.status == status)

    result = await db.execute(q)
    return result.scalars().all()


# ── GET /manga/{id} ───────────────────────────────────────────────────────────

@router.get("/{manga_id}", response_model=MangaDetail)
async def get_manga(
    manga_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Manga)
        .where(models.Manga.id == manga_id)
        .options(
            selectinload(models.Manga.genres),
            selectinload(models.Manga.chapters),
        )
    )
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    return manga


# ── POST /manga ───────────────────────────────────────────────────────────────

@router.post("", response_model=MangaOut, status_code=status.HTTP_201_CREATED)
async def add_manga(
    body: MangaCreate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    # Check duplicate
    if body.mangadex_id:
        existing = await db.execute(
            select(models.Manga).where(models.Manga.mangadex_id == body.mangadex_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Manga already in library")

    slug = _slugify(body.title)
    # Ensure slug uniqueness by counting existing slugs with the same prefix
    count_q = await db.execute(
        select(func.count(models.Manga.id)).where(models.Manga.title_slug.like(f"{slug}%"))
    )
    count = count_q.scalar_one()
    if count:
        slug = f"{slug}-{count + 1}"

    manga = models.Manga(
        title=body.title,
        title_slug=slug,
        mangadex_id=body.mangadex_id,
        monitored=body.monitored,
        monitor_status=body.monitor_status,
        root_folder_path=body.root_folder_path,
        quality_profile_id=body.quality_profile_id,
        language_profile_id=body.language_profile_id,
        folder_name=body.title,
    )
    db.add(manga)
    await db.flush()

    # Fetch metadata from MangaDex if we have an ID
    if body.mangadex_id:
        try:
            from app.services.metadata import fetch_and_update_manga
            await fetch_and_update_manga(db, manga)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Metadata fetch failed: %s", exc)

    await db.commit()
    await db.refresh(manga)
    return manga


# ── PUT /manga/{id} ───────────────────────────────────────────────────────────

@router.put("/{manga_id}", response_model=MangaOut)
async def update_manga(
    manga_id: int,
    body: MangaUpdate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Manga).where(models.Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(manga, field, value)

    await db.commit()
    await db.refresh(manga)
    return manga


# ── DELETE /manga/{id} ────────────────────────────────────────────────────────

@router.delete("/{manga_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga(
    manga_id: int,
    delete_files: bool = Query(False, description="Also delete downloaded files"),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Manga).where(models.Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")

    if delete_files:
        # Collect and delete all chapter files
        files_q = await db.execute(
            select(models.ChapterFile)
            .join(models.Chapter)
            .where(models.Chapter.manga_id == manga_id)
        )
        for cf in files_q.scalars().all():
            from pathlib import Path
            try:
                Path(cf.path).unlink(missing_ok=True)
            except Exception:
                pass

    await db.delete(manga)
    await db.commit()


# ── POST /manga/lookup ────────────────────────────────────────────────────────

@router.get("/lookup/search", response_model=List[MangaDexResult])
async def lookup_manga(
    term: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Search MangaDex and annotate results with library membership."""
    from app.services.metadata import search_mangadex
    results = await search_mangadex(term)

    # Check which are already in library
    if results:
        ids = [r.mangadex_id for r in results]
        existing_q = await db.execute(
            select(models.Manga.mangadex_id).where(models.Manga.mangadex_id.in_(ids))
        )
        in_library = {row[0] for row in existing_q.all()}
        for r in results:
            r.already_in_library = r.mangadex_id in in_library

    return results


# ── POST /manga/{id}/search ───────────────────────────────────────────────────

@router.post("/{manga_id}/search", status_code=status.HTTP_202_ACCEPTED)
async def trigger_search(
    manga_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Trigger a manual search for missing chapters via Prowlarr."""
    result = await db.execute(select(models.Manga).where(models.Manga.id == manga_id))
    manga = result.scalar_one_or_none()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")

    from app.services.monitor import search_missing_chapters
    await search_missing_chapters(db, manga)
    return {"message": f"Search triggered for {manga.title}"}
