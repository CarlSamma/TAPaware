"""CHRONOS Temporal worker — stub for future implementation.

Provides `run_worker(settings)` which is imported by entrypoints/run_chronos.py.
Currently logs a warning and idles until shutdown.
"""
from __future__ import annotations

import asyncio
import signal

from tap.config import Settings
from tap.logger import get_logger

log = get_logger("chronos.worker")


async def run_worker(settings: Settings) -> None:
    """Start the Temporal workflow worker.

    This is a stub. Implement when Temporal worker SDK is integrated.
    """
    log.warning(
        "chronos_worker_not_implemented_yet",
        hint="Implement Temporal worker registration here",
        identity=settings.chronos_worker_identity,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: stop_event.set())

    log.info("chronos_worker_idling", identity=settings.chronos_worker_identity)
    await stop_event.wait()
    log.info("chronos_worker_shutdown_complete")
