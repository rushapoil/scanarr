from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db import models

router = APIRouter()


class CalendarEntry(BaseModel):
    chapter_id: int
    manga_id: int
    manga_title: str
    manga_cover: str | None
    chapter_number: float
    chapter_title: str | None
    release_date: datetime
    downloaded: bool


@router.get("", response_model=list[CalendarEntry])
async def get_calendar(
    start: date = Query(default_factory=lambda: date.today() - timedelta(days=7)),
    end: date = Query(default_factory=lambda: date.today() + timedelta(days=30)),
    unmonitored: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    q = (
        select(models.Chapter, models.Manga)
        .join(models.Manga, models.Chapter.manga_id == models.Manga.id)
        .where(
            models.Chapter.release_date >= start_dt,
            models.Chapter.release_date <= end_dt,
        )
        .order_by(models.Chapter.release_date)
    )

    if not unmonitored:
        q = q.where(models.Chapter.monitored == True, models.Manga.monitored == True)  # noqa: E712

    result = await db.execute(q)
    entries = []
    for chapter, manga in result.all():
        entries.append(CalendarEntry(
            chapter_id=chapter.id,
            manga_id=manga.id,
            manga_title=manga.title,
            manga_cover=manga.cover_local or manga.cover_url,
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title,
            release_date=chapter.release_date,
            downloaded=chapter.downloaded,
        ))
    return entries
