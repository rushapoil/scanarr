from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChapterFileOut(BaseModel):
    id: int
    path: str
    size: Optional[int]
    format: Optional[str]
    language: Optional[str]
    scanlator_group: Optional[str]
    model_config = {"from_attributes": True}


class ChapterOut(BaseModel):
    id: int
    manga_id: int
    chapter_number: float
    volume_number: Optional[int]
    title: Optional[str]
    mangadex_id: Optional[str]
    monitored: bool
    downloaded: bool
    ignored: bool
    release_date: Optional[datetime]
    download_date: Optional[datetime]
    language: Optional[str]
    scanlator_group: Optional[str]
    files: List[ChapterFileOut] = []
    model_config = {"from_attributes": True}


class ChapterUpdate(BaseModel):
    monitored: Optional[bool] = None
    ignored: Optional[bool] = None
