"""
Security utilities:
  - Fernet symmetric encryption for stored secrets (download client passwords, API keys)
  - Bcrypt password hashing for user auth
  - API key generation / verification
  - FastAPI HTTP Basic Auth dependency
"""
from __future__ import annotations

import secrets
import logging
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, APIKeyHeader
from passlib.context import CryptContext

from app.core.config import get_settings, Settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_basic = HTTPBasic(auto_error=False)
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


# ── Fernet key management ─────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_fernet(key_file: str) -> Fernet:
    """Load or generate the Fernet key. Result is cached for the process lifetime."""
    path = Path(key_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        key = path.read_bytes().strip()
    else:
        key = Fernet.generate_key()
        path.write_bytes(key)
        path.chmod(0o600)
        logger.info("Generated new encryption key at %s", path)

    return Fernet(key)


def _fernet(settings: Settings | None = None) -> Fernet:
    s = settings or get_settings()
    return _load_fernet(str(s.SECRET_KEY_FILE))


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a string with Fernet. Returns a URL-safe base64 token."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a Fernet token. Raises ValueError on tampered/invalid data."""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt secret — key mismatch or data corrupted") from exc


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── API key ───────────────────────────────────────────────────────────────────

def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


# ── FastAPI auth dependencies ─────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPBasicCredentials | None = Depends(http_basic),
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Accepts either:
      - HTTP Basic Auth  (username / password)
      - X-Api-Key header (raw token stored in app_config)
    If auth is disabled, passes through with username "anonymous".
    """
    if not settings.AUTH_REQUIRED:
        return "anonymous"

    # ── API key path ──────────────────────────────────────────
    if api_key:
        from app.db.database import AsyncSessionLocal
        from app.db import models
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(models.AppConfig).where(models.AppConfig.id == 1))
            cfg = result.scalar_one_or_none()
            if cfg and cfg.api_key and secrets.compare_digest(cfg.api_key, api_key):
                return "api"

    # ── Basic auth path ───────────────────────────────────────
    if credentials:
        username_ok = secrets.compare_digest(
            credentials.username.encode(), settings.AUTH_USERNAME.encode()
        )
        password_ok = (
            bool(settings.AUTH_PASSWORD_HASH)
            and verify_password(credentials.password, settings.AUTH_PASSWORD_HASH)
        )
        if username_ok and password_ok:
            return credentials.username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": 'Basic realm="Scanarr"'},
    )
