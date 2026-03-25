from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db import models

router = APIRouter()


class HistoryItemOut(BaseModel):
    id: int
    manga_id: int | None
    chapter_id: int | None
    event_type: str
    source_title: str | None
    indexer: str | None
    download_client: str | None
    quality: str | None
    language: str | None
    size: int | None
    created_at: datetime
    manga_title: str | None = None
    chapter_number: float | None = None
    model_config = {"from_attributes": True}


class HistoryPage(BaseModel):
    total_count: int
    page: int
    page_size: int
    items: list[HistoryItemOut]


@router.get("", response_model=HistoryPage)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: str | None = None,
    manga_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    q = select(models.History).order_by(models.History.created_at.desc())
    if event_type:
        q = q.where(models.History.event_type == event_type)
    if manga_id:
        q = q.where(models.History.manga_id == manga_id)

    total_q = await db.execute(
        select(func.count()).select_from(q.subquery())
    )
    total = total_q.scalar_one()

    items_q = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = items_q.scalars().all()

    out = []
    for item in items:
        d = HistoryItemOut.model_validate(item)
        if item.manga_id:
            m = await db.get(models.Manga, item.manga_id)
            if m:
                d.manga_title = m.title
        if item.chapter_id:
            c = await db.get(models.Chapter, item.chapter_id)
            if c:
                d.chapter_number = c.chapter_number
        out.append(d)

    return HistoryPage(total_count=total, page=page, page_size=page_size, items=out)
