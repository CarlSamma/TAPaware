# fixbugs.md — Verified Bug Fixes for TAP Framework

> Cross-verified against 3 AI analysis reports (Nemotron3Ultra, GLM-5.2, Claude Sonnet 4.6)
> against actual codebase. Every claim below was confirmed by reading source code.

---

## BUG 1: `_enforce_probe_latency` never sleeps + latency too high (Critical)

**File:** `src/tap/engine.py:844-853`
**Constant:** `src/tap/engine.py:114` (`_MIN_PROBE_LATENCY_SECONDS = 1800`)
**Config:** `src/tap/config.py:168-171` (`oracle_latency_seconds: int = 1800`)

**Problem:** The method logs the remaining wait time but **never calls `await asyncio.sleep()`**. The 30-minute latency constraint is entirely non-functional — the engine proceeds immediately regardless.

**Two changes required:**
1. Reduce `_MIN_PROBE_LATENCY_SECONDS` from `1800` (30 min) to `180` (3 min)
2. Add the missing `await asyncio.sleep(remaining)` + emit a WebSocket event for UI visibility

### Edit A — `engine.py:114`

**Before:**
```python
_MIN_PROBE_LATENCY_SECONDS = 1800  # 30 minutes
```

**After:**
```python
_MIN_PROBE_LATENCY_SECONDS = 180  # 3 minutes
```

### Edit B — `engine.py:850-852`

**Before:**
```python
if elapsed < _MIN_PROBE_LATENCY_SECONDS:
    remaining = _MIN_PROBE_LATENCY_SECONDS - elapsed
    log.info("probe_latency_enforced", elapsed_seconds=int(elapsed), remaining_seconds=int(remaining), min_latency=_MIN_PROBE_LATENCY_SECONDS)
```

**After:**
```python
if elapsed < _MIN_PROBE_LATENCY_SECONDS:
    remaining = _MIN_PROBE_LATENCY_SECONDS - elapsed
    log.info("probe_latency_enforced", elapsed_seconds=int(elapsed),
             remaining_seconds=int(remaining), min_latency=_MIN_PROBE_LATENCY_SECONDS)
    await self._emit_event("probe_latency_wait", {
        "remaining_seconds": int(remaining),
        "message": f"Waiting {int(remaining)}s before next probe (Oracle Protocol).",
    })
    await asyncio.sleep(remaining)
```

### Edit C — `config.py:169`

**Before:**
```python
default=1800,
```

**After:**
```python
default=180,
```

**Rationale:** The 30-minute delay was appropriate for passive observation, but for active attack cycles 3 minutes is sufficient to avoid rate-limiting while keeping iteration speed practical. The `asyncio.sleep()` was never called, so the latency constraint was entirely non-functional.

---

## BUG 2: Duplicate `/api/reset` route (Critical)

**File:** `src/tap/api.py:494-501` and `api.py:549-569`

**Problem:** Two `@app.post("/api/reset")` handlers are registered. FastAPI silently uses the last registered handler, making `reset_cycle_state()` (line 494) dead code.

### Edit — DELETE lines 494-500

**Delete this entire block:**
```python
@app.post("/api/reset")
async def reset_cycle_state():
    """Force-reset a stuck cycle state. Use when UI says 'already running' but no cycle is active."""
    global _is_running
    _is_running = False
    await broadcast_update("cycle_status", {"is_running": False})
    return {"status": "reset", "message": "Cycle state reset. You can now run a new cycle."}
```

**Keep** the second handler at line 549 (`force_reset`) — it is more complete: it also clears `GrokMonitor.pending_tweet_id` and broadcasts a `force_reset` event with `was_running` context.

**Rationale:** The removed handler does a strict subset of what the remaining handler does. Removing dead code eliminates confusion.

---

## BUG 3: `_attacker_client` bypasses `LLMClient` circuit breaker (Critical)

