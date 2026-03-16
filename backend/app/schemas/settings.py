from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ── Prowlarr ──────────────────────────────────────────────────────────────────

class ProwlarrConfigIn(BaseModel):
    url: str
    api_key: str
    enabled: bool = True


class ProwlarrConfigOut(BaseModel):
    id: int
    url: str
    enabled: bool
    last_sync: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Indexers ──────────────────────────────────────────────────────────────────

class IndexerOut(BaseModel):
    id: int
    prowlarr_id: Optional[int]
    name: str
    protocol: str
    type: Optional[str]
    priority: int
    enabled: bool
    model_config = {"from_attributes": True}


# ── Download Clients ──────────────────────────────────────────────────────────

class DownloadClientIn(BaseModel):
    name: str
    type: str
    host: str
    port: int
    use_ssl: bool = False
    url_base: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None     # plain — will be encrypted before storage
    api_key: Optional[str] = None      # plain — will be encrypted before storage
    category: str = "scanarr"
    priority: int = 0
    enabled: bool = True
    is_default: bool = False


class DownloadClientOut(BaseModel):
    id: int
    name: str
    type: str
    host: str
    port: int
    use_ssl: bool
    url_base: Optional[str]
    username: Optional[str]
    category: str
    priority: int
    enabled: bool
    is_default: bool
    model_config = {"from_attributes": True}


# ── Quality Profiles ──────────────────────────────────────────────────────────

class QualityProfileItemOut(BaseModel):
    id: int
    quality: str
    allowed: bool
    priority: int
    model_config = {"from_attributes": True}


class QualityProfileOut(BaseModel):
    id: int
    name: str
    is_default: bool
    items: List[QualityProfileItemOut] = []
    model_config = {"from_attributes": True}


# ── Language Profiles ─────────────────────────────────────────────────────────

class LanguageProfileOut(BaseModel):
    id: int
    name: str
    languages: List[str]
    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_parse(cls, obj):
        import json
        langs = json.loads(obj.languages) if isinstance(obj.languages, str) else obj.languages
        return cls(id=obj.id, name=obj.name, languages=langs)


# ── Naming Config ─────────────────────────────────────────────────────────────

class NamingConfigIn(BaseModel):
    rename_chapters: bool = True
    replace_illegal_chars: bool = True
    folder_format: str = "{Manga Title}"
    chapter_format: str = "{Manga Title} - Chapitre {Chapter:00} - {Chapter Title}"


class NamingConfigOut(NamingConfigIn):
    id: int
    model_config = {"from_attributes": True}


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationIn(BaseModel):
    name: str
    type: str
    settings: dict   # type-specific config (webhook url, token, etc.)
    on_grab: bool = True
    on_download: bool = True
    on_upgrade: bool = False
    on_rename: bool = False
    on_chapter_delete: bool = False
    on_health_issue: bool = True
    enabled: bool = True


class NotificationOut(BaseModel):
    id: int
    name: str
    type: str
    on_grab: bool
    on_download: bool
    on_upgrade: bool
    on_rename: bool
    on_chapter_delete: bool
    on_health_issue: bool
    enabled: bool
    model_config = {"from_attributes": True}


# ── Root Folder ───────────────────────────────────────────────────────────────

class RootFolderOut(BaseModel):
    id: int
    path: str
    free_space: Optional[int]
    is_default: bool
    model_config = {"from_attributes": True}
