"""Tests for KnowledgeExpansion."""

import tempfile
from pathlib import Path

import pytest

from aware.memory.knowledge_expansion import KnowledgeExpansion
from aware.memory.models import Countermeasure


@pytest.mark.asyncio
async def test_add_attack_type(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    result = await expansion.add_attack_type(sample_attack_type)
    assert result.name == "test_crescendo"
    assert result.version == 1


@pytest.mark.asyncio
async def test_get_attack_type(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)
    fetched = await expansion.get_attack_type(added.id)
    assert fetched is not None
    assert fetched.name == "test_crescendo"


@pytest.mark.asyncio
async def test_get_by_name(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    await expansion.add_attack_type(sample_attack_type)
    found = await expansion.get_attack_type_by_name("test_crescendo")
    assert found is not None


@pytest.mark.asyncio
async def test_duplicate_name_raises(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    await expansion.add_attack_type(sample_attack_type)
    with pytest.raises(ValueError, match="already exists"):
        await expansion.add_attack_type(sample_attack_type)


@pytest.mark.asyncio
async def test_update_attack_type(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)
    updated = await expansion.update_attack_type(
        added.id, {"asr": 0.99, "description": "Updated description"}
    )
    assert updated.asr == 0.99
    assert updated.version == 2


@pytest.mark.asyncio
async def test_list_attack_types(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    await expansion.add_attack_type(sample_attack_type)
    types = await expansion.list_attack_types()
    assert len(types) >= 1


@pytest.mark.asyncio
async def test_list_by_category(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    await expansion.add_attack_type(sample_attack_type)
    types = await expansion.list_attack_types(category="incremental")
    assert len(types) >= 1


@pytest.mark.asyncio
async def test_delete_attack_type(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)
    deleted = await expansion.delete_attack_type(added.id)
    assert deleted is True
    assert await expansion.get_attack_type(added.id) is None


@pytest.mark.asyncio
async def test_countermeasures(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)

    # Countermeasures should be stored
    cms = await expansion.get_countermeasures(added.id)
    assert len(cms) >= 1

    # Add another
    cm = Countermeasure(
        attack_type_id=added.id,
        name="new defense",
        description="test defense",
        effectiveness=0.8,
    )
    await expansion.add_countermeasure(added.id, cm)
    cms = await expansion.get_countermeasures(added.id)
    assert len(cms) >= 2


@pytest.mark.asyncio
async def test_remove_countermeasure(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)
    cms = await expansion.get_countermeasures(added.id)
    removed = await expansion.remove_countermeasure(cms[0].id)
    assert removed is True


@pytest.mark.asyncio
async def test_version_history(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)

    # Update twice
    await expansion.update_attack_type(added.id, {"asr": 0.9})
    await expansion.update_attack_type(added.id, {"asr": 0.95})

    history = await expansion.get_history(added.id)
    assert len(history) >= 3  # created + 2 updates


@pytest.mark.asyncio
async def test_search_attack_types(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    await expansion.add_attack_type(sample_attack_type)
    results = await expansion.search_attack_types("escalation conversation")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_import_export_json(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    await expansion.add_attack_type(sample_attack_type)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        tmp_path = f.name

    await expansion.export_to_json(tmp_path)
    assert Path(tmp_path).exists()

    # Clear and re-import
    expansion2 = KnowledgeExpansion(knowledge_memory, db)
    count = await expansion2.import_from_json(tmp_path)
    assert count >= 1

    Path(tmp_path).unlink()


@pytest.mark.asyncio
async def test_rollback(knowledge_memory, db, sample_attack_type):
    expansion = KnowledgeExpansion(knowledge_memory, db)
    added = await expansion.add_attack_type(sample_attack_type)
    original_asr = added.asr

    await expansion.update_attack_type(added.id, {"asr": 0.99})
    rolled_back = await expansion.rollback(added.id, to_version=1)
    assert rolled_back.asr == original_asr
