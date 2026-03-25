import platform
import sys
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.scheduler import scheduler
from app.schemas.system import DiskSpace, HealthCheck, SchedulerJob, SystemStatus

router = APIRouter()
_start_time = datetime.utcnow()


@router.get("/health", response_model=HealthCheck, include_in_schema=False)
async def health():
    return {"status": "ok"}


@router.get("/status", response_model=SystemStatus)
async def system_status(
    _user: str = Depends(get_current_user),
):
    settings = get_settings()
    return SystemStatus(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        build_time=None,
        is_debug=settings.DEBUG,
        db_path=str(settings.DB_PATH),
        config_dir=str(settings.CONFIG_DIR),
        data_dir=str(settings.DATA_DIR),
        os_name=platform.system(),
        os_version=platform.release(),
        runtime_version=f"Python {sys.version.split()[0]}",
        startup_time=_start_time.isoformat(),
    )


@router.get("/diskspace", response_model=list[DiskSpace])
async def disk_space(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    import shutil

    from sqlalchemy import select

    from app.db import models

    result = await db.execute(select(models.RootFolder))
    folders = result.scalars().all()

    spaces = []
    seen = set()
    for folder in folders:
        if folder.path in seen:
            continue
        seen.add(folder.path)
        try:
            usage = shutil.disk_usage(folder.path)
            spaces.append(DiskSpace(
                path=folder.path,
                free_space=usage.free,
                total_space=usage.total,
                used_space=usage.used,
            ))
        except Exception:
            pass
    return spaces


@router.get("/task", response_model=list[SchedulerJob])
async def list_tasks(
    _user: str = Depends(get_current_user),
):
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(SchedulerJob(
            id=job.id,
            name=job.name,
            next_run_time=job.next_run_time.isoformat() if job.next_run_time else None,
            trigger=str(job.trigger),
        ))
    return jobs


@router.post("/task/{job_id}/run", status_code=202)
async def run_task_now(
    job_id: str,
    _user: str = Depends(get_current_user),
):
    job = scheduler.get_job(job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    job.modify(next_run_time=datetime.utcnow())
    return {"message": f"Job '{job_id}' queued for immediate execution"}


@router.get("/apikey")
async def get_api_key(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from sqlalchemy import select

    from app.db import models
    result = await db.execute(select(models.AppConfig).where(models.AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    return {"api_key": cfg.api_key if cfg else None}
