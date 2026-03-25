from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, field_validator

# ── Genre ─────────────────────────────────────────────────────────────────────

class GenreOut(BaseModel):
    id: int
    genre: str
    model_config = {"from_attributes": True}


# ── Chapter (brief, embedded in manga response) ───────────────────────────────

class ChapterBrief(BaseModel):
    id: int
    chapter_number: float
    volume_number: int | None
    title: str | None
    monitored: bool
    downloaded: bool
    release_date: datetime | None
    model_config = {"from_attributes": True}


# ── Manga ─────────────────────────────────────────────────────────────────────

class MangaBase(BaseModel):
    title: str
    monitored: bool = True
    monitor_status: str = "all"
    root_folder_path: str = "/manga"
    quality_profile_id: int | None = None
    language_profile_id: int | None = None


class MangaCreate(MangaBase):
    """Used when adding a manga by MangaDex ID or by search result."""
    mangadex_id: str | None = None


class MangaUpdate(BaseModel):
    title: str | None = None
    monitored: bool | None = None
    monitor_status: str | None = None
    root_folder_path: str | None = None
    quality_profile_id: int | None = None
    language_profile_id: int | None = None


class MangaOut(MangaBase):
    id: int
    title_slug: str
    title_alt: list[str] | None = None
    mangadex_id: str | None = None
    anilist_id: int | None = None
    mal_id: int | None = None

    author: str | None = None
    artist: str | None = None
    synopsis: str | None = None
    cover_url: str | None = None
    cover_local: str | None = None

    status: str
    year: int | None = None
    publisher: str | None = None

    chapter_count: int
    monitored_chapter_count: int
    downloaded_chapter_count: int

    added_at: datetime
    updated_at: datetime
    last_searched_at: datetime | None = None

    genres: list[GenreOut] = []

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
    chapters: list[ChapterBrief] = []


# ── MangaDex search result (before adding to library) ────────────────────────

class MangaDexResult(BaseModel):
    mangadex_id: str
    title: str
    title_alt: list[str] = []
    author: str | None = None
    artist: str | None = None
    synopsis: str | None = None
    cover_url: str | None = None
    status: str
    year: int | None = None
    genres: list[str] = []
    already_in_library: bool = False
