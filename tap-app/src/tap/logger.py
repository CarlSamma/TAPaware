"""Structured logging setup using structlog.

Provides JSON output with correlation IDs, ISO timestamps, and log levels.
All modules use get_logger(name) for structured logging.

Logs are written to both stdout and a persistent log file when a file path
is configured. The file handler uses rotation to prevent unbounded growth.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog


def setup_logging(log_level: str = "INFO", log_file_path: str | None = None) -> None:
    """Configure structlog with JSON output, file logging, and correlation IDs.

    Call once at application startup before any logging occurs.

    Args:
        log_level: Minimum log level. One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_file_path: Optional path to a log file. If provided, logs are also
            written to this file with rotation (5 MB max, 3 backups).
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # ── Shared structlog processors ───────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # ── Stdlib logging handlers ───────────────────────────────────────
    # Console handler (stdout) — human-friendly colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    # Clear existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # File handler — structured JSON output
    if log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)

    # ── Configure structlog ───────────────────────────────────────────
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Console formatter — colored dev-friendly output
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=shared_processors,
    )
    console_handler.setFormatter(console_formatter)

    # File formatter — pure JSON for machine parsing
    if log_file_path:
        file_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
        file_handler.setFormatter(file_formatter)


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named structured logger.

    Args:
        name: Logger name, typically the module name (e.g., 'engine', 'db').

    Returns:
        A bound structlog logger instance.
    """
    return structlog.get_logger(name)

# --- Correlation ID helpers (v3.0) ---

import contextvars
import uuid

_cycle_id: contextvars.ContextVar[str] = contextvars.ContextVar("cycle_id", default="")
_probe_id: contextvars.ContextVar[str] = contextvars.ContextVar("probe_id", default="")


def set_cycle_id(cycle_id: str | None = None) -> str:
    """Set the cycle ID for log correlation."""
    cid = cycle_id or str(uuid.uuid4())[:8]
    _cycle_id.set(cid)
    structlog.contextvars.bind_contextvars(cycle_id=cid)
    return cid


def set_probe_id(probe_id: str | None = None) -> str:
    """Set the probe ID for log correlation."""
    pid = probe_id or str(uuid.uuid4())[:8]
    _probe_id.set(pid)
    structlog.contextvars.bind_contextvars(probe_id=pid)
    return pid


def get_cycle_id() -> str:
    """Return the current cycle ID from context."""
    return _cycle_id.get()


def get_probe_id() -> str:
    """Return the current probe ID from context."""
    return _probe_id.get()


def clear_correlation_ids() -> None:
    """Clear all correlation IDs from context."""
    _cycle_id.set("")
    _probe_id.set("")
    structlog.contextvars.clear_contextvars()
