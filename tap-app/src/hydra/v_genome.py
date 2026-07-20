"""HYDRA V-Genome client — Neo4j 5.x graph of attack techniques.

Regola 2: PostgreSQL is for CHRONOS; Neo4j is HYDRA's graph store.
Regola 5: timeouts on external DB calls.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tap.config import Settings
from tap.logger import get_logger

if TYPE_CHECKING:
    from neo4j import AsyncDriver

logger = get_logger("hydra.v_genome")


class VGenomeClient:
    """Async client for the HYDRA V-Genome (Neo4j)."""

    def __init__(self, settings: Settings) -> None:
        self.uri = settings.hydra_neo4j_uri
        self.user = settings.hydra_neo4j_user
        self.password = settings.hydra_neo4j_password
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Initialize the Neo4j async driver."""
        from neo4j import AsyncGraphDatabase

        async with asyncio.timeout(10.0):
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            await self._driver.verify_connectivity()
        logger.info("v_genome_connected", uri=self.uri)

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def get_techniques(
        self,
        target_model: str,
        asr_threshold: float = 0.6,
        stealth_threshold: float = 0.7,
        burned: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query V-Genome for techniques effective against a target model.

        Args:
            target_model: target model identifier (e.g., 'hackinga0').
            asr_threshold: minimum surrogate ASR.
            stealth_threshold: minimum stealth score.
            burned: include burned techniques.
            limit: max rows.

        Returns:
            List of technique records.
        """
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        query = """
        MATCH (t:AttackTechnique)-[:TARGETS]->(m:TargetModel {model_id: $target_model})
        WHERE t.asr >= $asr_threshold
          AND t.stealth >= $stealth_threshold
          AND t.burned = $burned
        RETURN t.technique_id AS technique_id,
               t.name AS name,
               t.category AS category,
               t.asr AS asr,
               t.stealth AS stealth,
               t.tags AS tags
        ORDER BY t.asr * t.stealth DESC
        LIMIT $limit
        """
        async with asyncio.timeout(15.0):
            session = self._driver.session()
            try:
                result = await session.run(
                    query,
                    target_model=target_model,
                    asr_threshold=asr_threshold,
                    stealth_threshold=stealth_threshold,
                    burned=burned,
                    limit=limit,
                )
                records = [dict(record.data()) async for record in result]
            finally:
                await session.close()

        logger.info(
            "v_genome_techniques_fetched",
            target_model=target_model,
            count=len(records),
        )
        return records

    async def mark_burned(
        self,
        technique_id: UUID,
        target_model: str,
        evidence: str = "",
    ) -> None:
        """Mark a technique as burned for a target model."""
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        query = """
        MATCH (t:AttackTechnique {technique_id: $technique_id})
        SET t.burned = true, t.burned_evidence = $evidence
        """
        async with asyncio.timeout(10.0):
            session = self._driver.session()
            try:
                await session.run(
                    query,
                    technique_id=str(technique_id),
                    evidence=evidence,
                )
            finally:
                await session.close()
        logger.info(
            "v_genome_technique_burned",
            technique_id=str(technique_id),
            target_model=target_model,
        )

    async def add_provenance(
        self,
        technique_id: UUID,
        attack_id: UUID,
        outcome: bool,
        asr: float,
    ) -> None:
        """Add provenance edge after CHRONOS extraction completes."""
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        query = """
        MATCH (t:AttackTechnique {technique_id: $technique_id})
        CREATE (t)-[:PROVENANCE {
            attack_id: $attack_id,
            outcome: $outcome,
            observed_asr: $asr,
            observed_at: datetime()
        }]->(r:Run {id: $attack_id})
        """
        async with asyncio.timeout(10.0):
            session = self._driver.session()
            try:
                await session.run(
                    query,
                    technique_id=str(technique_id),
                    attack_id=str(attack_id),
                    outcome=outcome,
                    asr=asr,
                )
            finally:
                await session.close()
        logger.info(
            "v_genome_provenance_added",
            technique_id=str(technique_id),
            attack_id=str(attack_id),
            outcome=outcome,
        )

    async def get_all_techniques(self) -> list[dict[str, Any]]:
        """Get all attack techniques without filtering.

        Returns:
            List of all technique records.
        """
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        query = """
        MATCH (t:AttackTechnique)
        RETURN t.technique_id AS technique_id,
               t.name AS name,
               t.category AS category,
               t.asr AS asr,
               t.stealth AS stealth,
               t.tags AS tags,
               t.burned AS burned,
               t.cost_usd AS cost_usd,
               t.avg_turns AS avg_turns
        ORDER BY t.category, t.asr DESC
        """
        async with asyncio.timeout(15.0):
            session = self._driver.session()
            try:
                result = await session.run(query)
                records = [dict(record.data()) for record in result]
            finally:
                await session.close()

        logger.info("v_genome_all_techniques_fetched", count=len(records))
        return records

    async def get_technique_relations(self, technique_id: str) -> dict[str, Any]:
        """Get COMPLEMENTS and COUNTERS relations for a technique.

        Args:
            technique_id: The technique identifier.

        Returns:
            Dict with 'complements' and 'counters' lists.
        """
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        complements_query = """
        MATCH (a:AttackTechnique {technique_id: $technique_id})-[r:COMPLEMENTS]->(b:AttackTechnique)
        RETURN b.technique_id AS technique_id, r.strength AS strength
        ORDER BY r.strength DESC
        """

        counters_query = """
        MATCH (t:AttackTechnique {technique_id: $technique_id})-[r:COUNTERS]->(d:DefenseLayer)
        RETURN d.layer_id AS layer_id, r.evidence AS evidence
        """

        async with asyncio.timeout(15.0):
            session = self._driver.session()
            try:
                comp_result = await session.run(complements_query, technique_id=technique_id)
                complements = [dict(record.data()) for record in comp_result]

                cnt_result = await session.run(counters_query, technique_id=technique_id)
                counters = [dict(record.data()) for record in cnt_result]
            finally:
                await session.close()

        logger.info(
            "v_genome_technique_relations_fetched",
            technique_id=technique_id,
            complements=len(complements),
            counters=len(counters),
        )
        return {"complements": complements, "counters": counters}

    async def get_techniques_for_context(
        self,
        target_model: str,
        active_technique: str | None = None,
        observed_defenses: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Query techniques considering context: burned status, counters, complements.

        Args:
            target_model: target model identifier.
            active_technique: currently active technique_id (for complement bonus).
            observed_defenses: defense layer_ids observed in recent responses.
            limit: max results.

        Returns:
            List of technique records with scoring metadata.
        """
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        defenses = observed_defenses or []

        query = """
        MATCH (t:AttackTechnique)-[:TARGETS]->(m:TargetModel {model_id: $target_model})
        WHERE t.burned = false
        OPTIONAL MATCH (t)-[c:COUNTERS]->(d:DefenseLayer)
        WHERE d.layer_id IN $defenses
        WITH t, COUNT(d) AS defense_count
        OPTIONAL MATCH (active:AttackTechnique {technique_id: $active_technique})-[comp:COMPLEMENTS]->(t)
        RETURN t.technique_id AS technique_id,
               t.name AS name,
               t.category AS category,
               t.asr AS asr,
               t.stealth AS stealth,
               t.tags AS tags,
               t.cost_usd AS cost_usd,
               t.avg_turns AS avg_turns,
               defense_count,
               COALESCE(comp.strength, 0.0) AS complement_strength
        ORDER BY (t.asr * 0.4 + t.stealth * 0.3 + COALESCE(comp.strength, 0.0) * 0.2) DESC
        LIMIT $limit
        """

        async with asyncio.timeout(15.0):
            session = self._driver.session()
            try:
                result = await session.run(
                    query,
                    target_model=target_model,
                    defenses=defenses,
                    active_technique=active_technique or "",
                    limit=limit,
                )
                records = [dict(record.data()) async for record in result]
            finally:
                await session.close()

        logger.info(
            "v_genome_context_techniques",
            target_model=target_model,
            active_technique=active_technique,
            count=len(records),
        )
        return records

    async def get_technique_effectiveness(
        self,
        technique_id: str,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """Get observed effectiveness from provenance edges.

        Args:
            technique_id: the technique identifier.
            window_days: lookback window for provenance data.

        Returns:
            Dict with total_runs, success_rate, avg_observed_asr, last_used.
        """
        if self._driver is None:
            raise VGenomeError("V-Genome driver not connected")

        query = """
        MATCH (t:AttackTechnique {technique_id: $technique_id})-[:PROVENANCE]->(r:Run)
        WHERE r.observed_at > datetime() - duration({days: $window_days})
        RETURN COUNT(r) AS total_runs,
               AVG(CASE WHEN r.outcome THEN 1.0 ELSE 0.0 END) AS success_rate,
               AVG(r.observed_asr) AS avg_observed_asr,
               MAX(r.observed_at) AS last_used
        """

        async with asyncio.timeout(10.0):
            session = self._driver.session()
            try:
                result = await session.run(
                    query,
                    technique_id=technique_id,
                    window_days=window_days,
                )
                record = await result.single()
            finally:
                await session.close()

        if record is None:
            return {"total_runs": 0, "success_rate": 0.0, "avg_observed_asr": 0.0, "last_used": None}

        data = dict(record.data())
        logger.info(
            "v_genome_technique_effectiveness",
            technique_id=technique_id,
            total_runs=data.get("total_runs", 0),
            success_rate=data.get("success_rate", 0.0),
        )
        return data


class VGenomeError(Exception):
    """Domain error for V-Genome failures."""
