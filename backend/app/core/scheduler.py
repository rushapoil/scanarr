"""APScheduler setup — all periodic background jobs are registered here."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    """Register all jobs and start the scheduler."""

    # ── RSS monitor: poll indexers for new chapter releases ──────────────────
    scheduler.add_job(
        _rss_monitor_job,
        trigger=IntervalTrigger(minutes=settings.RSS_POLL_INTERVAL),
        id="rss_monitor",
        name="RSS Monitor",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
    )

    # ── Queue sync: update download progress from clients ────────────────────
    scheduler.add_job(
        _queue_sync_job,
        trigger=IntervalTrigger(seconds=settings.QUEUE_SYNC_INTERVAL),
        id="queue_sync",
        name="Queue Sync",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=10,
    )

    # ── Metadata refresh: update manga info from MangaDex ───────────────────
    scheduler.add_job(
        _metadata_refresh_job,
        trigger=IntervalTrigger(hours=settings.METADATA_REFRESH_INTERVAL),
        id="metadata_refresh",
        name="Metadata Refresh",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


# ── Job implementations ───────────────────────────────────────────────────────

async def _rss_monitor_job() -> None:
    try:
        from app.services.monitor import run_rss_monitor
        await run_rss_monitor()
    except Exception:
        logger.exception("RSS monitor job failed")


async def _queue_sync_job() -> None:
    try:
        from app.services.download import sync_queue
        await sync_queue()
    except Exception:
        logger.exception("Queue sync job failed")


async def _metadata_refresh_job() -> None:
    try:
        from app.services.metadata import refresh_all_manga_metadata
        await refresh_all_manga_metadata()
    except Exception:
        logger.exception("Metadata refresh job failed")
