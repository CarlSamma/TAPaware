"""
Entrypoint: Stream Listener (Adapters)
Avvia il listener X/Twitter che raccoglie reply a @HackingA0.
"""
from __future__ import annotations
import asyncio
import signal
import sys

from tap.config import get_settings
from tap.logger import get_logger

log = get_logger("entrypoint.stream")


async def main() -> None:
    settings = get_settings()
    log.info("stream_listener_entrypoint_starting")

    from tap.stream_listener import StreamListener

    log.info("stream_listener_config_loaded")

    listener = StreamListener(settings=settings)

    stop_event = asyncio.Event()

    def _shutdown(sig_name: str) -> None:
        log.info("shutdown_signal_received", signal=sig_name)
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig.name: _shutdown(s))

    log.info("stream_listener_starting")
    listen_task = asyncio.create_task(listener.start())

    await stop_event.wait()
    listen_task.cancel()
    try:
        await listen_task
    except asyncio.CancelledError:
        pass
    log.info("stream_listener_shutdown_complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
