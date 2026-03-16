from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QueueItemOut(BaseModel):
    id: int
    manga_id: Optional[int]
    chapter_id: Optional[int]
    title: str
    protocol: str
    quality: Optional[str]
    language: Optional[str]
    scanlator_group: Optional[str]
    size: Optional[int]
    status: str
    progress: float
    error_message: Optional[str]
    added_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Joined fields for display
    manga_title: Optional[str] = None
    chapter_number: Optional[float] = None
    indexer_name: Optional[str] = None
    client_name: Optional[str] = None

    model_config = {"from_attributes": True}


class QueuePage(BaseModel):
    total_count: int
    page: int
    page_size: int
    items: list[QueueItemOut]
