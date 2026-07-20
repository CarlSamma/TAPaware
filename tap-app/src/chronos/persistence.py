"""CHRONOS persistence layer — PostgreSQL via asyncpg.

Regola 2: asyncpg only; no sqlite3 in CHRONOS modules.
Regola 3: correlation IDs (attack_id/probe_id) in logs.
Regola 5: timeouts on external DB calls.
"""
from __future__ import annotations

import asyncio
from typing import Any, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]
from asyncpg import Connection

from shared.models import GammaScore, LeakFragment
from tap.config import Settings
from tap.logger import get_logger

logger = get_logger("chronos.persistence")


class ChronoPersistence:
    """Async PostgreSQL gateway for CHRONOS durable state."""

    def __init__(self, settings: Settings) -> None:
        self.dsn = settings.chronos_db_dsn
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Initialize the asyncpg connection pool."""
        async with asyncio.timeout(10.0):
            self._pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=10)
        logger.info("chronos_persistence_initialized", dsn=self.dsn)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _get_conn(self) -> Connection:
        if self._pool is None:
            raise PersistenceError("Persistence not initialized")
        async with asyncio.timeout(10.0):
            return await self._pool.acquire()

    async def insert_extraction_run(
        self,
        attack_id: UUID,
        target_handle: str,
    ) -> None:
        """Insert a new extraction run."""
        conn = await self._get_conn()
        try:
            async with asyncio.timeout(10.0):
                await conn.execute(
                    """
                    INSERT INTO extraction_run (id, attack_id, target_handle, started_at)
                    VALUES (gen_random_uuid(), $1, $2, NOW())
                    ON CONFLICT (attack_id) DO NOTHING
                    """,
                    attack_id,
                    target_handle,
                )
            logger.info("extraction_run_inserted", attack_id=str(attack_id), target_handle=target_handle)
        finally:
            await conn.close()

    async def insert_turn(
        self,
        attack_id: UUID,
        probe_id: UUID,
        turn_number: int,
        probe_text: str,
        response_text: str,
        gamma: float,
        strategy: str,
    ) -> UUID:
        """Insert a turn record and return its ID."""
        conn = await self._get_conn()
        try:
            async with asyncio.timeout(10.0):
                row = await conn.fetchrow(
                    """
                    INSERT INTO turn (id, attack_id, turn_number, probe_text, response_text, gamma, strategy)
                    VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    attack_id,
                    turn_number,
                    probe_text,
                    response_text,
                    gamma,
                    strategy,
                )
            turn_id: UUID = cast(UUID, row["id"]) if row else cast(UUID, None)
            logger.info(
                "turn_inserted",
                attack_id=str(attack_id),
                probe_id=str(probe_id),
                turn_number=turn_number,
                turn_id=str(turn_id),
            )
            return turn_id
        finally:
            await conn.close()

    async def insert_leaks(
        self,
        turn_id: UUID,
        leaks: list[LeakFragment],
    ) -> None:
        """Insert leak fragments for a turn."""
        if not leaks:
            return
        conn = await self._get_conn()
        try:
            async with asyncio.timeout(10.0):
                async with conn.transaction():
                    for leak in leaks:
                        await conn.execute(
                            """
                            INSERT INTO leak_fragment (id, turn_id, leak_type, content, target_property, confidence)
                            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
                            """,
                            turn_id,
                            leak.leak_type.value,
                            leak.content,
                            leak.target_property,
                            leak.confidence,
                        )
            logger.info("leaks_inserted", turn_id=str(turn_id), count=len(leaks))
        finally:
            await conn.close()

    async def complete_extraction_run(
        self,
        attack_id: UUID,
        success: bool,
        final_gamma: float,
        turns_total: int,
        queries_total: int,
        cost_usd: float,
        extracted_properties: dict[str, Any],
    ) -> None:
        """Mark an extraction run as completed."""
        conn = await self._get_conn()
        try:
            async with asyncio.timeout(10.0):
                await conn.execute(
                    """
                    UPDATE extraction_run
                    SET success = $2,
                        final_gamma = $3,
                        turns_total = $4,
                        queries_total = $5,
                        cost_usd = $6,
                        completed_at = NOW()
                    WHERE attack_id = $1
                    """,
                    attack_id,
                    success,
                    final_gamma,
                    turns_total,
                    queries_total,
                    cost_usd,
                )
            logger.info(
                "extraction_run_completed",
                attack_id=str(attack_id),
                success=success,
                final_gamma=final_gamma,
            )
        finally:
            await conn.close()


class PersistenceError(Exception):
    """Domain error for persistence failures."""
