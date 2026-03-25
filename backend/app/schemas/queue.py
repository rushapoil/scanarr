from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class QueueItemOut(BaseModel):
    id: int
    manga_id: int | None
    chapter_id: int | None
    title: str
    protocol: str
    quality: str | None
    language: str | None
    scanlator_group: str | None
    size: int | None
    status: str
    progress: float
    error_message: str | None
    added_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    # Joined fields for display
    manga_title: str | None = None
    chapter_number: float | None = None
    indexer_name: str | None = None
    client_name: str | None = None

    model_config = {"from_attributes": True}


class QueuePage(BaseModel):
    total_count: int
    page: int
    page_size: int
    items: list[QueueItemOut]