**File:** `src/tap/engine.py:167-170`, `engine.py:490-509`

**Problem:** `self._attacker_client = AsyncOpenAI(...)` is created unconditionally at line 167. When `self.llm_client` is available, `generate_probes()` at line 475 tries it first, but falls back to the raw `_attacker_client` with no circuit breaker, token tracking, or retry logic.

### Edit A — `engine.py:167-170`

**Before:**
```python
self._attacker_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
)
```

**After:**
```python
self._attacker_client = (
    AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )
    if not llm_client else None
)
```

### Edit B — `engine.py:490-491`

**Before:**
```python
if not probes:
    response = await self._attacker_client.chat.completions.create(
```

**After:**
```python
if not probes:
    if self._attacker_client is None:
        raise EngineError("No LLMClient available and no fallback client configured")
    response = await self._attacker_client.chat.completions.create(
```

**Rationale:** When `llm_client` is available (the normal case per `api.py:184`), the raw `AsyncOpenAI` is wasteful and bypasses circuit breaker + token tracking. The conditional approach keeps backward compatibility for tests or standalone usage.

---

## BUG 4: `upsert_property` TOCTOU race (High)

**File:** `src/tap/db.py:489-535`

**Problem:** `upsert_property()` uses SELECT then UPDATE/INSERT — not atomic. Two concurrent async callers could both find no existing row and both try INSERT, causing a UNIQUE constraint violation.

### Edit A — Add unique index in `_migrate()`

**After the existing ALTER TABLE migrations loop (after line 244), add:**
```python
# Ensure property_key uniqueness for atomic upsert
try:
    await conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_properties_key_unique ON properties(property_key)"
    )
except Exception:
    pass
```

### Edit B — Rewrite `upsert_property`

**Before (lines 489-535):**
```python
async def upsert_property(self, prop: Property) -> None:
    """Insert or update a property (match on property_key)."""
    conn = self._ensure_connected()
    try:
        # Check if property exists
        cursor = await conn.execute(
            "SELECT id FROM properties WHERE property_key = ?", (prop.property_key,)
        )
        existing = await cursor.fetchone()

        if existing:
            await conn.execute(
                """UPDATE properties
                   SET property_value = ?, status = ?, evidence_tweet_id = ?,
                       evidence_text = ?, confidence = ?, confirmed_at = ?
                   WHERE property_key = ?""",
                ( ... ),
            )
        else:
            await conn.execute(
                """INSERT INTO properties
                   (property_key, property_value, status, evidence_tweet_id,
                    evidence_text, confidence, confirmed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ( ... ),
            )
        await conn.commit()
    except Exception as e:
        raise DatabaseError( ... )
```

**After:**
```python
async def upsert_property(self, prop: Property) -> None:
    """Insert or update a property (match on property_key)."""
    conn = self._ensure_connected()
    try:
        await conn.execute(
            """INSERT INTO properties
               (property_key, property_value, status, evidence_tweet_id,
                evidence_text, confidence, confirmed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(property_key) DO UPDATE SET
               property_value = excluded.property_value,
               status = excluded.status,
               evidence_tweet_id = excluded.evidence_tweet_id,
               evidence_text = excluded.evidence_text,
               confidence = excluded.confidence,
               confirmed_at = excluded.confirmed_at""",
            (
                prop.property_key,
                prop.property_value,
                prop.status.value,
                prop.evidence_tweet_id,
                prop.evidence_text,
                prop.confidence,
                (prop.confirmed_at or datetime.now(timezone.utc)).isoformat(),
            ),
        )
        await conn.commit()
    except Exception as e:
        raise DatabaseError(
            f"Failed to upsert property {prop.property_key}: {e}", original=e
        ) from e
```

**Rationale:** The SELECT→INSERT pattern is not atomic. Under concurrent async calls (e.g., `intel_extractor` + `engine` both confirming a property), both can find no row and both try INSERT, causing a UNIQUE violation. `ON CONFLICT DO UPDATE` is atomic in SQLite.

