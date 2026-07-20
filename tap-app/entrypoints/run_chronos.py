"""
Entrypoint: Chronos Worker
Avvia il Temporal workflow worker.
Se src/chronos/worker.py non esiste ancora, rimane in attesa (no crash).
"""
from __future__ import annotations
import asyncio
import signal
import sys

from tap.config import get_settings
from tap.logger import get_logger

log = get_logger("entrypoint.chronos")


async def main() -> None:
    settings = get_settings()
    log.info("chronos_worker_entrypoint_starting")

    try:
        from chronos.worker import run_worker
        log.info("chronos_worker_module_found")
        await run_worker(settings)
    except ModuleNotFoundError:
        log.warning("chronos_worker_not_implemented_yet_idling",
                    hint="Crea src/chronos/worker.py con async def run_worker(settings)")
        # Idle loop — non crasha, aspetta shutdown
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: stop_event.set())
        await stop_event.wait()

    log.info("chronos_worker_shutdown_complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
