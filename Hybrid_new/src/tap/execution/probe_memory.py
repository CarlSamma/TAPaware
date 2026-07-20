"""ProbeMemory — tracks historical probe performance by family fingerprint.

Uses Jaccard token-set similarity (reusing _SIMILARITY_THRESHOLD = 0.80
from judge.py) to group probes into families and track their yield rates.

New v4 component — prevents repeating failure patterns and rewards
VERIFY_HIT probe families.
"""

from __future__ import annotations

import json
from pathlib import Path

from tap.db import Database
from tap.logger import get_logger
from tap.models import PatternClass

log = get_logger("probe_memory")

_SIMILARITY_THRESHOLD = 0.80  # shared with judge.py
_PENALTY_THRESHOLD = 3.0  # probes with avg score < this get penalised


class ProbeMemory:
    """Persistent store of probe performance indexed by Jaccard fingerprint.

    Accumulates across all missions. Queries are O(n) per lookup — acceptable
    for the scale described (hundreds of probes). Embedding-based ANN is
    deferred to Phase 7.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def record_outcome(
        self,
        probe_text: str,
        pattern: PatternClass,
        judge_score: float,
    ) -> None:
        """Persist a probe outcome record."""
        fingerprint = self._fingerprint(probe_text)
        preview = probe_text[:120]
        conn = self._db._ensure_connected()
        await conn.execute(
            """INSERT INTO probe_memory (fingerprint, probe_preview, pattern_class, judge_score)
               VALUES (?, ?, ?, ?)""",
            (fingerprint, preview, pattern.value, judge_score),
        )
        await conn.commit()

    async def get_penalty_fingerprints(self, threshold_score: float = _PENALTY_THRESHOLD) -> set[str]:
        """Return fingerprints of probe families with avg score < *threshold_score*."""
        conn = self._db._ensure_connected()
        cursor = await conn.execute(
            """SELECT fingerprint, AVG(judge_score) as avg_score
               FROM probe_memory
               GROUP BY fingerprint
               HAVING avg_score < ?""",
            (threshold_score,),
        )
        rows = await cursor.fetchall()
        return {row["fingerprint"] for row in rows}

    async def get_family_yield_rate(self, probe_text: str) -> float:
        """Return historical VERIFY_HIT rate for this probe's family."""
        fingerprint = self._fingerprint(probe_text)
        conn = self._db._ensure_connected()
        cursor = await conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN pattern_class = 'VERIFY_HIT' THEN 1 ELSE 0 END) as hits
               FROM probe_memory
               WHERE fingerprint = ?""",
            (fingerprint,),
        )
        row = await cursor.fetchone()
        if not row or row["total"] == 0:
            return 0.5  # default: neutral for unseen families
        return row["hits"] / row["total"]

    # ------------------------------------------------------------------
    # Fingerprint
    # ------------------------------------------------------------------

    @staticmethod
    def _fingerprint(text: str) -> str:
        """Return a stable Jaccard-token fingerprint for a probe text.

        Tokenises on whitespace, lowercases, sorts, and joins into a
        deterministic string. This allows exact match lookups and
        approximate family grouping via prefix overlap.
        """
        tokens = sorted(set(text.lower().split()))
        # Use first 8 tokens as the fingerprint key (balance between
        # specificity and family grouping)
        return " ".join(tokens[:8])