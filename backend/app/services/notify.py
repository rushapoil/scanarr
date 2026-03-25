"""
Notification dispatch service.
Sends notifications to Discord, Telegram, webhooks, etc.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.security import decrypt_secret

logger = logging.getLogger(__name__)


async def dispatch(event: str, **context: Any) -> None:
    """
    Dispatch notifications for the given event to all enabled notifiers.

    event: "on_grab" | "on_download" | "on_upgrade" | "on_rename" |
           "on_chapter_delete" | "on_health_issue"
    """
    from sqlalchemy import select

    from app.db import models
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(models.Notification).where(models.Notification.enabled == True)  # noqa: E712
        )
        notifiers = result.scalars().all()

    for notifier in notifiers:
        if not getattr(notifier, event, False):
            continue
        try:
            settings = json.loads(decrypt_secret(notifier.settings_enc))
            await _send(notifier.type, settings, event, context)
        except Exception:
            logger.exception("Notification failed for %s (%s)", notifier.name, notifier.type)


async def _send(notif_type: str, settings: dict, event: str, context: dict) -> None:
    message = _build_message(event, context)

    if notif_type == "discord":
        await _send_discord(settings.get("webhook_url", ""), message)
    elif notif_type == "telegram":
        await _send_telegram(settings.get("bot_token", ""), settings.get("chat_id", ""), message)
    elif notif_type == "webhook":
        await _send_webhook(settings.get("url", ""), settings.get("method", "POST"), message, context)
    else:
        logger.warning("Unknown notification type: %s", notif_type)


def _build_message(event: str, context: dict) -> str:
    manga = context.get("manga")
    chapter = context.get("chapter")

    manga_title = manga.title if manga else "Unknown"
    chapter_num = chapter.chapter_number if chapter else "?"

    messages = {
        "on_grab": f"📥 Grabbed: **{manga_title}** — Chapter {chapter_num}",
        "on_download": f"✅ Downloaded: **{manga_title}** — Chapter {chapter_num}",
        "on_upgrade": f"⬆️ Upgraded: **{manga_title}** — Chapter {chapter_num}",
        "on_rename": f"✏️ Renamed: **{manga_title}** — Chapter {chapter_num}",
        "on_chapter_delete": f"🗑️ Deleted: **{manga_title}** — Chapter {chapter_num}",
        "on_health_issue": f"⚠️ Health issue: {context.get('message', 'Unknown issue')}",
    }
    return messages.get(event, f"Scanarr event: {event}")


async def _send_discord(webhook_url: str, message: str) -> None:
    if not webhook_url:
        return
    async with httpx.AsyncClient() as c:
        resp = await c.post(webhook_url, json={"content": message})
        resp.raise_for_status()


async def _send_telegram(bot_token: str, chat_id: str, message: str) -> None:
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient() as c:
        resp = await c.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
        resp.raise_for_status()


async def _send_webhook(url: str, method: str, message: str, context: dict) -> None:
    if not url:
        return
    payload = {
        "event": context.get("event"),
        "message": message,
        "manga": context.get("manga") and {
            "id": context["manga"].id,
            "title": context["manga"].title,
        },
        "chapter": context.get("chapter") and {
            "id": context["chapter"].id,
            "number": context["chapter"].chapter_number,
        },
    }
    async with httpx.AsyncClient() as c:
        if method.upper() == "POST":
            resp = await c.post(url, json=payload)
        else:
            resp = await c.get(url, params={"message": message})
        resp.raise_for_status()
