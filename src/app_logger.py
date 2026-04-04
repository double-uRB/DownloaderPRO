"""
Centralized logging for Downloader PRO.
Logs to both file (logs/app.log) and a rotating buffer for in-app display.
"""

import logging
import os
import re
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


class SanitizingFilter(logging.Filter):
    """
    Scrub sensitive patterns (PO tokens, OAuth, Cookies) from logs before writing to disk/console.
    """
    PATTERNS = [
        (re.compile(r'(po_token=)[^\s&\"\'\)]+'), r'\1[REDACTED]'),
        (re.compile(r'(Authorization: )\S+'), r'\1[REDACTED]'),
        (re.compile(r'(Cookie: )[^\s;]+'), r'\1[REDACTED]'),
        (re.compile(r'(--add-header\s+Cookie:)[^\s]+', re.IGNORECASE), r'\1 [REDACTED]'),
    ]

    def filter(self, record):
        if not isinstance(record.msg, str):
            record.msg = str(record.msg)
            
        for pat, repl in self.PATTERNS:
            record.msg = pat.sub(repl, record.msg)
        return True


# ── Log directory setup ─────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"


# ── Logger factory ──────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Get a named logger that writes to the shared log file with sanitization."""
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    
    # Shared filter for all handlers
    sanitizer = SanitizingFilter()

    # ── File handler (rotating) ──────────────────────────────────────────
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024, # 5MB
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(sanitizer)
    logger.addHandler(file_handler)

    # ── Console handler ─────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(sanitizer)
    logger.addHandler(console_handler)

    return logger
