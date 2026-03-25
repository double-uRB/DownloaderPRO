"""
Centralized logging for Downloader PRO.
Logs to both file (logs/app.log) and a rotating buffer for in-app display.
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


# ── Log directory setup ─────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"


# ── Logger factory ──────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Get a named logger that writes to the shared log file.

    Usage:
        from app_logger import get_logger
        log = get_logger(__name__)
        log.info("Download started")
        log.error("Something failed", exc_info=True)
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── File handler (rotating, 5 MB max, keep 3 backups) ───────────────
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # ── Console handler (INFO+, safe encoding) ──────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    return logger
