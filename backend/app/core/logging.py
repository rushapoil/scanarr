"""Structured logging configuration using stdlib logging with rich formatting."""
import logging
import logging.config
import sys
from pathlib import Path

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    log_level = settings.LOG_LEVEL.upper()

    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOGS_DIR / "scanarr.log"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": (
                    '{"time":"%(asctime)s","level":"%(levelname)s",'
                    '"logger":"%(name)s","message":"%(message)s"}'
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "console": {
                "format": "%(asctime)s  %(levelname)-8s  %(name)-30s  %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "console",
                "level": log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_file),
                "maxBytes": 10 * 1024 * 1024,   # 10 MB
                "backupCount": 5,
                "formatter": "json",
                "level": log_level,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": log_level,
        },
        "loggers": {
            # Silence noisy third-party loggers
            "uvicorn.access": {"level": "WARNING"},
            "apscheduler": {"level": "INFO"},
            "httpx": {"level": "WARNING"},
            "sqlalchemy.engine": {"level": "WARNING"},
        },
    }

    logging.config.dictConfig(config)
    logging.getLogger(__name__).info(
        "Logging initialised — level=%s file=%s", log_level, log_file
    )
