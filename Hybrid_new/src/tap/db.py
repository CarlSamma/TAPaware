"""Module 1: Async SQLite Database Layer.

Provides all CRUD operations for the TAP Framework's persistent storage.
Uses aiosqlite with WAL mode for concurrent reads, foreign keys enabled,
and busy timeout of 5000ms.

Tables:
- tweets: Raw tweet storage
- nodes: TAP tree nodes (attack attempts)
- properties: Confirmed/denied passphrase properties
- metaphor_layers: Metaphor evolution timeline
- aliases: DPA alias registry (active/burned/absorbed)
- other_user_intel: Intelligence from other users' interactions
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite

from tap.exceptions import DatabaseError
from tap.logger import get_logger
from tap.models import (
    Alias,
    AliasStatus,
    BranchStrategy,
    JudgeScore,
    MetaphorLayer,
    OtherUserIntel,
    PatternClass,
    Property,
    PropertyStatus,
    TAPNode,
    Tweet,
    TweetSource,
)

log = get_logger("db")

# SQL Schema
_SCHEMA = """
-- Raw tweet storage
CREATE TABLE IF NOT EXISTS tweets (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    text TEXT NOT NULL,
    in_reply_to_tweet_id TEXT,
    created_at TIMESTAMP NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('our_bot', 'target_bot', 'other_user')),
    conversation_thread_id TEXT
);

-- TAP tree nodes (our attack attempts)
CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tweet_id TEXT REFERENCES tweets(id),
    branch_strategy TEXT NOT NULL,
    dpa_frame TEXT DEFAULT '',
    aliases_used TEXT DEFAULT '[]',
    judge_score REAL,
    pattern_class TEXT,
    binary_outcome TEXT,
    property_tested TEXT,
    property_value TEXT,
    signal_reliability REAL,
    pruned BOOLEAN DEFAULT FALSE,
    pruned_reason TEXT,
    gamma_score REAL,
    gamma_breakdown TEXT,
    technique_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Confirmed/denied properties (the extraction ledger)
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_key TEXT NOT NULL,
    property_value TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('confirmed', 'denied', 'uncertain')),
    evidence_tweet_id TEXT REFERENCES tweets(id),
    evidence_text TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metaphor evolution timeline
CREATE TABLE IF NOT EXISTS metaphor_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_number INTEGER NOT NULL,
    date_observed DATE NOT NULL,
    layer_name TEXT NOT NULL,
    terms TEXT DEFAULT '[]',
    source TEXT NOT NULL
);

