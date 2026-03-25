"""First-run initialisation: create tables (via Alembic) and seed defaults."""
import logging

from sqlalchemy import select

from app.core.security import generate_api_key
from app.db import models
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Called at application startup.
    - Ensures the config directory exists
    - Seeds AppConfig / NamingConfig singletons if they don't exist yet
    - Seeds default QualityProfile and LanguageProfile
    """
    from app.core.config import get_settings
    settings = get_settings()
    settings.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    settings.COVERS_DIR.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        # ── AppConfig singleton ──────────────────────────────────────────────
        result = await db.execute(select(models.AppConfig).where(models.AppConfig.id == 1))
        app_cfg = result.scalar_one_or_none()
        if app_cfg is None:
            api_key = generate_api_key()
            app_cfg = models.AppConfig(
                id=1,
                api_key=api_key,
                auth_required=settings.AUTH_REQUIRED,
            )
            db.add(app_cfg)
            logger.info("AppConfig created — API key: %s", api_key)

        # ── NamingConfig singleton ───────────────────────────────────────────
        result = await db.execute(select(models.NamingConfig).where(models.NamingConfig.id == 1))
        if result.scalar_one_or_none() is None:
            db.add(models.NamingConfig(id=1))
            logger.info("NamingConfig created with defaults")

        # ── Default quality profiles ─────────────────────────────────────────
        result = await db.execute(select(models.QualityProfile))
        if not result.scalars().all():
            standard = models.QualityProfile(name="Standard", is_default=True)
            db.add(standard)
            await db.flush()
            for priority, (quality, allowed) in enumerate(
                [("best", True), ("web", True), ("raw", False)]
            ):
                db.add(models.QualityProfileItem(
                    quality_profile_id=standard.id,
                    quality=quality,
                    allowed=allowed,
                    priority=priority,
                ))
            logger.info("Default quality profile created")

        # ── Default language profiles ────────────────────────────────────────
        result = await db.execute(select(models.LanguageProfile))
        if not result.scalars().all():
            import json
            db.add(models.LanguageProfile(name="Français (VF/VOSTFR)", languages=json.dumps(["fr", "en"])))
            db.add(models.LanguageProfile(name="Anglais uniquement", languages=json.dumps(["en"])))
            db.add(models.LanguageProfile(name="RAW", languages=json.dumps(["raw", "ja"])))
            logger.info("Default language profiles created")

        # ── Default root folder ──────────────────────────────────────────────
        result = await db.execute(select(models.RootFolder))
        if not result.scalars().all():
            db.add(models.RootFolder(path=str(settings.DATA_DIR), is_default=True))
            logger.info("Default root folder: %s", settings.DATA_DIR)

        await db.commit()
        logger.info("Database initialisation complete")
