from fastapi import APIRouter

from app.api.v1 import mangas, chapters, queue, history, settings, system, calendar

api_router = APIRouter()

api_router.include_router(mangas.router,   prefix="/manga",    tags=["Manga"])
api_router.include_router(chapters.router, prefix="/chapter",  tags=["Chapters"])
api_router.include_router(queue.router,    prefix="/queue",    tags=["Queue"])
api_router.include_router(history.router,  prefix="/history",  tags=["History"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(system.router,   prefix="/system",   tags=["System"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
