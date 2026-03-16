"""SQLAlchemy 2.0 ORM models — mirrors the validated data schema."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ── Manga & Chapters ──────────────────────────────────────────────────────────

class Manga(Base):
    __tablename__ = "manga"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    title_alt: Mapped[Optional[str]] = mapped_column(Text)          # JSON array of alt titles

    # External IDs
    mangadex_id: Mapped[Optional[str]] = mapped_column(Text, unique=True, index=True)
    anilist_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    mal_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)

    # Metadata
    author: Mapped[Optional[str]] = mapped_column(Text)
    artist: Mapped[Optional[str]] = mapped_column(Text)
    synopsis: Mapped[Optional[str]] = mapped_column(Text)
    cover_url: Mapped[Optional[str]] = mapped_column(Text)
    cover_local: Mapped[Optional[str]] = mapped_column(Text)        # /config/covers/<slug>.jpg

    # Publication
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ongoing")
    # ongoing | completed | hiatus | cancelled | upcoming
    year: Mapped[Optional[int]] = mapped_column(Integer)
    publisher: Mapped[Optional[str]] = mapped_column(Text)

    # Monitoring
    monitored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    monitor_status: Mapped[str] = mapped_column(Text, nullable=False, default="all")
    # all | future | missing | existing | first | latest | none

    # Profiles
    quality_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quality_profile.id", ondelete="SET NULL")
    )
    language_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("language_profile.id", ondelete="SET NULL")
    )

    # Library path
    root_folder_path: Mapped[str] = mapped_column(Text, nullable=False, default="/manga")
    folder_name: Mapped[Optional[str]] = mapped_column(Text)

    # Counters (denormalised for performance)
    chapter_count: Mapped[int] = mapped_column(Integer, default=0)
    monitored_chapter_count: Mapped[int] = mapped_column(Integer, default=0)
    downloaded_chapter_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    added_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    last_searched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    genres: Mapped[List["MangaGenre"]] = relationship(
        back_populates="manga", cascade="all, delete-orphan"
    )
    chapters: Mapped[List["Chapter"]] = relationship(
        back_populates="manga", cascade="all, delete-orphan", order_by="Chapter.chapter_number"
    )
    quality_profile: Mapped[Optional["QualityProfile"]] = relationship(foreign_keys=[quality_profile_id])
    language_profile: Mapped[Optional["LanguageProfile"]] = relationship(foreign_keys=[language_profile_id])


class MangaGenre(Base):
    __tablename__ = "manga_genre"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manga_id: Mapped[int] = mapped_column(Integer, ForeignKey("manga.id", ondelete="CASCADE"))
    genre: Mapped[str] = mapped_column(Text, nullable=False)

    manga: Mapped["Manga"] = relationship(back_populates="genres")


class Chapter(Base):
    __tablename__ = "chapter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    manga_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("manga.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chapter_number: Mapped[float] = mapped_column(Float, nullable=False)  # 1.5 for specials
    volume_number: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(Text)

    mangadex_id: Mapped[Optional[str]] = mapped_column(Text, index=True)

    # State
    monitored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    downloaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ignored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Dates
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    download_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Quality info
    language: Mapped[Optional[str]] = mapped_column(Text)       # fr | en | raw
    scanlator_group: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    manga: Mapped["Manga"] = relationship(back_populates="chapters")
    files: Mapped[List["ChapterFile"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )
    queue_items: Mapped[List["DownloadQueue"]] = relationship(back_populates="chapter")


class ChapterFile(Base):
    __tablename__ = "chapter_file"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False
    )

    path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    size: Mapped[Optional[int]] = mapped_column(Integer)            # bytes
    format: Mapped[Optional[str]] = mapped_column(Text)             # cbz | cbr | pdf | zip

    language: Mapped[Optional[str]] = mapped_column(Text)
    scanlator_group: Mapped[Optional[str]] = mapped_column(Text)
    release_group: Mapped[Optional[str]] = mapped_column(Text)
    sha256: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    chapter: Mapped["Chapter"] = relationship(back_populates="files")


# ── Quality & Language Profiles ───────────────────────────────────────────────

class QualityProfile(Base):
    __tablename__ = "quality_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    cutoff_id: Mapped[Optional[int]] = mapped_column(Integer)       # min acceptable quality rank

    items: Mapped[List["QualityProfileItem"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="QualityProfileItem.priority"
    )


class QualityProfileItem(Base):
    __tablename__ = "quality_profile_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quality_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quality_profile.id", ondelete="CASCADE"), nullable=False
    )
    quality: Mapped[str] = mapped_column(Text, nullable=False)   # best | web | raw
    allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["QualityProfile"] = relationship(back_populates="items")


class LanguageProfile(Base):
    __tablename__ = "language_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    languages: Mapped[str] = mapped_column(Text, nullable=False)    # JSON: ["fr","en","raw"]


# ── Prowlarr & Indexers ───────────────────────────────────────────────────────

class ProwlarrConfig(Base):
    __tablename__ = "prowlarr_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_enc: Mapped[str] = mapped_column(Text, nullable=False)  # Fernet-encrypted
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Indexer(Base):
    __tablename__ = "indexer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prowlarr_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    protocol: Mapped[str] = mapped_column(Text, nullable=False)     # torrent | usenet
    type: Mapped[Optional[str]] = mapped_column(Text)               # torznab | newznab | rss
    url: Mapped[Optional[str]] = mapped_column(Text)
    api_key_enc: Mapped[Optional[str]] = mapped_column(Text)        # Fernet-encrypted
    categories: Mapped[Optional[str]] = mapped_column(Text)         # JSON int array
    priority: Mapped[int] = mapped_column(Integer, default=25)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_rss_id: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ── Download Clients ──────────────────────────────────────────────────────────

class DownloadClient(Base):
    __tablename__ = "download_client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    # qbittorrent | transmission | deluge | sabnzbd | nzbget

    host: Mapped[str] = mapped_column(Text, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=False)
    url_base: Mapped[Optional[str]] = mapped_column(Text)
    username: Mapped[Optional[str]] = mapped_column(Text)
    password_enc: Mapped[Optional[str]] = mapped_column(Text)       # Fernet-encrypted
    api_key_enc: Mapped[Optional[str]] = mapped_column(Text)        # Fernet-encrypted

    category: Mapped[str] = mapped_column(Text, default="scanarr")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    queue_items: Mapped[List["DownloadQueue"]] = relationship(back_populates="download_client")


# ── Download Queue & History ──────────────────────────────────────────────────

class DownloadQueue(Base):
    __tablename__ = "download_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    manga_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("manga.id", ondelete="SET NULL"))
    chapter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chapter.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(Text, nullable=False)
    indexer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("indexer.id", ondelete="SET NULL"))
    download_url: Mapped[str] = mapped_column(Text, nullable=False)
    magnet_uri: Mapped[Optional[str]] = mapped_column(Text)
    protocol: Mapped[str] = mapped_column(Text, nullable=False)     # torrent | usenet

    download_client_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("download_client.id", ondelete="SET NULL")
    )
    external_id: Mapped[Optional[str]] = mapped_column(Text)        # hash / nzb ID

    quality: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text)
    scanlator_group: Mapped[Optional[str]] = mapped_column(Text)
    size: Mapped[Optional[int]] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    # queued | downloading | completed | failed | ignored | paused
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    added_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    manga: Mapped[Optional["Manga"]] = relationship()
    chapter: Mapped[Optional["Chapter"]] = relationship(back_populates="queue_items")
    download_client: Mapped[Optional["DownloadClient"]] = relationship(back_populates="queue_items")
    indexer: Mapped[Optional["Indexer"]] = relationship()


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    manga_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("manga.id", ondelete="SET NULL"))
    chapter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chapter.id", ondelete="SET NULL"))

    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    # grabbed | downloadFailed | downloadImported | downloadIgnored | chapterFileDeleted

    source_title: Mapped[Optional[str]] = mapped_column(Text)
    indexer: Mapped[Optional[str]] = mapped_column(Text)
    download_client: Mapped[Optional[str]] = mapped_column(Text)
    quality: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text)
    size: Mapped[Optional[int]] = mapped_column(Integer)
    data: Mapped[Optional[str]] = mapped_column(Text)               # JSON blob

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    manga: Mapped[Optional["Manga"]] = relationship()
    chapter: Mapped[Optional["Chapter"]] = relationship()


# ── Notifications ─────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    # discord | telegram | webhook | email | slack

    settings_enc: Mapped[str] = mapped_column(Text, nullable=False)     # Fernet-encrypted JSON

    on_grab: Mapped[bool] = mapped_column(Boolean, default=True)
    on_download: Mapped[bool] = mapped_column(Boolean, default=True)
    on_upgrade: Mapped[bool] = mapped_column(Boolean, default=False)
    on_rename: Mapped[bool] = mapped_column(Boolean, default=False)
    on_chapter_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    on_health_issue: Mapped[bool] = mapped_column(Boolean, default=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ── System ────────────────────────────────────────────────────────────────────

class RootFolder(Base):
    __tablename__ = "root_folder"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    free_space: Mapped[Optional[int]] = mapped_column(Integer)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class NamingConfig(Base):
    __tablename__ = "naming_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    rename_chapters: Mapped[bool] = mapped_column(Boolean, default=True)
    replace_illegal_chars: Mapped[bool] = mapped_column(Boolean, default=True)
    folder_format: Mapped[str] = mapped_column(Text, default="{Manga Title}")
    chapter_format: Mapped[str] = mapped_column(
        Text, default="{Manga Title} - Chapitre {Chapter:00} - {Chapter Title}"
    )


class AppConfig(Base):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    log_level: Mapped[str] = mapped_column(Text, default="info")
    update_interval: Mapped[int] = mapped_column(Integer, default=60)

    api_key: Mapped[str] = mapped_column(Text, nullable=False)      # raw token, generated at init
    auth_required: Mapped[bool] = mapped_column(Boolean, default=True)
