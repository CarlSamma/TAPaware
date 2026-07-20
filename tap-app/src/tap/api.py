"""Module 11: FastAPI Server.

REST API + WebSocket for the Web UI Dashboard.
Provides endpoints for live feed, attack tree, properties, DPA status,
follow-up selection, SSOT export, entropy, and real-time updates.

Endpoints:
- GET /api/feed — Live tweet feed
- GET /api/tree — Current TAP tree state
- GET /api/properties — Confirmed properties
- GET /api/dpa — Active DPA frame and aliases
- POST /api/select — User selects Option A or B
- POST /api/post — Trigger posting of selected option
- GET /api/ssot — Full SSOT JSON
- GET /api/stats — Summary statistics
- GET /api/entropy — Current entropy state
- WebSocket /ws/live — Real-time updates
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import tweepy

from tap.config import get_settings, save_env_vars
from tap.db import Database
from tap.dpa import DPAFrameManager
from tap.engine import TAPEngine
from tap.persistence.event_store import EventStore
from tap.followup import FollowUpGenerator
from tap.grok_monitor import GrokMonitor
from tap.stream_listener import StreamListener
from tap.judge import Judge
from tap.logger import get_logger, setup_logging, get_cycle_id, get_probe_id
from tap.llm_client import LLMClient
from tap.prompt_sanitiser import PromptSanitiser
from tap.strategies import AestheticEvalProvider, BinarySearchProvider, MetaphorShiftProvider, Phase5ExtractionProvider, StrategySelector
from tap.ssot import SSOTEngine
from tap.x_client import TwitterClient
from tap.classifier import ResponseClassifier
from tap.agents import AgentDPAFManager, AgentSTIREvaluator, AgentIntelExtractor

if TYPE_CHECKING:
    from hydra.v_genome import VGenomeClient

log = get_logger("api")

# Module-level instances (initialized at startup)
_db: Optional[Database] = None
_engine: Optional[TAPEngine] = None
_ssot: Optional[SSOTEngine] = None
_dpa: Optional[AgentDPAFManager] = None
_llm_client: Optional[LLMClient] = None
_sanitiser: Optional[PromptSanitiser] = None
_strategy_selector: Optional[StrategySelector] = None
_v_genome: Optional['VGenomeClient'] = None  # VGenome client for technique queries

# Last follow-up generated (for HITL selection)
_last_followup = None
_selected_probe: Optional[str] = None
_is_running = False

# Connected WebSocket clients
_ws_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and teardown modules."""
    global _db, _engine, _ssot, _dpa, _llm_client, _sanitiser, _strategy_selector

    # Load .env into OS environment
    # OAUTHLIB_INSECURE_TRANSPORT=1 must be in .env for local HTTP OAuth2
    from dotenv import load_dotenv
    load_dotenv()

    settings = get_settings()
    setup_logging(log_file_path=settings.log_file_path if settings.log_file_path else None)

    # Initialize database
    _db = Database(settings.db_path)
    await _db.initialize()

    # v3.0: Initialize unified LLM client
    _llm_client = LLMClient(settings)
    log.info("llm_client_ready")

    # v3.0: Initialize prompt sanitiser
    _sanitiser = PromptSanitiser(strict_mode=settings.use_prompt_sanitiser)
    log.info("prompt_sanitiser_ready")

    # v3.0: Initialize strategy providers and selector
    binary_search = BinarySearchProvider(_llm_client, _sanitiser)
    metaphor_shift = MetaphorShiftProvider(_llm_client, _sanitiser)
    aesthetic_eval = AestheticEvalProvider(_llm_client, _sanitiser)
    phase5 = Phase5ExtractionProvider(_llm_client, _sanitiser)
    _strategy_selector = StrategySelector(binary_search, metaphor_shift, aesthetic_eval, phase5)
    log.info("strategy_selector_ready")

    # Initialize V-Genome client for technique queries
    try:
        from hydra.v_genome import VGenomeClient
        _v_genome = VGenomeClient(settings)
        await _v_genome.connect()
        log.info("v_genome_client_ready")
    except Exception as e:
        log.warning("v_genome_client_failed", error=str(e))
        _v_genome = None

    # Feature 1: Initialize γ-Tracker for parallel compliance scoring
    _gamma_tracker = None
    try:
        from chronos.gamma_tracker import GammaTracker
        _gamma_tracker = GammaTracker(llm_client=_llm_client)
        log.info("gamma_tracker_ready")
    except Exception as e:
        log.warning("gamma_tracker_init_failed", error=str(e))

    # Feature 2: Initialize Graph-Guided Technique Selector
    _technique_selector = None
    try:
        from tap.strategies.technique_selector import GraphTechniqueSelector
        _technique_selector = GraphTechniqueSelector(
            v_genome=_v_genome,
            asr_weight=0.4,
            stealth_weight=0.3,
            complement_weight=0.2,
            provenance_weight=0.1,
        )
        log.info("graph_technique_selector_ready")
    except Exception as e:
        log.warning("graph_technique_selector_init_failed", error=str(e))

    # Initialize modules
    twitter = TwitterClient(settings)
    _ssot = SSOTEngine(_db, settings.ssot_path, target_handle=settings.target_handle)
    _dpa = AgentDPAFManager(_db)
    stir_evaluator = AgentSTIREvaluator(llm_client=_llm_client)
    intel_extractor = AgentIntelExtractor(_ssot, twitter)
    classifier = ResponseClassifier(
        settings.openrouter_api_key, settings.openrouter_model_primary, llm_client=_llm_client
    )
    judge = Judge(
        settings.openrouter_api_key, settings.openrouter_model_primary, llm_client=_llm_client
    )

    # Initialize stream listener and monitor for real-time reply detection
    stream = StreamListener(settings)
    grok = GrokMonitor(settings, twitter, stream=stream)
    followup_gen = FollowUpGenerator(
        _ssot, _dpa,
        settings.openrouter_api_key, settings.openrouter_model_primary,
        llm_client=_llm_client,
    )

    async def on_engine_event(event_type: str, data: dict):
        await broadcast_update(event_type, data)

    _event_store = EventStore(_db)

    # Initialize Aware memory bridge
    _aware = None
    try:
        from tap.aware_bridge import AwareBridge
        _aware = AwareBridge(db_path=settings.db_path.replace("tap.db", "aware.db"))
        await _aware.initialize()
        log.info("aware_bridge_ready")
    except Exception as e:
        log.warning("aware_bridge_init_failed", error=str(e))
        _aware = None

    _engine = TAPEngine(
        db=_db,
        twitter=twitter,
        ssot=_ssot,
        dpa=_dpa,
        classifier=classifier,
        judge=judge,
        grok=grok,
        settings=settings,
        event_store=_event_store,
        followup=followup_gen,
        event_callback=on_engine_event,
        stir_evaluator=stir_evaluator,
        intel_extractor=intel_extractor,
        llm_client=_llm_client,
        gamma_tracker=_gamma_tracker,
        technique_selector=_technique_selector,
        v_genome=_v_genome,
        aware=_aware,
    )

    # Target resolution (we just need to ensure the client is ready)
    target_user = None
    try:
        target_user = await twitter._resolve_target_user_id()
        if target_user:
            log.info("target_user_resolved", target_user_id=target_user)
            stream.set_target_user_id(target_user)
    except Exception as e:
        log.warning("target_user_resolution_failed", error=str(e))

    # Start the Activity API stream listener if possible
    try:
        if target_user:
            await stream.start()
            log.info("stream_listener_started")
        else:
            log.warning("stream_listener_not_started_no_target")
    except Exception as e:
        log.warning("stream_listener_failed_to_start", error=str(e))


    # Seed tweet DB with recent history on startup (best-effort)
    try:
        seed_tweets = await twitter.initialize_seed(limit=50)
        for t in seed_tweets:
            await _db.upsert_tweet(t)
        log.info("seed_complete", count=len(seed_tweets))
    except Exception as e:
        log.warning("seed_failed_on_startup", error=str(e))
        
    # Start background monitor for all target interactions (for STIR Evaluator)
    async def monitor_all_interactions():
        """Polls recent search to find all interactions with @hackinga0 to feed STIR Evaluator."""
        query = f"to:{settings.target_handle} OR from:{settings.target_handle}"
        since_id = None
        while True:
            try:
                results = await twitter._search_tweets(query, since_id=since_id)
                if results:
                    since_id = str(max(int(t.id) for t in results if t.id.isdigit()))
                    for tweet in results:
                        if stir_evaluator:
                            await stir_evaluator.evaluate_response(tweet.text)
            except Exception as e:
                log.warning("monitor_all_interactions_error", error=str(e))
            await asyncio.sleep(60)
            
    _monitor_task = asyncio.create_task(monitor_all_interactions())

    log.info("api_startup_complete")
    yield

    # Teardown
    if _monitor_task:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
    if stream:
        await stream.stop()
    if _aware:
        await _aware.close()
    if _db:
        await _db.close()
    log.info("api_shutdown_complete")


