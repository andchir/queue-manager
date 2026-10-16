"""Logging helpers shared by worker processes and the worker manager."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TextIO


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = ROOT_DIR / "logs" / "workers"
LOG_FORMAT = (
    "%(asctime)s %(levelname)s worker=%(worker)s pid=%(process)d "
    "%(name)s: %(message)s"
)


class _WorkerContextFilter(logging.Filter):
    def __init__(self, worker_name: str):
        super().__init__()
        self.worker_name = worker_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.worker = self.worker_name
        return True


def configure_worker_logger(
    worker_name: str,
    log_dir: str | os.PathLike[str] | None = None,
    *,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure a rotating, per-worker logger and return it.

    The function is idempotent so worker modules can safely call it more than
    once. Logs are deliberately kept outside the source tree's root files.
    """
    safe_name = Path(worker_name).stem.replace(" ", "_")
    directory = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
    directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"queue_manager.worker.{safe_name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename) == directory / f"{safe_name}.log"
        for handler in logger.handlers
    ):
        handler = RotatingFileHandler(
            directory / f"{safe_name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler.addFilter(_WorkerContextFilter(safe_name))
        logger.addHandler(handler)

    return logger


class _LoggingStream:
    """File-like adapter that turns legacy print() calls into log records."""

    def __init__(self, logger: logging.Logger, level: int, original: TextIO):
        self.logger = logger
        self.level = level
        self.original = original
        self._buffer = ""

    def write(self, value: str) -> int:
        if not value:
            return 0
        self._buffer += value
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self.logger.log(self.level, line.rstrip())
        return len(value)

    def flush(self) -> None:
        if self._buffer.strip():
            self.logger.log(self.level, self._buffer.rstrip())
            self._buffer = ""
        self.original.flush()

    def isatty(self) -> bool:
        return False

    @property
    def encoding(self) -> str:
        return getattr(self.original, "encoding", "utf-8") or "utf-8"


def redirect_standard_streams(logger: logging.Logger) -> None:
    """Capture print()/stderr output without breaking explicit flush calls."""
    sys.stdout = _LoggingStream(logger, logging.INFO, sys.stdout)  # type: ignore[assignment]
    sys.stderr = _LoggingStream(logger, logging.ERROR, sys.stderr)  # type: ignore[assignment]