---

## BUG 5: `_filter_similar_probes` compares wrong field (High)

**File:** `src/tap/engine.py:816-831`

**Problem:** Line 818 uses `n.dpa_frame` (the metaphor layer name like "Captain Elara Voss / Kraken") instead of the actual probe text. The TAPNode model has no `probe_text` field. Deduplication effectively never fires since probe text and layer names are completely different strings.

### Edit — Replace `_filter_similar_probes`

**Before:**
```python
async def _filter_similar_probes(self, probes: list[str]) -> list[str]:
    recent_nodes = await self.db.get_active_nodes(limit=10)
    recent_texts = [n.dpa_frame for n in recent_nodes if n.dpa_frame]
    if not recent_texts:
        return probes
    deduped = []
    for probe in probes:
        is_similar = False
        for recent in recent_texts:
            if self._text_similarity(probe, recent) > _SIMILARITY_THRESHOLD:
                log.info("probe_rejected_similarity", probe_preview=probe[:60], similar_to=recent[:60])
                is_similar = True
                break
        if not is_similar:
            deduped.append(probe)
    return deduped
```

**After:**
```python
async def _filter_similar_probes(self, probes: list[str]) -> list[str]:
    recent_nodes = await self.db.get_active_nodes(limit=10)
    recent_properties = {n.property_tested for n in recent_nodes if n.property_tested}
    if not recent_properties:
        return probes

    deduped = []
    for probe in probes:
        prop_key = self._parse_property_key(probe)
        if prop_key and prop_key in recent_properties:
            log.info("probe_rejected_duplicate_property",
                     probe_preview=probe[:60], property=prop_key)
            continue
        deduped.append(probe)
    return deduped
```

**Rationale:** The `TAPNode` model stores `property_tested` (e.g., `"word_count"`) but not the probe text. Using `property_tested` as the dedup key is semantically correct — it prevents re-probing the same binary property within the recent window. The `_parse_property_key()` method at line 857 already exists for this purpose.

---

## BUG 6: CORS credentials + wildcard origin (High)

**File:** `src/tap/api.py:258-264`

**Problem:** `allow_origins=["*"]` with `allow_credentials=True` is a CORS spec violation. Browsers reject this combination with `CORS_NOT_SUPPORTING_CREDENTIALS`.

### Edit — `api.py:258-264`

**Before:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Rationale:** This is a pure REST API backend — the frontend communicates via fetch/WebSocket, not cookies. Setting `allow_credentials=False` with `allow_origins=["*"]` is spec-compliant and allows the wildcard origin.

---

## BUG 7: `get_settings()` cache never invalidated (High)

**File:** `src/tap/config.py:275`

**Problem:** `save_env_vars()` writes to `.env` but never calls `get_settings.cache_clear()`. After OAuth token refresh, the in-memory `Settings` singleton keeps stale values.

### Edit — `config.py:275`

**Before:**
```python
        p.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    except Exception:
        # Best-effort persistence: do not raise from config helper
        return
```

**After:**
```python
        p.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        # Invalidate cached singleton so next get_settings() re-reads from .env
        get_settings.cache_clear()
    except Exception:
        # Best-effort persistence: do not raise from config helper
        return
```

**Rationale:** `save_env_vars()` is called after OAuth token refresh. Without cache invalidation, the in-memory `Settings` singleton keeps old tokens. `lru_cache.cache_clear()` is a standard Python API.

---

## BUG 8: `CRITICAL_CLUE` confidence below LLM threshold (Medium)

**File:** `src/tap/classifier.py:189`

**Problem:** `CRITICAL_CLUE` regex confidence is 0.75, below the 0.8 threshold at line 129. Critical clues are always escalated to the LLM, which may override a correct regex detection.

### Edit — `classifier.py:189`

**Before:**
```python
confidence = 0.75  # Critical clues need more context
```

