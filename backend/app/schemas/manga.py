from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator


# ── Genre ─────────────────────────────────────────────────────────────────────

class GenreOut(BaseModel):
    id: int
    genre: str
    model_config = {"from_attributes": True}


# ── Chapter (brief, embedded in manga response) ───────────────────────────────

class ChapterBrief(BaseModel):
    id: int
    chapter_number: float
    volume_number: Optional[int]
    title: Optional[str]
    monitored: bool
    downloaded: bool
    release_date: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Manga ─────────────────────────────────────────────────────────────────────

class MangaBase(BaseModel):
    title: str
    monitored: bool = True
    monitor_status: str = "all"
    root_folder_path: str = "/manga"
    quality_profile_id: Optional[int] = None
    language_profile_id: Optional[int] = None


class MangaCreate(MangaBase):
    """Used when adding a manga by MangaDex ID or by search result."""
    mangadex_id: Optional[str] = None


class MangaUpdate(BaseModel):
    title: Optional[str] = None
    monitored: Optional[bool] = None
    monitor_status: Optional[str] = None
    root_folder_path: Optional[str] = None
    quality_profile_id: Optional[int] = None
    language_profile_id: Optional[int] = None


class MangaOut(MangaBase):
    id: int
    title_slug: str
    title_alt: Optional[List[str]] = None
    mangadex_id: Optional[str] = None
    anilist_id: Optional[int] = None
    mal_id: Optional[int] = None

    author: Optional[str] = None
    artist: Optional[str] = None
    synopsis: Optional[str] = None
    cover_url: Optional[str] = None
    cover_local: Optional[str] = None

    status: str
    year: Optional[int] = None
    publisher: Optional[str] = None

    chapter_count: int
    monitored_chapter_count: int
    downloaded_chapter_count: int

    added_at: datetime
    updated_at: datetime
    last_searched_at: Optional[datetime] = None

    genres: List[GenreOut] = []

    model_config = {"from_attributes": True}

    @field_validator("title_alt", mode="before")
    @classmethod
    def parse_title_alt(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []


class MangaDetail(MangaOut):
    """Full manga with chapters list."""
    chapters: List[ChapterBrief] = []


# ── MangaDex search result (before adding to library) ────────────────────────

class MangaDexResult(BaseModel):
    mangadex_id: str
    title: str
    title_alt: List[str] = []
    author: Optional[str] = None
    artist: Optional[str] = None
    synopsis: Optional[str] = None
    cover_url: Optional[str] = None
    status: str
    year: Optional[int] = None
    genres: List[str] = []
    already_in_library: bool = False
