from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChapterFileOut(BaseModel):
    id: int
    path: str
    size: int | None
    format: str | None
    language: str | None
    scanlator_group: str | None
    model_config = {"from_attributes": True}


class ChapterOut(BaseModel):
    id: int
    manga_id: int
    chapter_number: float
    volume_number: int | None
    title: str | None
    mangadex_id: str | None
    monitored: bool
    downloaded: bool
    ignored: bool
    release_date: datetime | None
    download_date: datetime | None
    language: str | None
    scanlator_group: str | None
    files: list[ChapterFileOut] = []
    model_config = {"from_attributes": True}


class ChapterUpdate(BaseModel):
    monitored: bool | None = None
    ignored: bool | None = None
