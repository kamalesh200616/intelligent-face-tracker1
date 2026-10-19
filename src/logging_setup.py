"""Structured logging setup for Intelligent Face Tracker.

Configures both console logging and persistent audit logging to `logs/events.log`,
capturing all required system events (detection, recognition, registration,
tracking, entry, exit, errors, recovery).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import LoggingConfig


def setup_logging(
    config: Optional[LoggingConfig] = None,
    log_file_path: str = "logs/events.log",
    log_level: Optional[str] = None,
) -> logging.Logger:
    """Initialize structured logging across the application.

    Args:
        config: LoggingConfig instance or None for default.
        log_file_path: Path to write the mandatory events.log file.
        log_level: Override logging level if provided.

    Returns:
        The configured root or package logger.
    """
    level_str = log_level or (config.level if config else "INFO")
    numeric_level = getattr(logging, level_str.upper(), logging.INFO)

    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger("facetracker")
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    # 1. Mandatory Persistent File Handler (events.log)
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 2. Console Handler (if enabled)
    console_enabled = config.console_output if config else True
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    root_logger.propagate = False
    root_logger.info("Structured logger initialized. Audit events logging to: %s", log_path.resolve())
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Retrieve a namespaced child logger under 'facetracker'."""
    return logging.getLogger(f"facetracker.{name}")
