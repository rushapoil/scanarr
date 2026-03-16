from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db import models
from app.schemas.queue import QueueItemOut, QueuePage

router = APIRouter()


@router.get("", response_model=QueuePage)
async def get_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    total_q = await db.execute(select(func.count()).select_from(models.DownloadQueue))
    total = total_q.scalar_one()

    items_q = await db.execute(
        select(models.DownloadQueue)
        .order_by(models.DownloadQueue.added_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = items_q.scalars().all()

    # Enrich with display names
    out = []
    for item in items:
        d = QueueItemOut.model_validate(item)
        if item.manga_id:
            m = await db.get(models.Manga, item.manga_id)
            if m:
                d.manga_title = m.title
        if item.chapter_id:
            c = await db.get(models.Chapter, item.chapter_id)
            if c:
                d.chapter_number = c.chapter_number
        if item.indexer_id:
            idx = await db.get(models.Indexer, item.indexer_id)
            if idx:
                d.indexer_name = idx.name
        if item.download_client_id:
            cl = await db.get(models.DownloadClient, item.download_client_id)
            if cl:
                d.client_name = cl.name
        out.append(d)

    return QueuePage(total_count=total, page=page, page_size=page_size, items=out)


@router.delete("/{item_id}", status_code=204)
async def remove_from_queue(
    item_id: int,
    blacklist: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    item = await db.get(models.DownloadQueue, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    await db.delete(item)
    await db.commit()
