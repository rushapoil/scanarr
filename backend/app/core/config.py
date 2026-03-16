from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "Scanarr"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    PORT: int = 8080

    # ── Paths ────────────────────────────────────────────────
    CONFIG_DIR: Path = Path("/config")
    DATA_DIR: Path = Path("/manga")

    @property
    def DB_PATH(self) -> Path:
        return self.CONFIG_DIR / "scanarr.db"

    @property
    def DB_URL(self) -> str:
        return f"sqlite+aiosqlite:///{self.DB_PATH}"

    @property
    def SECRET_KEY_FILE(self) -> Path:
        return self.CONFIG_DIR / "secret.key"

    @property
    def COVERS_DIR(self) -> Path:
        return self.CONFIG_DIR / "covers"

    @property
    def LOGS_DIR(self) -> Path:
        return self.CONFIG_DIR / "logs"

    # ── Auth ─────────────────────────────────────────────────
    AUTH_REQUIRED: bool = True
    AUTH_USERNAME: str = "admin"
    # Bcrypt hash — empty means not yet configured
    AUTH_PASSWORD_HASH: str = ""

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ── Scheduler ────────────────────────────────────────────
    RSS_POLL_INTERVAL: int = 60       # minutes
    QUEUE_SYNC_INTERVAL: int = 30     # seconds
    METADATA_REFRESH_INTERVAL: int = 24  # hours


@lru_cache()
def get_settings() -> Settings:
    return Settings()