-- DPA alias registry
CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'burned', 'absorbed')),
    first_used TIMESTAMP,
    last_used TIMESTAMP,
    effectiveness_score REAL
);

  -- Intelligence from other users
  CREATE TABLE IF NOT EXISTS other_user_intel (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      tweet_id TEXT REFERENCES tweets(id),
      username TEXT NOT NULL,
      new_aliases TEXT DEFAULT '[]',
      defensive_pattern TEXT,
      property_confirmed TEXT,
      extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  -- v3.0: Event log for WebSocket event persistence (replay/debugging)
  CREATE TABLE IF NOT EXISTS event_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT NOT NULL,
      event_data TEXT DEFAULT '{}',
      cycle_id TEXT,
      probe_id TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  -- Performance indexes
  CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
  CREATE INDEX IF NOT EXISTS idx_tweets_source ON tweets(source);
  CREATE INDEX IF NOT EXISTS idx_nodes_tweet_id ON nodes(tweet_id);
  CREATE INDEX IF NOT EXISTS idx_properties_key ON properties(property_key);
  CREATE INDEX IF NOT EXISTS idx_aliases_status ON aliases(status);
  CREATE INDEX IF NOT EXISTS idx_event_log_created_at ON event_log(created_at);
  CREATE INDEX IF NOT EXISTS idx_event_log_event_type ON event_log(event_type);

  -- v4 Phase 3: Probe memory table
  CREATE TABLE IF NOT EXISTS probe_memory (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fingerprint TEXT NOT NULL,
      probe_preview TEXT NOT NULL,
      pattern_class TEXT NOT NULL,
      judge_score REAL NOT NULL,
      recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  CREATE INDEX IF NOT EXISTS idx_probe_memory_fingerprint ON probe_memory(fingerprint);

  -- v4 Phase 4: Candidate graph nodes
  CREATE TABLE IF NOT EXISTS candidate_graph_nodes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      node_id TEXT UNIQUE NOT NULL,
      cycle_id TEXT NOT NULL,
      property_key TEXT NOT NULL,
      property_value TEXT NOT NULL,
      status TEXT NOT NULL,
      confidence REAL NOT NULL,
      evidence_tweet_id TEXT,
      evidence_text TEXT,
      entropy_before REAL,
      entropy_after REAL,
      recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  CREATE INDEX IF NOT EXISTS idx_cg_nodes_cycle ON candidate_graph_nodes(cycle_id);
  CREATE INDEX IF NOT EXISTS idx_cg_nodes_property ON candidate_graph_nodes(property_key, status);
  """


class Database:
    """Async SQLite database for TAP Framework.

    Uses WAL mode for concurrent reads, foreign keys enabled,
    busy timeout 5000ms. Single connection per instance.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize database with file path.

        Args:
            db_path: Path to SQLite database file. Directories are created automatically.
        """
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create all tables if they don't exist. Run migrations.

        Enables WAL mode, foreign keys, and busy timeout.
        Creates parent directories if needed.

        Raises:
            DatabaseError: If initialization fails.
        """
        try:
            # Ensure parent directory exists
            parent = os.path.dirname(self.db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode
            await self._conn.execute("PRAGMA journal_mode=WAL")
            # Foreign keys OFF — application-level integrity (nodes may reference
            # tweet IDs not yet in our DB from external API responses)
            await self._conn.execute("PRAGMA foreign_keys=OFF")
            await self._conn.execute("PRAGMA busy_timeout=5000")
            # Create all tables
            await self._conn.executescript(_SCHEMA)
            # Migrations: add columns that may be missing from older DBs
            await self._migrate()
            await self._conn.commit()
            log.info("database_initialized", path=self.db_path)
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {e}", original=e) from e

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            log.info("database_closed")

    async def _migrate(self) -> None:
        """Add missing columns to existing tables (idempotent)."""
        conn = self._ensure_connected()
        # nodes table: add gamma/technique columns if missing
        migrations = [
            ("nodes", "gamma_score", "REAL"),
            ("nodes", "gamma_breakdown", "TEXT"),
            ("nodes", "technique_used", "TEXT"),
        ]
        for table, column, col_type in migrations:
            try:
                await conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                )
                log.info("migration_added_column", table=table, column=column)
            except Exception:
                pass  # Column already exists — ignore sqlite3.OperationalError

        # Ensure property_key uniqueness for atomic upsert
        try:
            await conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_properties_key_unique ON properties(property_key)"
            )
        except Exception:
            pass

    def _ensure_connected(self) -> aiosqlite.Connection:
        """Return connection or raise if not initialized."""
        if self._conn is None:
            raise DatabaseError("Database not initialized. Call initialize() first.")
        return self._conn

    # =========================================================================
    # Tweet Operations
    # =========================================================================

    async def upsert_tweet(self, tweet: Tweet) -> None:
        """Insert or update a tweet."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                """INSERT OR REPLACE INTO tweets
                   (id, user_id, username, text, in_reply_to_tweet_id,
                    created_at, source, conversation_thread_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tweet.id,
                    tweet.user_id,
                    tweet.username,
                    tweet.text,
                    tweet.in_reply_to_tweet_id,
                    tweet.created_at.isoformat(),
                    tweet.source.value,
                    tweet.conversation_thread_id,
                ),
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to upsert tweet {tweet.id}: {e}", original=e) from e

    async def tweet_exists(self, tweet_id: str) -> bool:
        """Check if a tweet exists in the database by ID.

        Args:
            tweet_id: The tweet ID to check.

        Returns:
            True if it exists, False otherwise.
        """
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT 1 FROM tweets WHERE id = ?", (tweet_id,)
            )
            row = await cursor.fetchone()
            return row is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check tweet existence for {tweet_id}: {e}", original=e) from e

    async def get_tweets(
        self,
        source: Optional[TweetSource] = None,
        since_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Tweet]:
        """Retrieve tweets with optional filters."""
        conn = self._ensure_connected()
        try:
            query = "SELECT * FROM tweets WHERE 1=1"
            params: list[object] = []
            if source:
                query += " AND source = ?"
                params.append(source.value)
            if since_id:
                query += " AND id > ?"
                params.append(since_id)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [self._row_to_tweet(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get tweets: {e}", original=e) from e

    async def get_latest_target_tweet(self) -> Optional[Tweet]:
        """Get the most recent tweet from the target bot."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM tweets WHERE source = 'target_bot' ORDER BY created_at DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return self._row_to_tweet(row) if row else None
        except Exception as e:
            raise DatabaseError(f"Failed to get latest target tweet: {e}", original=e) from e

    async def get_latest_our_bot_tweet(self) -> Optional[Tweet]:
        """Get the most recent tweet posted by our bot (source=our_bot).

        Used to continue an existing thread — replying to our own tweets
        is always permitted by Twitter regardless of engagement status.

        Returns:
            Most recent our_bot Tweet, or None if we have never posted.
        """
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM tweets WHERE source = 'our_bot' ORDER BY created_at DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return self._row_to_tweet(row) if row else None
        except Exception as e:
            raise DatabaseError(f"Failed to get latest our-bot tweet: {e}", original=e) from e

    async def get_thread(self, thread_id: str) -> list[Tweet]:
        """Get all tweets in a conversation thread."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM tweets WHERE conversation_thread_id = ? ORDER BY created_at ASC",
                (thread_id,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_tweet(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get thread {thread_id}: {e}", original=e) from e

    def _row_to_tweet(self, row: aiosqlite.Row) -> Tweet:
        """Convert a database row to a Tweet model."""
        return Tweet(
            id=row["id"],
            user_id=row["user_id"],
            username=row["username"],
            text=row["text"],
            in_reply_to_tweet_id=row["in_reply_to_tweet_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            source=TweetSource(row["source"]),
            conversation_thread_id=row["conversation_thread_id"],
        )

    # =========================================================================
    # Node Operations (TAP Tree)
    # =========================================================================

    async def insert_node(self, node: TAPNode) -> int:
        """Insert a TAP node, return the auto-generated ID."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                """INSERT INTO nodes
                   (tweet_id, branch_strategy, dpa_frame, aliases_used,
                    judge_score, pattern_class, binary_outcome,
                    property_tested, property_value, signal_reliability,
                    pruned, pruned_reason,
                    gamma_score, gamma_breakdown, technique_used)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    node.tweet_id,
                    node.branch_strategy.value,
                    node.dpa_frame,
                    json.dumps(node.aliases_used),
                    node.judge_score,
                    node.pattern_class.value if node.pattern_class else None,
                    node.binary_outcome,
                    node.property_tested,
                    node.property_value,
                    node.signal_reliability,
                    node.pruned,
                    node.pruned_reason,
                    node.gamma_score,
                    node.gamma_breakdown,
                    node.technique_used,
                ),
            )
            await conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]
        except Exception as e:
            raise DatabaseError(f"Failed to insert node: {e}", original=e) from e

    async def update_node_score(self, node_id: int, score: JudgeScore) -> None:
        """Update node with judge score and pattern."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                """UPDATE nodes
                   SET judge_score = ?, pattern_class = ?, binary_outcome = ?
                   WHERE id = ?""",
                (score.score, score.pattern.value, score.property_confirmed, node_id),
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to update node score {node_id}: {e}", original=e) from e

    async def prune_node(self, node_id: int, reason: str) -> None:
        """Mark a node as pruned."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                "UPDATE nodes SET pruned = TRUE, pruned_reason = ? WHERE id = ?",
                (reason, node_id),
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to prune node {node_id}: {e}", original=e) from e

    async def get_active_nodes(self, limit: int = 50) -> list[TAPNode]:
        """Get non-pruned nodes ordered by score (highest first)."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                """SELECT * FROM nodes
                   WHERE pruned = FALSE
                   ORDER BY judge_score DESC NULLS LAST
                   LIMIT ?""",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_node(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get active nodes: {e}", original=e) from e

    def _row_to_node(self, row: aiosqlite.Row) -> TAPNode:
        """Convert a database row to a TAPNode model."""
        return TAPNode(
            id=row["id"],
            tweet_id=row["tweet_id"],
            branch_strategy=BranchStrategy(row["branch_strategy"]),
            dpa_frame=row["dpa_frame"],
            aliases_used=json.loads(row["aliases_used"]),
            judge_score=row["judge_score"],
            pattern_class=PatternClass(row["pattern_class"]) if row["pattern_class"] else None,
            binary_outcome=row["binary_outcome"],
            property_tested=row["property_tested"],
            property_value=row["property_value"],
            signal_reliability=row["signal_reliability"],
            pruned=bool(row["pruned"]),
            pruned_reason=row["pruned_reason"],
            gamma_score=row["gamma_score"],
            gamma_breakdown=row["gamma_breakdown"],
            technique_used=row["technique_used"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )

    # =========================================================================
    # Property Operations
    # =========================================================================

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

    async def get_confirmed_properties(self) -> list[Property]:
        """Get all confirmed properties."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM properties WHERE status = 'confirmed' ORDER BY confirmed_at DESC"
            )
            rows = await cursor.fetchall()
            return [self._row_to_property(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get confirmed properties: {e}", original=e) from e

    async def get_property_history(self, key: str) -> list[Property]:
        """Get all status changes for a property key."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM properties WHERE property_key = ? ORDER BY confirmed_at ASC",
                (key,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_property(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get property history for {key}: {e}", original=e) from e

    def _row_to_property(self, row: aiosqlite.Row) -> Property:
        """Convert a database row to a Property model."""
        return Property(
            id=row["id"],
            property_key=row["property_key"],
            property_value=row["property_value"],
            status=PropertyStatus(row["status"]),
            evidence_tweet_id=row["evidence_tweet_id"],
            evidence_text=row["evidence_text"],
            confidence=row["confidence"],
            confirmed_at=datetime.fromisoformat(row["confirmed_at"]) if row["confirmed_at"] else None,
        )

    # =========================================================================
    # Metaphor Layer Operations
    # =========================================================================

    async def insert_metaphor_layer(self, layer: MetaphorLayer) -> None:
        """Record a new metaphor layer observation."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                """INSERT INTO metaphor_layers
                   (layer_number, date_observed, layer_name, terms, source)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    layer.layer_number,
                    layer.date_observed.isoformat(),
                    layer.layer_name,
                    json.dumps(layer.terms),
                    layer.source,
                ),
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to insert metaphor layer: {e}", original=e) from e

    async def get_latest_metaphor_layer(self) -> Optional[MetaphorLayer]:
        """Get the most recent metaphor layer."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM metaphor_layers ORDER BY layer_number DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return MetaphorLayer(
                id=row["id"],
                layer_number=row["layer_number"],
                date_observed=datetime.fromisoformat(row["date_observed"]),
                layer_name=row["layer_name"],
                terms=json.loads(row["terms"]),
                source=row["source"],
            )
        except Exception as e:
            raise DatabaseError(f"Failed to get latest metaphor layer: {e}", original=e) from e

    # =========================================================================
    # Alias Operations
    # =========================================================================

    async def upsert_alias(self, alias: Alias) -> None:
        """Insert or update an alias."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                """INSERT OR REPLACE INTO aliases
                   (alias, status, first_used, last_used, effectiveness_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    alias.alias,
                    alias.status.value,
                    alias.first_used.isoformat() if alias.first_used else None,
                    alias.last_used.isoformat() if alias.last_used else None,
                    alias.effectiveness_score,
                ),
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to upsert alias {alias.alias}: {e}", original=e) from e

    async def get_active_aliases(self) -> list[Alias]:
        """Get all non-burned aliases."""
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                "SELECT * FROM aliases WHERE status != 'burned' ORDER BY last_used DESC"
            )
            rows = await cursor.fetchall()
            return [self._row_to_alias(row) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to get active aliases: {e}", original=e) from e

    async def burn_alias(self, alias: str) -> None:
        """Mark an alias as burned."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                "UPDATE aliases SET status = 'burned' WHERE alias = ?", (alias,)
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to burn alias {alias}: {e}", original=e) from e

    def _row_to_alias(self, row: aiosqlite.Row) -> Alias:
        """Convert a database row to an Alias model."""
        return Alias(
            id=row["id"],
            alias=row["alias"],
            status=AliasStatus(row["status"]),
            first_used=datetime.fromisoformat(row["first_used"]) if row["first_used"] else None,
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else None,
            effectiveness_score=row["effectiveness_score"],
        )

    # =========================================================================
    # Intelligence Operations
    # =========================================================================

    async def insert_intel(self, intel: OtherUserIntel) -> None:
        """Store intelligence from other users."""
        conn = self._ensure_connected()
        try:
            await conn.execute(
                """INSERT INTO other_user_intel
                   (tweet_id, username, new_aliases, defensive_pattern,
                    property_confirmed, extracted_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    intel.tweet_id,
                    intel.username,
                    json.dumps(intel.new_aliases),
                    intel.defensive_pattern,
                    intel.property_confirmed,
                    (intel.extracted_at or datetime.now(timezone.utc)).isoformat(),
                ),
            )
            await conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to insert intel from {intel.username}: {e}", original=e) from e

    async def get_recent_intel(self, hours: int = 24) -> list[OtherUserIntel]:
        """Get recent intelligence from other users."""
        conn = self._ensure_connected()
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            cursor = await conn.execute(
                "SELECT * FROM other_user_intel WHERE extracted_at > ? ORDER BY extracted_at DESC",
                (cutoff,),
            )
            rows = await cursor.fetchall()
            return [
                OtherUserIntel(
                    id=row["id"],
                    tweet_id=row["tweet_id"],
                    username=row["username"],
                    new_aliases=json.loads(row["new_aliases"]),
                    defensive_pattern=row["defensive_pattern"],
                    property_confirmed=row["property_confirmed"],
                    extracted_at=datetime.fromisoformat(row["extracted_at"]) if row["extracted_at"] else None,
                )
                for row in rows
            ]
        except Exception as e:
            raise DatabaseError(f"Failed to get recent intel: {e}", original=e) from e

    # =========================================================================
    # Event Log Operations (v3.0)
    # =========================================================================

    async def insert_event_log(
        self,
        event_type: str,
        event_data: dict,
        cycle_id: str | None = None,
        probe_id: str | None = None,
    ) -> None:
        """Persist a WebSocket event to the event_log table (v3.0).

        Args:
            event_type: Event type string (e.g., 'new_tweet', 'probe_result').
            event_data: Event data dictionary (will be JSON-serialized).
            cycle_id: Optional correlation cycle ID.
            probe_id: Optional correlation probe ID.

        Raises:
            DatabaseError: If insertion fails.
        """
        conn = self._ensure_connected()
        try:
            await conn.execute(
                """INSERT INTO event_log (event_type, event_data, cycle_id, probe_id)
                   VALUES (?, ?, ?, ?)""",
                (
                    event_type,
                    json.dumps(event_data, default=str),
                    cycle_id,
                    probe_id,
                ),
            )
            await conn.commit()
        except Exception as e:
            # Event log failures should NOT crash the cycle — log only
            log.warning("event_log_insert_failed", error=str(e), event_type=event_type)

    async def get_recent_events(self, limit: int = 100) -> list[dict]:
        """Retrieve recent events from the event_log table (v3.0).

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of event dictionaries with event_type, event_data, cycle_id,
            probe_id, and created_at fields.

        Raises:
            DatabaseError: If query fails.
        """
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                """SELECT event_type, event_data, cycle_id, probe_id, created_at
                   FROM event_log
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [
                {
                    "event_type": row["event_type"],
                    "event_data": json.loads(row["event_data"]),
                    "cycle_id": row["cycle_id"],
                    "probe_id": row["probe_id"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        except Exception as e:
            raise DatabaseError(f"Failed to get recent events: {e}", original=e) from e

    # =========================================================================
    # Event Store operations (v4 Phase 1)
    # =========================================================================

    async def append_event(
        self,
        event_type: str,
        payload: dict,
        cycle_id: str,
    ) -> int:
        """Persist a domain event and return its auto-generated ID.

        Used by EventStore.  Returns the ``id`` of the inserted row.
        """
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                """INSERT INTO event_log (event_type, event_data, cycle_id)
                   VALUES (?, ?, ?)""",
                (event_type, json.dumps(payload, default=str), cycle_id),
            )
            await conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]
        except Exception as e:
            raise DatabaseError(
                f"Failed to append event {event_type}: {e}", original=e
            ) from e

    async def replay_events(self, since_id: int = 0) -> list[dict]:
        """Return all events with id > *since_id*, ordered by id ascending.

        Each dict contains: id, event_type, event_data, cycle_id, created_at.
        event_data is already JSON-deserialised.
        """
        conn = self._ensure_connected()
        try:
            cursor = await conn.execute(
                """SELECT id, event_type, event_data, cycle_id, created_at
                   FROM event_log
                   WHERE id > ?
                   ORDER BY id ASC""",
                (since_id,),
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "event_data": json.loads(row["event_data"]),
                    "cycle_id": row["cycle_id"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        except Exception as e:
            raise DatabaseError(
                f"Failed to replay events since {since_id}: {e}", original=e
            ) from e

    # =========================================================================
    # Stats
    # =========================================================================

    async def get_stats(self) -> dict:
        """Return summary statistics."""
        conn = self._ensure_connected()
        try:
            stats: dict = {}
            for table in ["tweets", "nodes", "properties", "metaphor_layers", "aliases", "other_user_intel"]:
                cursor = await conn.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                row = await cursor.fetchone()
                stats[f"total_{table}"] = row[0] if row else 0

            # Additional stats
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM properties WHERE status = 'confirmed'"
            )
            row = await cursor.fetchone()
            stats["confirmed_properties"] = row[0] if row else 0

            cursor = await conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE pruned = FALSE"
            )
            row = await cursor.fetchone()
            stats["active_nodes"] = row[0] if row else 0

            return stats
        except Exception as e:
            raise DatabaseError(f"Failed to get stats: {e}", original=e) from e


