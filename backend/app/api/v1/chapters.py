from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.db import models
from app.schemas.chapter import ChapterOut, ChapterUpdate

router = APIRouter()


@router.get("/manga/{manga_id}", response_model=List[ChapterOut])
async def list_chapters(
    manga_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Chapter)
        .where(models.Chapter.manga_id == manga_id)
        .options(selectinload(models.Chapter.files))
        .order_by(models.Chapter.chapter_number)
    )
    return result.scalars().all()


@router.get("/{chapter_id}", response_model=ChapterOut)
async def get_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Chapter)
        .where(models.Chapter.id == chapter_id)
        .options(selectinload(models.Chapter.files))
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.put("/{chapter_id}", response_model=ChapterOut)
async def update_chapter(
    chapter_id: int,
    body: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Chapter).where(models.Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(chapter, field, value)

    await db.commit()
    await db.refresh(chapter)
    return chapter


@router.post("/{chapter_id}/search", status_code=202)
async def search_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Trigger a manual search for this specific chapter."""
    result = await db.execute(
        select(models.Chapter)
        .where(models.Chapter.id == chapter_id)
        .options(selectinload(models.Chapter.manga))
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    from app.services.monitor import search_chapter
    await search_chapter(db, chapter)
    return {"message": f"Search triggered for chapter {chapter.chapter_number}"}
