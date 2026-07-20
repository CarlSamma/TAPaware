"""
Entrypoint: TAP Engine
Avvia il loop principale di TAPEngine collegando tutte le dipendenze.
Richiede variabili in .env: OPENROUTER_API_KEY, DATABASE_URL, NEO4J_URI, etc.
"""
from __future__ import annotations
import asyncio
import signal
import sys

from tap.config import get_settings
from tap.logger import get_logger

log = get_logger("entrypoint.engine")


async def main() -> None:
    settings = get_settings()
    log.info("tap_engine_entrypoint_starting", env=settings.environment if hasattr(settings, 'environment') else 'docker')

    # --- Import lazy per evitare import circolari al boot ---
    from tap.db import Database
    from tap.ssot import SSOTEngine
    from tap.dpa import DPAFrameManager
    from tap.classifier import ResponseClassifier
    from tap.judge import Judge
    from tap.grok_monitor import GrokMonitor
    from tap.x_client import TwitterClient
    from tap.followup import FollowUpGenerator
    from tap.persistence.event_store import EventStore
    from tap.engine import TAPEngine
    from tap.llm_client import LLMClient

    db = Database(settings.db_path)
    await db.initialize()
    log.info("db_initialized")

    twitter = TwitterClient(settings)
    ssot = SSOTEngine(db=db, settings=settings)
    dpa = DPAFrameManager(db=db, settings=settings)
    classifier = ResponseClassifier(settings=settings)
    judge = Judge(settings=settings)
    grok = GrokMonitor(settings=settings)
    event_store = EventStore(db=db)
    llm_client = LLMClient(settings=settings)
    followup = FollowUpGenerator(
        ssot=ssot, dpa=dpa,
        openrouter_api_key=settings.openrouter_api_key,
        model=settings.openrouter_model_primary,
    )

    engine = TAPEngine(
        db=db, twitter=twitter, ssot=ssot, dpa=dpa,
        classifier=classifier, judge=judge, grok=grok,
        settings=settings, event_store=event_store,
        followup=followup, llm_client=llm_client,
    )

    log.info("tap_engine_ready_waiting_for_api_trigger")

    # Il TAPEngine e' HITL-driven: i cicli vengono avviati dall'API via WebSocket.
    # Qui manteniamo il processo vivo e in ascolto di segnali di shutdown.
    stop_event = asyncio.Event()

    def _shutdown(sig_name: str) -> None:
        log.info("shutdown_signal_received", signal=sig_name)
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig.name: _shutdown(s))

    log.info("tap_engine_idle_loop_started")
    await stop_event.wait()
    log.info("tap_engine_shutdown_complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
