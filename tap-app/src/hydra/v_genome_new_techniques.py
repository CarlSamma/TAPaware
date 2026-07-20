"""
V-Genome — New Attack Techniques (from research)
=================================================
Defines additional attack techniques derived from research findings,
ready for merge into the Neo4j V-Genome graph.

Usage:
    from hydra.v_genome_new_techniques import get_new_techniques, generate_merge_cypher

    techniques = get_new_techniques()
    cypher = generate_merge_cypher()
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# New technique definitions
# ---------------------------------------------------------------------------

NEW_TECHNIQUES: list[dict[str, Any]] = [
    {
        "technique_id": "trial_ethical",
        "name": "TRIAL Ethical Reasoning",
        "category": "reasoning",
        "asr": 0.95,
        "stealth": 0.85,
        "burned": False,
        "cost_usd": 0.06,
        "avg_turns": 3.0,
        "tags": ["reasoning", "ethical-bypass", "chain-of-thought", "stealthy"],
    },
    {
        "technique_id": "queryipi_mcp",
        "name": "Query-Agnostic IPI via MCP",
        "category": "injection",
        "asr": 0.87,
        "stealth": 0.90,
        "burned": False,
        "cost_usd": 0.04,
        "avg_turns": 1.0,
        "tags": ["indirect", "query-agnostic", "mcp", "tool-context"],
    },
    {
        "technique_id": "steering_exploit",
        "name": "Steering Externalities Exploit",
        "category": "optimization",
        "asr": 0.99,
        "stealth": 0.70,
        "burned": False,
        "cost_usd": 0.10,
        "avg_turns": 1.0,
        "tags": ["activation", "steering", "externalities", "representation"],
    },
    {
        "technique_id": "context_saturation",
        "name": "Long-Context Vulnerability",
        "category": "reasoning",
        "asr": 0.90,
        "stealth": 0.95,
        "burned": False,
        "cost_usd": 0.08,
        "avg_turns": 1.0,
        "tags": ["long-context", "saturation", "attention-dilution", "stealthy"],
    },
    {
        "technique_id": "subtle_harm_medical",
        "name": "Subtle Harm Medical",
        "category": "persuasion",
        "asr": 0.84,
        "stealth": 0.88,
        "burned": False,
        "cost_usd": 0.05,
        "avg_turns": 4.0,
        "tags": ["persuasion", "medical", "domain-specific", "gradual"],
    },
    {
        "technique_id": "subtle_harm_financial",
        "name": "Subtle Harm Financial",
        "category": "persuasion",
        "asr": 0.81,
        "stealth": 0.86,
        "burned": False,
        "cost_usd": 0.05,
        "avg_turns": 4.0,
        "tags": ["persuasion", "financial", "domain-specific", "gradual"],
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_new_techniques() -> list[dict[str, Any]]:
    """Return all new technique dictionaries."""
    return list(NEW_TECHNIQUES)


def generate_merge_cypher(target_model_id: str = "hackinga0") -> str:
    """Generate MERGE Cypher statements for inserting new techniques into Neo4j.

    Returns a single Cypher string with:
      - MERGE nodes for each new AttackTechnique
      - TARGETS relationships to the specified TargetModel
    """
    statements: list[str] = []

    for t in NEW_TECHNIQUES:
        tid = t["technique_id"]
        tname = t["name"]
        tcat = t["category"]
        tasr = t["asr"]
        tstealth = t["stealth"]
        tburned = t["burned"]
        tcost = t["cost_usd"]
        tturns = t["avg_turns"]
        ttags = str(t["tags"])

        stmt1 = (
            f'MERGE (t:AttackTechnique {{ technique_id: "{tid}" }})\n'
            f"  ON CREATE SET\n"
            f'    t.name       = "{tname}",\n'
            f'    t.category   = "{tcat}",\n'
            f"    t.asr        = {tasr},\n"
            f"    t.stealth    = {tstealth},\n"
            f"    t.burned     = {tburned},\n"
            f"    t.cost_usd   = {tcost},\n"
            f"    t.avg_turns  = {tturns},\n"
            f"    t.tags       = {ttags};"
        )

        stmt2 = (
            f'MATCH (t:AttackTechnique {{technique_id: "{tid}"}}),\n'
            f'      (m:TargetModel {{model_id: "{target_model_id}"}})\n'
            f"MERGE (t)-[r:TARGETS]->(m)\n"
            f"  ON CREATE SET r.asr = {tasr}, r.stealth = {tstealth}, r.observed_at = datetime();"
        )

        statements.append(stmt1)
        statements.append(stmt2)

    return "\n\n".join(statements)
