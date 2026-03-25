"""Settings endpoints — Prowlarr, download clients, profiles, naming, notifications."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.core.security import decrypt_secret, encrypt_secret
from app.db import models
from app.schemas.settings import (
    DownloadClientIn,
    DownloadClientOut,
    IndexerOut,
    LanguageProfileOut,
    NamingConfigIn,
    NamingConfigOut,
    NotificationIn,
    NotificationOut,
    ProwlarrConfigIn,
    ProwlarrConfigOut,
    QualityProfileOut,
    RootFolderOut,
)

router = APIRouter()


# ── Prowlarr ──────────────────────────────────────────────────────────────────

@router.get("/prowlarr", response_model=ProwlarrConfigOut)
async def get_prowlarr(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.ProwlarrConfig).where(models.ProwlarrConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Prowlarr not configured")
    return cfg


@router.put("/prowlarr", response_model=ProwlarrConfigOut)
async def save_prowlarr(
    body: ProwlarrConfigIn,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.ProwlarrConfig).where(models.ProwlarrConfig.id == 1))
    cfg = result.scalar_one_or_none()

    enc_key = encrypt_secret(body.api_key)
    if cfg:
        cfg.url = body.url.rstrip("/")
        cfg.api_key_enc = enc_key
        cfg.enabled = body.enabled
    else:
        cfg = models.ProwlarrConfig(id=1, url=body.url.rstrip("/"), api_key_enc=enc_key, enabled=body.enabled)
        db.add(cfg)

    await db.commit()
    await db.refresh(cfg)
    return cfg


@router.post("/prowlarr/test", status_code=200)
async def test_prowlarr(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from app.services.prowlarr import test_connection
    result_q = await db.execute(select(models.ProwlarrConfig).where(models.ProwlarrConfig.id == 1))
    cfg = result_q.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=400, detail="Prowlarr not configured")
    ok = await test_connection(cfg.url, decrypt_secret(cfg.api_key_enc))
    if not ok:
        raise HTTPException(status_code=502, detail="Could not connect to Prowlarr")
    return {"message": "Connection successful"}


@router.post("/prowlarr/sync-indexers", status_code=202)
async def sync_indexers(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from app.services.prowlarr import sync_indexers_from_prowlarr
    result_q = await db.execute(select(models.ProwlarrConfig).where(models.ProwlarrConfig.id == 1))
    cfg = result_q.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=400, detail="Prowlarr not configured")
    await sync_indexers_from_prowlarr(db, cfg)
    return {"message": "Indexers synced"}


# ── Indexers ──────────────────────────────────────────────────────────────────

@router.get("/indexer", response_model=list[IndexerOut])
async def list_indexers(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Indexer).order_by(models.Indexer.priority, models.Indexer.name))
    return result.scalars().all()


# ── Download Clients ──────────────────────────────────────────────────────────

@router.get("/downloadclient", response_model=list[DownloadClientOut])
async def list_download_clients(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.DownloadClient).order_by(models.DownloadClient.name))
    return result.scalars().all()


@router.post("/downloadclient", response_model=DownloadClientOut, status_code=status.HTTP_201_CREATED)
async def add_download_client(
    body: DownloadClientIn,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    client = models.DownloadClient(
        name=body.name,
        type=body.type,
        host=body.host,
        port=body.port,
        use_ssl=body.use_ssl,
        url_base=body.url_base,
        username=body.username,
        password_enc=encrypt_secret(body.password) if body.password else None,
        api_key_enc=encrypt_secret(body.api_key) if body.api_key else None,
        category=body.category,
        priority=body.priority,
        enabled=body.enabled,
        is_default=body.is_default,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/downloadclient/{client_id}", response_model=DownloadClientOut)
async def update_download_client(
    client_id: int,
    body: DownloadClientIn,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    client = await db.get(models.DownloadClient, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.name = body.name
    client.type = body.type
    client.host = body.host
    client.port = body.port
    client.use_ssl = body.use_ssl
    client.url_base = body.url_base
    client.username = body.username
    if body.password:
        client.password_enc = encrypt_secret(body.password)
    if body.api_key:
        client.api_key_enc = encrypt_secret(body.api_key)
    client.category = body.category
    client.priority = body.priority
    client.enabled = body.enabled
    client.is_default = body.is_default

    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/downloadclient/{client_id}", status_code=204)
async def delete_download_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    client = await db.get(models.DownloadClient, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.delete(client)
    await db.commit()


@router.post("/downloadclient/{client_id}/test", status_code=200)
async def test_download_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from app.services.download import test_client
    client = await db.get(models.DownloadClient, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    ok = await test_client(client)
    if not ok:
        raise HTTPException(status_code=502, detail="Could not connect to download client")
    return {"message": "Connection successful"}


# ── Quality Profiles ──────────────────────────────────────────────────────────

@router.get("/qualityprofile", response_model=list[QualityProfileOut])
async def list_quality_profiles(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.QualityProfile).options(selectinload(models.QualityProfile.items))
    )
    return result.scalars().all()


# ── Language Profiles ─────────────────────────────────────────────────────────

@router.get("/languageprofile", response_model=list[LanguageProfileOut])
async def list_language_profiles(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.LanguageProfile))
    return [LanguageProfileOut.from_orm_with_parse(lp) for lp in result.scalars().all()]


# ── Naming Config ─────────────────────────────────────────────────────────────

@router.get("/naming", response_model=NamingConfigOut)
async def get_naming(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.NamingConfig).where(models.NamingConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Naming config not found")
    return cfg


@router.put("/naming", response_model=NamingConfigOut)
async def update_naming(
    body: NamingConfigIn,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.NamingConfig).where(models.NamingConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Naming config not found")
    for field, value in body.model_dump().items():
        setattr(cfg, field, value)
    await db.commit()
    await db.refresh(cfg)
    return cfg


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notification", response_model=list[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Notification).order_by(models.Notification.name))
    return result.scalars().all()


@router.post("/notification", response_model=NotificationOut, status_code=201)
async def add_notification(
    body: NotificationIn,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    notif = models.Notification(
        name=body.name,
        type=body.type,
        settings_enc=encrypt_secret(json.dumps(body.settings)),
        on_grab=body.on_grab,
        on_download=body.on_download,
        on_upgrade=body.on_upgrade,
        on_rename=body.on_rename,
        on_chapter_delete=body.on_chapter_delete,
        on_health_issue=body.on_health_issue,
        enabled=body.enabled,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


@router.delete("/notification/{notif_id}", status_code=204)
async def delete_notification(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    notif = await db.get(models.Notification, notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.delete(notif)
    await db.commit()


# ── Root Folders ──────────────────────────────────────────────────────────────

@router.get("/rootfolder", response_model=list[RootFolderOut])
async def list_root_folders(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(models.RootFolder))
    folders = result.scalars().all()
    # Update free space on each response
    import shutil
    for folder in folders:
        try:
            usage = shutil.disk_usage(folder.path)
            folder.free_space = usage.free
        except Exception:
            pass
    return folders
