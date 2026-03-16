from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.init_db import init_db

settings = get_settings()

# Frontend dist is at this path inside the Docker image
# (copied by the root multi-stage Dockerfile)
_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Scanarr",
    description="Manga/Scantrad automation — *-arr style",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── Serve frontend SPA in production ─────────────────────────────────────────
# Only registered if the compiled frontend is present (not in dev mode).
if _FRONTEND_DIST.exists():
    _assets = _FRONTEND_DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        index = _FRONTEND_DIST / "index.html"
        if not index.exists():
            raise HTTPException(status_code=503, detail="Frontend not built")
        return FileResponse(str(index))
