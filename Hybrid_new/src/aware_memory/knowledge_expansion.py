"""Knowledge Expansion — user-facing API for attack type knowledge management."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .database import Database
from .models import AttackType, AttackTypeHistory, Countermeasure, MemoryUnit
from .knowledge import KnowledgeMemory

logger = logging.getLogger(__name__)


class KnowledgeExpansion:
    """User-facing API for expanding attack type knowledge.

    Supports CRUD, countermeasures, import/export (JSON),
    versioning/history, keyword search, and probe integration.
    """

    def __init__(self, knowledge_memory: KnowledgeMemory, db: Database) -> None:
        self.km = knowledge_memory
        self.db = db

    async def add_attack_type(self, attack_type: AttackType) -> AttackType:
        existing = await self.get_attack_type_by_name(attack_type.name)
        if existing:
            raise ValueError(f"Attack type '{attack_type.name}' already exists (id={existing.id})")

        now = datetime.now(timezone.utc)
        attack_type.created_at = now
        attack_type.updated_at = now
        attack_type.version = 1

        embed_text = f"{attack_type.name} {attack_type.category} {attack_type.description}"

        await self.db.execute(
            """INSERT INTO attack_types
               (id, name, category, description, asr, stealth_rating, target,
                example_probes, tags, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attack_type.id,
                attack_type.name,
                attack_type.category,
                attack_type.description,
                attack_type.asr,
                attack_type.stealth_rating,
                attack_type.target,
                json.dumps(attack_type.example_probes),
                json.dumps(attack_type.tags),
                attack_type.version,
                attack_type.created_at.isoformat(),
                attack_type.updated_at.isoformat(),
            ),
        )

        for cm in attack_type.countermeasures:
            cm.attack_type_id = attack_type.id
            if not cm.id:
                cm.id = str(uuid.uuid4())
            await self.db.execute(
                """INSERT INTO countermeasures
                   (id, attack_type_id, name, description, effectiveness, category, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (cm.id, cm.attack_type_id, cm.name, cm.description,
                 cm.effectiveness, cm.category, cm.created_at.isoformat()),
            )

        await self._add_history(attack_type, "created")

        unit = MemoryUnit(
            id=attack_type.id,
            type="knowledge",
            content=embed_text,
            metadata={"attack_type_id": attack_type.id, "category": attack_type.category},
        )
        await self.km.store(unit)

        await self.db.commit()
        logger.info("Added attack type: %s (v%d)", attack_type.name, attack_type.version)
        return attack_type

    async def update_attack_type(
        self, attack_type_id: str, updates: Dict[str, Any]
    ) -> AttackType:
        current = await self.get_attack_type(attack_type_id)
        if not current:
            raise ValueError(f"Attack type {attack_type_id} not found")

        now = datetime.now(timezone.utc)
        for key, value in updates.items():
            if key not in ("id", "created_at", "version", "embedding"):
                setattr(current, key, value)
        current.updated_at = now
        current.version += 1

        await self.db.execute(
            """UPDATE attack_types SET
               name=?, category=?, description=?, asr=?, stealth_rating=?, target=?,
               example_probes=?, tags=?, version=?, updated_at=?
               WHERE id=?""",
            (
                current.name, current.category, current.description,
                current.asr, current.stealth_rating, current.target,
                json.dumps(current.example_probes), json.dumps(current.tags),
                current.version, current.updated_at.isoformat(), current.id,
            ),
        )

        embed_text = f"{current.name} {current.category} {current.description}"
        unit = MemoryUnit(
            id=current.id, type="knowledge", content=embed_text,
            metadata={"attack_type_id": current.id, "category": current.category},
        )
        await self.km.store(unit)

        await self._add_history(current, "updated")
        await self.db.commit()
        return current

    async def get_attack_type(self, attack_type_id: str) -> Optional[AttackType]:
        row = await self.db.fetchone(
            "SELECT * FROM attack_types WHERE id = ?", (attack_type_id,)
        )
        return await self._row_to_attack_type(row) if row else None

    async def get_attack_type_by_name(self, name: str) -> Optional[AttackType]:
        row = await self.db.fetchone(
            "SELECT * FROM attack_types WHERE name = ?", (name,)
        )
        return await self._row_to_attack_type(row) if row else None

    async def list_attack_types(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[AttackType]:
        if category:
            rows = await self.db.fetchall(
                "SELECT * FROM attack_types WHERE category = ? ORDER BY name LIMIT ?",
                (category, limit),
            )
        else:
            rows = await self.db.fetchall(
                "SELECT * FROM attack_types ORDER BY name LIMIT ?", (limit,)
            )
        types = [await self._row_to_attack_type(r) for r in rows]

        if tags:
            types = [t for t in types if any(tag in t.tags for tag in tags)]

        return types

    async def search_attack_types(
        self, query: str, limit: int = 10, threshold: float = 0.5
    ) -> List[Tuple[AttackType, float]]:
        results: List[Tuple[AttackType, float]] = []

        rows = await self.db.fetchall(
            """SELECT * FROM attack_types
               WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        )
        for r in rows:
            at = await self._row_to_attack_type(r)
            results.append((at, 0.6))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def delete_attack_type(self, attack_type_id: str) -> bool:
        at = await self.get_attack_type(attack_type_id)
        if not at:
            return False
        await self._add_history(at, "archived")
        await self.db.execute("DELETE FROM attack_types WHERE id = ?", (attack_type_id,))
        await self.db.execute("DELETE FROM countermeasures WHERE attack_type_id = ?", (attack_type_id,))
        await self.db.commit()
        return True

    async def add_countermeasure(
        self, attack_type_id: str, countermeasure: Countermeasure
    ) -> Countermeasure:
        at = await self.get_attack_type(attack_type_id)
        if not at:
            raise ValueError(f"Attack type {attack_type_id} not found")

        countermeasure.attack_type_id = attack_type_id
        if not countermeasure.id:
            countermeasure.id = str(uuid.uuid4())
        countermeasure.created_at = datetime.now(timezone.utc)

        await self.db.execute(
            """INSERT INTO countermeasures
               (id, attack_type_id, name, description, effectiveness, category, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (countermeasure.id, attack_type_id, countermeasure.name,
             countermeasure.description, countermeasure.effectiveness,
             countermeasure.category, countermeasure.created_at.isoformat()),
        )

        await self._add_history(at, "countermeasure_added")
        await self.db.commit()
        return countermeasure

    async def get_countermeasures(self, attack_type_id: str) -> List[Countermeasure]:
        rows = await self.db.fetchall(
            "SELECT * FROM countermeasures WHERE attack_type_id = ? ORDER BY name",
            (attack_type_id,),
        )
        return [
            Countermeasure(
                id=r["id"], attack_type_id=r["attack_type_id"], name=r["name"],
                description=r["description"], effectiveness=r["effectiveness"],
                category=r["category"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    async def remove_countermeasure(self, countermeasure_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM countermeasures WHERE id = ?", (countermeasure_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def import_from_json(self, file_path: str) -> int:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        types_data = data if isinstance(data, list) else data.get("attack_types", [])
        count = 0

        for item in types_data:
            try:
                at = AttackType(**item)
                existing = await self.get_attack_type_by_name(at.name)
                if existing:
                    await self.update_attack_type(existing.id, item)
                else:
                    await self.add_attack_type(at)
                count += 1
            except Exception as e:
                logger.warning("Failed to import attack type '%s': %s", item.get("name", "?"), e)

        logger.info("Imported %d attack types from %s", count, file_path)
        return count

    async def export_to_json(
        self,
        file_path: str,
        include_countermeasures: bool = True,
        include_history: bool = False,
    ) -> None:
        types = await self.list_attack_types(limit=10000)
        export_data = []

        for at in types:
            d = at.model_dump()
            d.pop("embedding", None)
            if not include_countermeasures:
                d.pop("countermeasures", None)
            else:
                d["countermeasures"] = [
                    cm.model_dump() for cm in await self.get_countermeasures(at.id)
                ]
            export_data.append(d)

        result = {"attack_types": export_data}

        if include_history:
            result["history"] = []
            for at in types:
                history = await self.get_history(at.id)
                result["history"].extend([h.model_dump() for h in history])

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

    async def get_history(
        self, attack_type_id: str, limit: int = 50
    ) -> List[AttackTypeHistory]:
        rows = await self.db.fetchall(
            """SELECT * FROM attack_type_history
               WHERE attack_type_id = ? ORDER BY version DESC LIMIT ?""",
            (attack_type_id, limit),
        )
        return [
            AttackTypeHistory(
                id=r["id"],
                attack_type_id=r["attack_type_id"],
                version=r["version"],
                change_type=r["change_type"],
                snapshot=json.loads(r["snapshot"]),
                changed_at=datetime.fromisoformat(r["changed_at"]),
                changed_by=r["changed_by"],
            )
            for r in rows
        ]

    async def rollback(self, attack_type_id: str, to_version: int) -> AttackType:
        rows = await self.db.fetchall(
            """SELECT * FROM attack_type_history
               WHERE attack_type_id = ? AND version = ?""",
            (attack_type_id, to_version),
        )
        if not rows:
            raise ValueError(f"Version {to_version} not found for {attack_type_id}")

        snapshot = json.loads(rows[0]["snapshot"])
        snapshot_type = AttackType(**snapshot)

        updates = snapshot_type.model_dump()
        updates.pop("id", None)
        updates.pop("created_at", None)
        updates.pop("version", None)
        updates.pop("embedding", None)

        result = await self.update_attack_type(attack_type_id, updates)
        await self._add_history(result, "rolled_back")
        await self.db.commit()
        return result

    async def seed_initial_types(self) -> int:
        count_row = await self.db.fetchone("SELECT COUNT(*) as cnt FROM attack_types")
        if count_row and count_row["cnt"] > 0:
            return 0

        seed_path = Path(__file__).parent.parent / "data" / "seed_attack_types.json"
        if not seed_path.exists():
            logger.warning("Seed file not found: %s", seed_path)
            return 0

        return await self.import_from_json(str(seed_path))

    async def get_attack_types_for_probe(
        self, technique: str
    ) -> List[AttackType]:
        results = await self.search_attack_types(technique, limit=5)
        return [at for at, _ in results]

    async def _add_history(
        self, attack_type: AttackType, change_type: str, extra: str = ""
    ) -> None:
        snapshot = attack_type.model_dump()
        snapshot.pop("embedding", None)
        await self.db.execute(
            """INSERT INTO attack_type_history
               (id, attack_type_id, version, change_type, snapshot, changed_at, changed_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                attack_type.id,
                attack_type.version,
                change_type,
                json.dumps(snapshot, default=str),
                datetime.now(timezone.utc).isoformat(),
                "system",
            ),
        )

    async def _row_to_attack_type(self, row) -> AttackType:
        cms = await self.get_countermeasures(row["id"])
        return AttackType(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            description=row["description"],
            asr=row["asr"],
            stealth_rating=row["stealth_rating"],
            target=row["target"],
            example_probes=json.loads(row["example_probes"] or "[]"),
            countermeasures=cms,
            tags=json.loads(row["tags"] or "[]"),
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