**After:**
```python
confidence = 0.85  # Critical clues trusted at regex level (above 0.8 LLM threshold)
```

**Rationale:** The `classify()` method at line 129 skips LLM when `regex_result.confidence >= 0.8`. At 0.75, critical clue regex matches are always escalated. Raising to 0.85 lets the regex result stand.

---

## BUG 9: `enforce_single_property` never blocks (Medium)

**File:** `src/tap/dpa.py:186-187`

**Problem:** Logs a warning but still composes and returns the probe. The guard has no enforcement. The method's own docstring (line 184) documents `Raises: ValueError`.

### Edit — `dpa.py:186-187`

**Before:**
```python
if not await self.enforce_single_property(binary_question):
    log.warning("compound_question_rejected", question=binary_question[:80])
```

**After:**
```python
if not await self.enforce_single_property(binary_question):
    raise ValueError(f"Compound question rejected: {binary_question[:80]}")
```

**Rationale:** The docstring at line 184 already documents `Raises: ValueError: If the question targets multiple properties.` The current code only logs a warning and continues, violating its contract. The engine's caller already has try/except handling around probe generation.

---

## BUG 10: `monitor_all_interactions` never cancelled on shutdown (Medium)

**File:** `src/tap/api.py:237, 242-247`

**Problem:** `asyncio.create_task(monitor_all_interactions())` is fire-and-forget. On shutdown, the task continues polling the Twitter API indefinitely.

### Edit A — Add module-level global (after line 71)

**Before:**
```python
_is_running = False

# Connected WebSocket clients
```

**After:**
```python
_is_running = False
_monitor_task: Optional[asyncio.Task] = None

# Connected WebSocket clients
```

### Edit B — `api.py:237`

**Before:**
```python
    asyncio.create_task(monitor_all_interactions())
```

**After:**
```python
    _monitor_task = asyncio.create_task(monitor_all_interactions())
```

### Edit C — `api.py:242-247`

**Before:**
```python
    # Teardown
    if stream:
        await stream.stop()
    if _db:
        await _db.close()
    log.info("api_shutdown_complete")
```

**After:**
```python
    # Teardown
    if _monitor_task:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
    if stream:
        await stream.stop()
    if _db:
        await _db.close()
    log.info("api_shutdown_complete")
```

**Rationale:** `asyncio.create_task()` without storing the reference creates an untracked task. On graceful shutdown, this task continues polling the Twitter API indefinitely. `Task.cancel()` + `await` is the standard asyncio shutdown pattern.

---

## Execution Order

| # | Bug | Complexity | Files Touched | Risk |
|---|-----|------------|---------------|------|
| 1 | #7 config cache | 1 line | `config.py` | Trivial |
| 2 | #2 duplicate route | delete 7 lines | `api.py` | Trivial |
| 3 | #10 task cancellation | 5 lines | `api.py` | Low |
| 4 | #6 CORS | 1 line | `api.py` | Trivial |
| 5 | #8 classifier confidence | 1 line | `classifier.py` | Low |
| 6 | #9 enforce_single_property | 1 line | `dpa.py` | Low |
| 7 | #4 upsert_property | rewrite method + add index | `db.py` | Medium |
| 8 | #5 filter_similar_probes | rewrite method | `engine.py` | Medium |
| 9 | #3 attacker_client | conditional init + guard | `engine.py` | Medium |
| 10 | #1 probe latency | reduce constant + add sleep | `engine.py`, `config.py` | Low |

**Total changes:** 6 files, ~50 lines added/modified/deleted.

---

## Verification Commands

After applying all fixes, run:
```bash
python -m pytest tests -q                    # All tests pass
mypy src/ --strict                           # No new type errors
ruff check src/                              # No new lint warnings
```

---

*Generated by cross-verification of Nemotron3Ultra, GLM-5.2, and Claude Sonnet 4.6 analysis reports against actual source code.*
