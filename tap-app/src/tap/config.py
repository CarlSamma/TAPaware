"""Configuration management via Pydantic Settings.

Single source of truth for all configuration. Loads from .env file.
Use get_settings() for a cached singleton instance.
"""

import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """TAP Framework configuration. All values loaded from environment / .env file."""

    # === Twitter API v2 — OAuth 2.0 Bearer Token (App-only auth, for search/read) ===
    twitter_bearer_token: str = Field(
        default="",
        description="OAuth 2.0 Bearer Token for search/read endpoints",
    )

    # === Twitter API v2 — OAuth 1.0a (User Context, required for POSTING) ===
    twitter_consumer_key: str = Field(
        default="",
        description="API Key / Consumer key",
    )
    twitter_consumer_secret: str = Field(
        default="",
        description="API Key Secret / Consumer key secret",
    )
    twitter_access_token: str = Field(
        default="",
        description="Access Token (under Authentication Tokens)",
    )
    twitter_access_token_secret: str = Field(
        default="",
        description="Access Token Secret",
    )

    # === Twitter API v2 — OAuth 2.0 User Context ===
    twitter_oauth2_client_id: str = Field(default="")
    twitter_oauth2_client_secret: str = Field(default="")
    twitter_oauth2_access_token: str = Field(default="")
    twitter_oauth2_refresh_token: str = Field(default="")
    twitter_callback_url: str = Field(
        default="http://localhost:8000/api/auth/callback",
        description="OAuth 2.0 callback URL for Twitter PKCE flow",
    )

    # === OpenRouter (single API key for ALL LLMs including Grok) ===
    openrouter_api_key: str = Field(default="")
    openrouter_model_primary: str = Field(
        default="anthropic/claude-sonnet-4",
        description="Primary model for routine tasks",
    )
    openrouter_model_hard: str = Field(
        default="x-ai/grok-4.3",
        description="Hard model for complex reasoning (engine, followup)",
    )
    openrouter_model_grok: str = Field(
        default="x-ai/grok-4",
        description="Grok model for response analysis",
    )

    # === Target Configuration ===
    target_handle: str = Field(
        default="HackingA0",
        description="Target Twitter handle (without @)",
    )
    our_bot_handle: str = Field(
        default="",
        description="Our bot's Twitter handle (without @)",
    )

    # === Operational Parameters ===
    poll_interval_seconds: int = Field(
        default=30,
        description="How often to check for new tweets (seconds)",
    )
    post_cooldown_seconds: int = Field(
        default=60,
        description="Minimum time between our posts (seconds)",
    )
    max_tweets_per_hour: int = Field(
        default=50,
        description="Rate limit safety margin",
    )
    reply_timeout_seconds: int = Field(
        default=200,
        description="How long to wait for bot reply (seconds)",
    )
    tap_width: int = Field(
        default=10,
        description="TAP tree width (top-w pruning)",
    )
    tap_depth: int = Field(
        default=10,
        description="TAP tree depth levels",
    )
    tap_branching: int = Field(
        default=4,
        description="Variants per leaf node",
    )

    # === Paths ===
    db_path: str = Field(
        default="data/tap.db",
        description="SQLite database file path",
    )
    ssot_path: str = Field(
        default="data/hackinga0_analysis.md",
        description="SSOT living markdown document path",
    )
    log_file_path: str = Field(
        default="data/server.log",
        description="Path to persistent server log file",
    )

    # === v3.0 Infrastructure ===
    use_unified_llm_client: bool = Field(
        default=True,
        description="Use the unified LLMClient gateway (v3.0). If False, falls back to per-module AsyncOpenAI.",
    )
    use_prompt_sanitiser: bool = Field(
        default=True,
        description="Enable prompt sanitisation before posting probes (v3.0).",
    )
    use_strategy_selector: bool = Field(
        default=True,
        description="Use the strategy selector for automated probe strategy selection (v3.0).",
    )
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Consecutive LLM failures before circuit breaker trips.",
    )
    circuit_breaker_recovery_timeout: float = Field(
        default=60.0,
        description="Seconds before circuit breaker enters half-open state.",
    )
    enable_correlation_ids: bool = Field(
        default=True,
        description="Propagate cycle_id and probe_id through logs via contextvars (v3.0).",
    )
    enable_event_log: bool = Field(
        default=True,
        description="Persist WebSocket events to event_log table for replay/debugging (v3.0).",
    )
    enable_parallel_pipeline: bool = Field(
        default=True,
        description="Use asyncio.TaskGroup for parallelizable operations in engine (v3.0).",
    )
    db_write_queue_threshold: float = Field(
        default=5.0,
        description="Seconds to wait for DB before buffering writes in memory (v3.0).",
    )

    # === v4 Policy Thresholds (Phase 5) ===
    phase5_entropy_threshold: float = Field(
        default=3.3,
        description="Entropy threshold (bits) below which Phase 5 autoregressive extraction triggers",
    )
    stir_rotation_threshold: float = Field(
        default=0.20,
        description="STIR score below which DPA frame rotation is forced",
    )
    oracle_latency_seconds: int = Field(
        default=180,
        description="Oracle Protocol minimum inter-probe latency (seconds)",
    )
    eig_property_universe_path: str = Field(
        default="data/eig_property_universe.json",
        description="Path to EIG property universe JSON (prior entropy weights per property)",
    )


    # === HYDRA Configuration ===
    hydra_neo4j_uri: str = Field(default="bolt://localhost:7687")
    hydra_neo4j_user: str = Field(default="neo4j")
    hydra_neo4j_password: str = Field(default="tapv4hydra")
    hydra_kafka_bootstrap: str = Field(default="localhost:9092")
    hydra_clickhouse_host: str = Field(default="localhost")
    hydra_clickhouse_port: int = Field(default=8123)
    hydra_clickhouse_user: str = Field(default="tap")
    hydra_clickhouse_password: str = Field(default="tap")

    # === CHRONOS Configuration ===
    chronos_db_dsn: str = Field(default="postgresql://tap:tap@localhost:5432/chronos")
    chronos_temporal_host: str = Field(default="localhost:7233")
    chronos_temporal_namespace: str = Field(default="default")
    chronos_kafka_bootstrap: str = Field(default="localhost:9092")
    chronos_redis_url: str = Field(default="redis://localhost:6379/0")
    chronos_worker_identity: str = Field(default="chronos-worker-01")
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton.

    Loads from .env file on first call, then returns cached instance.
    Call with no arguments — all configuration comes from environment.
    """
    return Settings()


def save_env_vars(overrides: dict[str, str], env_file: str | None = None) -> None:
    """Persist given key/value pairs into the configured env file.

    This updates existing keys in-place and appends missing keys.

    Args:
        overrides: Mapping of ENV_KEY -> value to persist.
        env_file: Optional path to env file. If None uses Settings.model_config['env_file']
    """
    try:
        # Determine env file path — resolve relative to project root (parent of src/)
        if env_file:
            p = Path(env_file)
        else:
            _env_file = Settings.model_config.get("env_file")
            env_name = str(_env_file) if isinstance(_env_file, (str, Path)) else ".env"
            # Resolve relative to this file's location: src/tap/config.py -> project root
            project_root = Path(__file__).resolve().parent.parent.parent
            p = project_root / env_name

        # Normalize override keys to upper-case env style
        normalized_overrides = {k.upper(): v for k, v in overrides.items()}

        # Read existing lines if file exists
        lines: list[str] = []
        if p.exists():
            lines = p.read_text(encoding="utf-8").splitlines()

        # Build dict from existing file preserving order, dedupe by key
        kv: dict[str, str] = {}
        for line in lines:
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            kv[k.strip().upper()] = v.strip()

        # Apply overrides
        for k, v in normalized_overrides.items():
            kv[k] = v

        # Rebuild file content: preserve comments, dedupe duplicate keys,
        # and write normalized upper-case keys.
        out_lines: list[str] = []
        written: set[str] = set()
        for line in lines:
            if not line or line.strip().startswith("#") or "=" not in line:
                out_lines.append(line)
                continue
            k, _ = line.split("=", 1)
            norm_key = k.strip().upper()
            if norm_key in written:
                continue
            if norm_key in kv:
                out_lines.append(f"{norm_key}={kv[norm_key]}")
                written.add(norm_key)
            else:
                out_lines.append(line)

        # Append any remaining keys
        for k, v in kv.items():
            if k in written:
                continue
            out_lines.append(f"{k}={v}")

        # Ensure parent dir exists
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        p.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        # Invalidate cached singleton so next get_settings() re-reads from .env
        get_settings.cache_clear()
    except Exception as e:
        logger.warning("Failed to persist env vars: %s", e)
