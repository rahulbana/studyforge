"""Central logging configuration.

Supports two formats (``LOG_FORMAT``):
  * ``text`` — human-readable, one line per record (default, best for dev).
  * ``json`` — one JSON object per line (best for log shippers / production).

Every record carries the current correlation id (``request_id``) so a single
operation can be traced across requests and background threads.
"""
from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler

from .config import get_settings
from .context import get_request_id

_configured = False

# Attributes present on a stdlib LogRecord that are not "extra" fields.
_RESERVED = set(vars(logging.makeLogRecord({})))


class _RequestIdFilter(logging.Filter):
    """Attach the current correlation id to every record as ``request_id``."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        return True


class _JsonFormatter(logging.Formatter):
    """Render a record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Include any structured extras passed via logger.*(..., extra={...}).
        for key, value in record.__dict__.items():
            if key not in _RESERVED and key not in payload:
                payload[key] = value
        return json.dumps(payload, default=str)


def _make_formatter(as_json: bool) -> logging.Formatter:
    if as_json:
        return _JsonFormatter()
    return logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s"
    )


def configure_logging() -> None:
    """Configure root logging once, using the level/format from settings.

    Always logs to the console; also logs to a rotating file when ``LOG_FILE``
    is set (default ``logs/app.log``, relative to the backend working dir), so
    generation tracebacks are captured somewhere inspectable.
    """
    global _configured
    if not _configured:
        settings = get_settings()
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        as_json = settings.log_format.lower() == "json"
        id_filter = _RequestIdFilter()

        handlers: list[logging.Handler] = []

        console = logging.StreamHandler()
        handlers.append(console)

        log_file = (settings.log_file or "").strip()
        if log_file:
            try:
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
                )
                handlers.append(file_handler)
            except OSError as exc:  # read-only fs — keep console logging working
                import sys

                print(f"WARNING: file logging disabled ({log_file}): {exc}", file=sys.stderr)

        for handler in handlers:
            handler.addFilter(id_filter)
            handler.setFormatter(_make_formatter(as_json))

        root = logging.getLogger()
        root.handlers.clear()
        for handler in handlers:
            root.addHandler(handler)
        root.setLevel(level)
        _configured = True

    # Run every call (not just the first): uvicorn reconfigures its own loggers
    # at server startup, after the import-time configure_logging(). Re-routing
    # them here (also called from the app lifespan) makes it stick so HTTP access
    # lines and uvicorn error tracebacks reach our console + file handlers.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv = logging.getLogger(name)
        uv.handlers.clear()
        uv.propagate = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