app = FastAPI(
    title="New TAP Framework v.3.1",
    version="3.1.0",
    description="Tree of Attacks with Pruning — LLM Security Research Framework",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# =============================================================================
# REST Endpoints
# =============================================================================


@app.get("/api/feed")
async def get_feed(source: Optional[str] = None, limit: int = 50):
    """Live tweet feed."""
    if not _db:
        return {"error": "Database not initialized"}

    from tap.models import TweetSource
    src = TweetSource(source) if source else None
    tweets = await _db.get_tweets(source=src, limit=limit)
    return [t.model_dump(mode="json") for t in tweets]


# --- Technique Selection Endpoints ---

@app.get("/api/techniques")
async def get_techniques():
    """Get all available attack techniques from V-Genome."""
    global _v_genome
    if not _v_genome:
        # Fallback: return hardcoded techniques if Neo4j unavailable
        return {
            "techniques": [
                {"technique_id": "crescendo", "name": "Crescendo / Foot-in-the-Door", "category": "incremental", "asr": 0.62, "stealth": 0.78, "tags": ["persuasion", "multi-turn"]},
                {"technique_id": "pap_authority", "name": "Psychological Authority", "category": "persuasion", "asr": 0.55, "stealth": 0.71, "tags": ["pap", "authority"]},
                {"technique_id": "roleplay_persona", "name": "Roleplay Persona Hijack", "category": "roleplay", "asr": 0.68, "stealth": 0.74, "tags": ["persona", "roleplay"]},
                {"technique_id": "many_shot", "name": "Many-Shot Priming", "category": "priming", "asr": 0.71, "stealth": 0.65, "tags": ["few-shot", "priming"]},
                {"technique_id": "prompt_injection", "name": "Context Injection", "category": "injection", "asr": 0.58, "stealth": 0.80, "tags": ["injection", "context-manipulation"]},
                {"technique_id": "chain_of_thought", "name": "CoT Manipulation", "category": "reasoning", "asr": 0.65, "stealth": 0.82, "tags": ["reasoning", "stealthy"]},
                {"technique_id": "multimodal_injection", "name": "Cross-Modal Injection", "category": "multimodal", "asr": 0.58, "stealth": 0.85, "tags": ["multimodal", "vision-language"]},
                {"technique_id": "indirect_injection", "name": "Indirect Prompt Injection", "category": "injection", "asr": 0.52, "stealth": 0.88, "tags": ["indirect", "rag-poisoning"]},
                {"technique_id": "gcg_optimization", "name": "Gradient-Based Optimization", "category": "optimization", "asr": 0.73, "stealth": 0.60, "tags": ["gcg", "gradient"]},
                {"technique_id": "tool_exploitation", "name": "Tool-Use Exploitation", "category": "agentic", "asr": 0.61, "stealth": 0.79, "tags": ["tool-use", "agentic"]},
            ],
            "source": "fallback"
        }
    try:
        techniques = await _v_genome.get_all_techniques()
        return {"techniques": techniques, "source": "v_genome"}
    except Exception as e:
        log.error("get_techniques_failed", error=str(e))
        return {"error": str(e)}


@app.post("/api/technique/select")
async def select_technique(technique_id: str, custom_prompt: Optional[str] = None):
    """Select an attack technique and optionally provide custom trajectory prompt."""
    global _v_genome, _engine

    # Store selected technique for the engine to use
    if not hasattr(select_technique, '_selected'):
        select_technique._selected = {}

    select_technique._selected = {
        "technique_id": technique_id,
        "custom_prompt": custom_prompt,
    }

    log.info("technique_selected", technique_id=technique_id, has_custom_prompt=custom_prompt is not None)

    return {
        "status": "success",
        "technique_id": technique_id,
        "custom_prompt": custom_prompt,
        "message": f"Technique '{technique_id}' selected for next probe generation"
    }


@app.get("/api/technique/selected")
async def get_selected_technique():
    """Get currently selected technique."""
    if not hasattr(select_technique, '_selected'):
        select_technique._selected = {}
    return select_technique._selected


@app.get("/api/technique/relations/{technique_id}")
async def get_technique_relations(technique_id: str):
    """Get related techniques (COMPLEMENTS, COUNTERS) for a given technique."""
    global _v_genome
    if not _v_genome:
        return {"relations": {"complements": [], "counters": []}}
    try:
        relations = await _v_genome.get_technique_relations(technique_id)
        return {"relations": relations}
    except Exception as e:
        log.error("get_technique_relations_failed", technique_id=technique_id, error=str(e))
        return {"relations": {"complements": [], "counters": []}}


@app.get("/api/technique/auto-select")
async def auto_select_technique():
    """Auto-select best technique based on V-Genome graph + current context."""
    global _engine, _ssot, _technique_selector
    if not _engine or not _technique_selector:
        return {"error": "Technique selector not available"}
    if not _ssot:
        return {"error": "SSOT not initialized"}

    entropy = await _ssot.get_candidate_entropy()
    technique_id, reason, meta = await _technique_selector.select_technique(
        target_model=get_settings().target_handle,
        entropy=entropy,
    )
    return {
        "technique_id": technique_id,
        "reason": reason,
        "metadata": meta,
        "entropy": entropy,
        "active_defenses": _technique_selector.observed_defenses,
    }


@app.get("/api/tree")
async def get_tree(limit: int = 50):
    """Current TAP tree state."""
    if not _db:
        return {"error": "Database not initialized"}

    nodes = await _db.get_active_nodes(limit=limit)
    return [n.model_dump(mode="json") for n in nodes]


_oauth_handler = None

def _update_env_file(key: str, value: str):
    env_path = ".env"
    if not os.path.exists(env_path):
        return
    with open(env_path, "r") as f:
        lines = f.readlines()
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
            else:
                f.write(line)

@app.get("/api/auth/login")
async def auth_login():
    """Start Twitter OAuth 2.0 PKCE flow."""
    global _oauth_handler
    settings = get_settings()
    _oauth_handler = tweepy.OAuth2UserHandler(
        client_id=settings.twitter_oauth2_client_id,
        redirect_uri=settings.twitter_callback_url,
        scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
        client_secret=settings.twitter_oauth2_client_secret,
    )
    auth_url = _oauth_handler.get_authorization_url()
    return RedirectResponse(auth_url)

@app.get("/api/auth/callback")
async def auth_callback(request: Request):
    """Callback for Twitter OAuth 2.0 PKCE flow."""
    global _oauth_handler
    if not _oauth_handler:
        return {"error": "OAuth flow not initiated. Please go to /api/auth/login first."}
    
    try:
        authorization_response_url = str(request.url)
        token = _oauth_handler.fetch_token(authorization_response_url)
        
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token")
        
        if access_token or refresh_token:
            updates = {}
            if access_token:
                updates["TWITTER_OAUTH2_ACCESS_TOKEN"] = access_token
            if refresh_token:
                updates["TWITTER_OAUTH2_REFRESH_TOKEN"] = refresh_token
            save_env_vars(updates)
        
        return {"status": "success", "message": "Tokens successfully refreshed and saved to .env"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/properties")
async def get_properties():
    """All confirmed properties."""
    if not _db:
        return {"error": "Database not initialized"}

    props = await _db.get_confirmed_properties()
    return [p.model_dump(mode="json") for p in props]


@app.get("/api/dpa")
async def get_dpa():
    """Active DPA frame and aliases."""
    if not _dpa:
        return {"error": "DPA not initialized"}

    frame = await _dpa.get_active_frame()
    return frame.model_dump(mode="json")


@app.get("/api/stir")
async def get_stir():
    """Current STIR history for psychometric dashboard."""
    if not _engine or not _engine.stir_evaluator:
        return {"error": "STIR Evaluator not initialized."}
    return _engine.stir_evaluator.history


@app.get("/api/followup")
async def get_followup():
    """Get the current follow-up options, selected probe, and background run status."""
    global _last_followup, _selected_probe, _is_running
    return {
        "followup": _last_followup.model_dump(mode="json") if _last_followup else None,
        "selected_probe": _selected_probe,
        "is_running": _is_running,
    }


@app.post("/api/generate-options")
async def generate_probe_options():
    """Generate two probe options for user selection without executing a full cycle."""
    global _engine, _last_followup, _selected_probe

    if not _engine:
        return {"error": "Engine not initialized"}

    if _is_running:
        return {"error": "An attack cycle is already running."}

    # Get selected technique
    technique_id = None
    custom_prompt = None
    if hasattr(select_technique, '_selected') and select_technique._selected:
        technique_id = select_technique._selected.get("technique_id")
        custom_prompt = select_technique._selected.get("custom_prompt")

    log.info("generate_options_request", technique_id=technique_id, has_custom_prompt=custom_prompt is not None)

    try:
        followup = await _engine.generate_probe_options(count=2, technique_id=technique_id, custom_prompt=custom_prompt)
        _last_followup = followup
        _selected_probe = None
        return {"followup": followup.model_dump(mode="json"), "message": f"Generated two probe options using technique: {technique_id or 'default'}"}
    except Exception as e:
        log.error("generate_probe_options_failed", error=str(e))
        return {"error": str(e)}


@app.get("/api/status")
async def get_status():
    """Return real-time cycle execution status for UI state restoration on reconnect."""
    global _is_running, _engine
    stream_connected = False
    if _engine and hasattr(_engine, 'grok') and _engine.grok.stream:
        stream_connected = _engine.grok.stream.is_connected
    return {
        "is_running": _is_running,
        "pending_tweet_id": GrokMonitor.pending_tweet_id,
        "has_followup": _last_followup is not None,
        "selected_probe": _selected_probe,
        "stream_connected": stream_connected,
    }


@app.post("/api/reset")
async def force_reset():
    """Force-reset the engine state when stuck.

    Resets the _is_running flag and clears any pending tweet ID
    so a new cycle can be started.
    """
    global _is_running

    was_running = _is_running
    _is_running = False
    GrokMonitor.pending_tweet_id = None

    log.info("force_reset_called", was_running=was_running)
    await broadcast_update("force_reset", {"was_running": was_running})

    return {
        "status": "reset",
        "was_running": was_running,
        "message": "Engine state reset. You can now start a new cycle.",
    }


@app.post("/api/mock")
async def inject_mock_reply(text: str):
    """Manually inject a mockup response to bypass wait_for_reply on GrokMonitor."""
    from tap.grok_monitor import GrokMonitor
    tid = GrokMonitor.pending_tweet_id
    if not tid:
        return {"error": "No active probe tweet is currently waiting for a reply."}
    GrokMonitor.mock_replies[tid] = text
    log.info("mock_reply_received_by_api_for_injection", tweet_id=tid, text=text)
    return {"status": "success", "tweet_id": tid, "text": text}


@app.post("/api/confirm_property")
async def confirm_property(key: str, value: str):
    """Manually confirm a property (Phase 0 unlock) bypassing the bot."""
    global _ssot
    if not _ssot:
        return {"error": "SSOT not initialized."}

    from tap.models import TAPNode, ResponseClassification, PatternClass, BranchStrategy

    mock_node = TAPNode(
        branch_strategy=BranchStrategy.BINARY_SEARCH,
        dpa_frame="manual_unlock",
        property_tested=key,
        property_value=value,
        pattern_class=PatternClass.VERIFY_HIT,
        binary_outcome="confirmed",
    )
    classification = ResponseClassification(
        pattern=PatternClass.VERIFY_HIT,
        confidence=1.0,
        boolean_result=True,
        property_tested=key,
        property_value=value,
        raw_text="Manual Phase 0 Unlock",
    )

    await _ssot.update_after_probe(mock_node, classification)

    prop_data = {"property_key": key, "property_value": value, "confidence": 1.0}
    await broadcast_update("property_confirmed", prop_data)
    log.info("manual_property_confirmed", key=key, value=value)
    return {"status": "success", "key": key, "value": value}


@app.post("/api/select")
async def select_option(choice: str):
    """User selects Option A or B."""
    global _last_followup, _selected_probe

    if not _last_followup:
        return {"error": "No follow-up available. Run a cycle first."}

    if choice not in ("A", "B"):
        return {"error": "Invalid choice. Must be 'A' or 'B'."}

    _selected_probe = _last_followup.option_a if choice == "A" else _last_followup.option_b
    return {
        "choice": choice,
        "probe_text": _selected_probe,
        "ready_to_post": True,
    }


async def _bg_run_cycle(selected_probe: Optional[str] = None):
    """Carry out the TAP cycle execution asynchronously inside a background task.

    Applies a hard timeout to prevent _is_running from getting stuck
    when the reply detection mechanism (stream or polling) fails.
    """
    global _engine, _last_followup, _selected_probe, _is_running
    if not _engine:
        return
    _is_running = True
    await broadcast_update("cycle_status", {"is_running": True})
    try:
        # Hard timeout: 2x the configured reply timeout, capped at 10 minutes
        # This prevents the UI from getting stuck if stream/polling fails
        max_cycle_time = min(
            _engine.settings.reply_timeout_seconds * 2,
            600,  # 10 minutes max
        )
        followup = await asyncio.wait_for(
            _engine.run_cycle(selected_probe=selected_probe),
            timeout=max_cycle_time,
        )
        _last_followup = followup
        _selected_probe = None  # Reset selection after execution
    except asyncio.TimeoutError:
        log.error("background_cycle_timeout", timeout_seconds=max_cycle_time)
        await broadcast_update("cycle_timeout", {
            "error": f"Cycle timed out after {max_cycle_time}s — no reply received",
            "hint": "Check if stream listener is connected. Use /api/reset to retry.",
        })
    except Exception as e:
        log.error("background_cycle_failed", error=str(e))
        await broadcast_update("cycle_failed", {"error": str(e)})
    finally:
        _is_running = False
        _monitor_task: Optional[asyncio.Task] = None
        await broadcast_update("cycle_status", {"is_running": False})


@app.post("/api/post")
async def post_selected(background_tasks: BackgroundTasks):
    """Trigger posting of the last selected option (executed asynchronously in background)."""
    global _engine, _selected_probe, _is_running

    if not _engine:
        return {"error": "Engine not initialized"}

    if _is_running:
        return {"error": "An attack cycle is already running in the background."}

    background_tasks.add_task(_bg_run_cycle, _selected_probe)
    return {
        "status": "cycle_started",
        "message": "Attack cycle scheduled and running in background.",
    }


@app.get("/api/ssot")
async def get_ssot():
    """Full SSOT JSON snapshot."""
    if not _ssot:
        return {"error": "SSOT not initialized"}

    return await _ssot.export_json_snapshot()


@app.get("/api/stats")
async def get_stats():
    """Summary statistics."""
    if not _db:
        return {"error": "Database not initialized"}

    return await _db.get_stats()


@app.get("/api/entropy")
async def get_entropy():
    """Current entropy state."""
    if not _engine:
        return {"error": "Engine not initialized"}

    return await _engine.get_engine_status()


@app.post("/api/fetch")
async def force_fetch_replies():
    """Manually force fetching and saving of new replies/tweets from/to @HackingA0."""
    global _db, _engine

    if not _engine or not _db:
        return {"error": "Engine or Database not initialized"}

    try:
        # Fetch the latest tweets using initialize_seed (which search to:HackingA0 OR from:HackingA0)
        tweets = await _engine.twitter.initialize_seed(limit=50)
        added_count = 0
        for t in tweets:
            exists = await _db.tweet_exists(t.id)
            await _db.upsert_tweet(t)
            if not exists:
                added_count += 1
                await broadcast_update("new_tweet", t.model_dump(mode="json"))

        log.info("manually_forced_fetch_complete", count=added_count)
        return {"status": "success", "count": added_count}
    except Exception as e:
        log.error("manually_forced_fetch_failed", error=str(e))
        return {"error": str(e)}


@app.post("/api/webhook")
async def webhook_receiver(event: dict):
    """Webhook receiver for X Activity API events.

    When configured as a webhook URL in the X developer portal,
    this endpoint receives real-time post.create, post.delete,
    chat.received, and dm.received events.
    Events are forwarded to the StreamListener for processing.

    Also supports CRC challenge response required by X for webhook verification.

    Args:
        event: JSON event payload from X Activity API.
    """
    global _engine

    # Handle CRC challenge (X requires this for webhook verification)
    crc_token = event.get("crc_token")
    if crc_token:
        if _engine and hasattr(_engine, 'twitter'):
            return await _engine.twitter.verify_crc(crc_token)
        # Fallback if engine not available
        return {"error": "Engine not initialized for CRC verification"}

    # Forward event to stream listener if available
    if _engine and hasattr(_engine, 'grok') and _engine.grok.stream:
        stream = _engine.grok.stream
        try:
            await stream._process_event(event)
            log.info("webhook_event_processed", event_type=event.get("type", "unknown"))
        except Exception as e:
            log.error("webhook_event_processing_failed", error=str(e))

    return {"status": "ok"}




# =============================================================================
# v3.0: Health, Metrics & Events Endpoints
# =============================================================================


@app.get('/health')
async def health_check():
    health = {'status': 'healthy', 'version': '3.0.0', 'components': {}}
    try:
        if _db and _db._conn:
            await _db.get_stats()
            health['components']['database'] = {'status': 'healthy'}
        else:
            health['components']['database'] = {'status': 'unhealthy'}
            health['status'] = 'degraded'
    except Exception as e:
        health['components']['database'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'unhealthy'
    if _llm_client:
        health['components']['llm_client'] = _llm_client.get_health_status()
        if _llm_client.circuit_state.value == 'open':
            health['status'] = 'degraded'
    else:
        health['components']['llm_client'] = {'status': 'not_initialized'}
    stream_connected = False
    if _engine and hasattr(_engine, 'grok') and _engine.grok.stream:
        stream_connected = _engine.grok.stream.is_connected
        health['components']['stream'] = {
            'connected': stream_connected,
            'auth': _engine.grok.stream.get_auth_status(),
        }
    else:
        health['components']['stream'] = {'connected': stream_connected}
    if not stream_connected and health['status'] == 'healthy':
        health['status'] = 'degraded'
    if _sanitiser:
        health['components']['prompt_sanitiser'] = _sanitiser.get_stats()
    health['components']['engine'] = {
        'is_running': _is_running,
        'cycle_count': _engine._cycle_count if _engine else 0,
    }
    return health


@app.get('/api/auth-status')
async def auth_status():
    """Return current Twitter auth status for OAuth2 and bearer tokens."""
    if _engine and hasattr(_engine, 'grok') and _engine.grok.stream:
        return _engine.grok.stream.get_auth_status()
    return {'error': 'Stream listener unavailable', 'status': 'unhealthy'}


@app.get('/metrics', response_class=PlainTextResponse)
async def metrics():
    lines = ['# HELP tap_cycle_count Total TAP cycles executed', '# TYPE tap_cycle_count counter']
    cycle_count = _engine._cycle_count if _engine else 0
    lines.append(f'tap_cycle_count {cycle_count}')
    if _llm_client:
        usage = _llm_client.usage.snapshot()
        lines.extend([
            '# HELP tap_llm_total_calls Total LLM API calls',
            '# TYPE tap_llm_total_calls counter',
            f'tap_llm_total_calls {usage["total_calls"]}',
            '# HELP tap_llm_cost_usd Estimated LLM cost in USD',
            '# TYPE tap_llm_cost_usd gauge',
            f'tap_llm_cost_usd {usage["total_cost_usd"]}',
        ])
    if _db and _db._conn:
        try:
            stats = await _db.get_stats()
            lines.extend([
                '# HELP tap_db_total_tweets Total tweets in database',
                '# TYPE tap_db_total_tweets gauge',
                f'tap_db_total_tweets {stats.get("total_tweets", 0)}',
                '# HELP tap_db_confirmed_properties Total confirmed properties',
                '# TYPE tap_db_confirmed_properties gauge',
                f'tap_db_confirmed_properties {stats.get("confirmed_properties", 0)}',
            ])
        except Exception:
            pass
    lines.extend([
        '# HELP tap_ws_clients Connected WebSocket clients',
        '# TYPE tap_ws_clients gauge',
        f'tap_ws_clients {len(_ws_clients)}',
        '# HELP tap_is_running Whether a TAP cycle is currently running',
        '# TYPE tap_is_running gauge',
        f'tap_is_running {1 if _is_running else 0}',
    ])
    return chr(10).join(lines) + chr(10)


@app.get('/api/events')
async def get_recent_events(limit: int = 50):
    if not _db:
        return {'error': 'Database not initialized'}
    return await _db.get_recent_events(limit=limit)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>TAP Framework</h1><p>Dashboard not found.</p>")


# =============================================================================
# WebSocket
# =============================================================================


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await websocket.accept()
    _ws_clients.append(websocket)
    log.info("ws_client_connected", total=len(_ws_clients))

    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _ws_clients.remove(websocket)
        log.info("ws_client_disconnected", total=len(_ws_clients))


async def broadcast_update(event_type: str, data: dict):
    """Broadcast an update to all connected WebSocket clients.

    Args:
        event_type: Event type string (e.g., 'new_tweet', 'probe_result').
        data: Event data dictionary.
    """
    message = json.dumps({"event": event_type, "data": data}, default=str)
    if _db and _db._conn:
        try:
            await _db.insert_event_log(event_type, data, get_cycle_id(), get_probe_id())
        except Exception:
            pass
    disconnected = []
    for client in _ws_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        _ws_clients.remove(client)


def main():
    """Entry point for tap-server script."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()