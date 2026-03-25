from __future__ import annotations

from pydantic import BaseModel


class SystemStatus(BaseModel):
    app_name: str
    version: str
    build_time: str | None
    is_debug: bool
    db_path: str
    config_dir: str
    data_dir: str
    os_name: str
    os_version: str
    runtime_version: str
    startup_time: str


class HealthCheck(BaseModel):
    status: str = "ok"


class DiskSpace(BaseModel):
    path: str
    free_space: int
    total_space: int
    used_space: int


class SchedulerJob(BaseModel):
    id: str
    name: str
    next_run_time: str | None
    trigger: str
