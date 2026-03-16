"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quality_profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("is_default", sa.Boolean, nullable=False, default=False),
        sa.Column("cutoff_id", sa.Integer),
    )

    op.create_table(
        "quality_profile_item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("quality_profile_id", sa.Integer, sa.ForeignKey("quality_profile.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quality", sa.Text, nullable=False),
        sa.Column("allowed", sa.Boolean, nullable=False, default=True),
        sa.Column("priority", sa.Integer, nullable=False, default=0),
    )

    op.create_table(
        "language_profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("languages", sa.Text, nullable=False),
    )

    op.create_table(
        "manga",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("title_slug", sa.Text, nullable=False, unique=True),
        sa.Column("title_alt", sa.Text),
        sa.Column("mangadex_id", sa.Text, unique=True),
        sa.Column("anilist_id", sa.Integer, unique=True),
        sa.Column("mal_id", sa.Integer, unique=True),
        sa.Column("author", sa.Text),
        sa.Column("artist", sa.Text),
        sa.Column("synopsis", sa.Text),
        sa.Column("cover_url", sa.Text),
        sa.Column("cover_local", sa.Text),
        sa.Column("status", sa.Text, nullable=False, default="ongoing"),
        sa.Column("year", sa.Integer),
        sa.Column("publisher", sa.Text),
        sa.Column("monitored", sa.Boolean, nullable=False, default=True),
        sa.Column("monitor_status", sa.Text, nullable=False, default="all"),
        sa.Column("quality_profile_id", sa.Integer, sa.ForeignKey("quality_profile.id", ondelete="SET NULL")),
        sa.Column("language_profile_id", sa.Integer, sa.ForeignKey("language_profile.id", ondelete="SET NULL")),
        sa.Column("root_folder_path", sa.Text, nullable=False, default="/manga"),
        sa.Column("folder_name", sa.Text),
        sa.Column("chapter_count", sa.Integer, default=0),
        sa.Column("monitored_chapter_count", sa.Integer, default=0),
        sa.Column("downloaded_chapter_count", sa.Integer, default=0),
        sa.Column("added_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("last_searched_at", sa.DateTime),
    )
    op.create_index("ix_manga_title_slug", "manga", ["title_slug"])
    op.create_index("ix_manga_mangadex_id", "manga", ["mangadex_id"])

    op.create_table(
        "manga_genre",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("manga_id", sa.Integer, sa.ForeignKey("manga.id", ondelete="CASCADE"), nullable=False),
        sa.Column("genre", sa.Text, nullable=False),
    )

    op.create_table(
        "chapter",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("manga_id", sa.Integer, sa.ForeignKey("manga.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_number", sa.Float, nullable=False),
        sa.Column("volume_number", sa.Integer),
        sa.Column("title", sa.Text),
        sa.Column("mangadex_id", sa.Text),
        sa.Column("monitored", sa.Boolean, nullable=False, default=True),
        sa.Column("downloaded", sa.Boolean, nullable=False, default=False),
        sa.Column("ignored", sa.Boolean, nullable=False, default=False),
        sa.Column("release_date", sa.DateTime),
        sa.Column("download_date", sa.DateTime),
        sa.Column("language", sa.Text),
        sa.Column("scanlator_group", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_chapter_manga_id", "chapter", ["manga_id"])
    op.create_index("ix_chapter_mangadex_id", "chapter", ["mangadex_id"])

    op.create_table(
        "chapter_file",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chapter_id", sa.Integer, sa.ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.Text, nullable=False, unique=True),
        sa.Column("size", sa.Integer),
        sa.Column("format", sa.Text),
        sa.Column("language", sa.Text),
        sa.Column("scanlator_group", sa.Text),
        sa.Column("release_group", sa.Text),
        sa.Column("sha256", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "prowlarr_config",
        sa.Column("id", sa.Integer, primary_key=True, default=1),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("api_key_enc", sa.Text, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("last_sync", sa.DateTime),
    )

    op.create_table(
        "indexer",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("prowlarr_id", sa.Integer, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("protocol", sa.Text, nullable=False),
        sa.Column("type", sa.Text),
        sa.Column("url", sa.Text),
        sa.Column("api_key_enc", sa.Text),
        sa.Column("categories", sa.Text),
        sa.Column("priority", sa.Integer, nullable=False, default=25),
        sa.Column("enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("last_rss_id", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "download_client",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("host", sa.Text, nullable=False),
        sa.Column("port", sa.Integer, nullable=False),
        sa.Column("use_ssl", sa.Boolean, nullable=False, default=False),
        sa.Column("url_base", sa.Text),
        sa.Column("username", sa.Text),
        sa.Column("password_enc", sa.Text),
        sa.Column("api_key_enc", sa.Text),
        sa.Column("category", sa.Text, nullable=False, default="scanarr"),
        sa.Column("priority", sa.Integer, nullable=False, default=0),
        sa.Column("enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("is_default", sa.Boolean, nullable=False, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "download_queue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("manga_id", sa.Integer, sa.ForeignKey("manga.id", ondelete="SET NULL")),
        sa.Column("chapter_id", sa.Integer, sa.ForeignKey("chapter.id", ondelete="SET NULL")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("indexer_id", sa.Integer, sa.ForeignKey("indexer.id", ondelete="SET NULL")),
        sa.Column("download_url", sa.Text, nullable=False),
        sa.Column("magnet_uri", sa.Text),
        sa.Column("protocol", sa.Text, nullable=False),
        sa.Column("download_client_id", sa.Integer, sa.ForeignKey("download_client.id", ondelete="SET NULL")),
        sa.Column("external_id", sa.Text),
        sa.Column("quality", sa.Text),
        sa.Column("language", sa.Text),
        sa.Column("scanlator_group", sa.Text),
        sa.Column("size", sa.Integer),
        sa.Column("status", sa.Text, nullable=False, default="queued"),
        sa.Column("progress", sa.Float, nullable=False, default=0.0),
        sa.Column("error_message", sa.Text),
        sa.Column("added_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime),
        sa.Column("completed_at", sa.DateTime),
    )

    op.create_table(
        "history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("manga_id", sa.Integer, sa.ForeignKey("manga.id", ondelete="SET NULL")),
        sa.Column("chapter_id", sa.Integer, sa.ForeignKey("chapter.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("source_title", sa.Text),
        sa.Column("indexer", sa.Text),
        sa.Column("download_client", sa.Text),
        sa.Column("quality", sa.Text),
        sa.Column("language", sa.Text),
        sa.Column("size", sa.Integer),
        sa.Column("data", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "notification",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("settings_enc", sa.Text, nullable=False),
        sa.Column("on_grab", sa.Boolean, nullable=False, default=True),
        sa.Column("on_download", sa.Boolean, nullable=False, default=True),
        sa.Column("on_upgrade", sa.Boolean, nullable=False, default=False),
        sa.Column("on_rename", sa.Boolean, nullable=False, default=False),
        sa.Column("on_chapter_delete", sa.Boolean, nullable=False, default=False),
        sa.Column("on_health_issue", sa.Boolean, nullable=False, default=True),
        sa.Column("enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "root_folder",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("path", sa.Text, nullable=False, unique=True),
        sa.Column("free_space", sa.Integer),
        sa.Column("is_default", sa.Boolean, nullable=False, default=False),
    )

    op.create_table(
        "naming_config",
        sa.Column("id", sa.Integer, primary_key=True, default=1),
        sa.Column("rename_chapters", sa.Boolean, nullable=False, default=True),
        sa.Column("replace_illegal_chars", sa.Boolean, nullable=False, default=True),
        sa.Column("folder_format", sa.Text, nullable=False, default="{Manga Title}"),
        sa.Column("chapter_format", sa.Text, nullable=False,
                  default="{Manga Title} - Chapitre {Chapter:00} - {Chapter Title}"),
    )

    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer, primary_key=True, default=1),
        sa.Column("log_level", sa.Text, nullable=False, default="info"),
        sa.Column("update_interval", sa.Integer, nullable=False, default=60),
        sa.Column("api_key", sa.Text, nullable=False),
        sa.Column("auth_required", sa.Boolean, nullable=False, default=True),
    )


def downgrade() -> None:
    op.drop_table("app_config")
    op.drop_table("naming_config")
    op.drop_table("root_folder")
    op.drop_table("notification")
    op.drop_table("history")
    op.drop_table("download_queue")
    op.drop_table("download_client")
    op.drop_table("indexer")
    op.drop_table("prowlarr_config")
    op.drop_table("chapter_file")
    op.drop_table("chapter")
    op.drop_table("manga_genre")
    op.drop_table("manga")
    op.drop_table("language_profile")
    op.drop_table("quality_profile_item")
    op.drop_table("quality_profile")
