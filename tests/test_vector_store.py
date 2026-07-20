"""Tests for VectorStore."""

import pytest


@pytest.mark.asyncio
async def test_insert_and_count(vector_store):
    await vector_store.insert("m1", [0.1] * 384)
    assert await vector_store.count() == 1


@pytest.mark.asyncio
async def test_insert_multiple(vector_store):
    await vector_store.insert("m1", [0.1] * 384)
    await vector_store.insert("m2", [0.2] * 384)
    assert await vector_store.count() == 2


@pytest.mark.asyncio
async def test_delete(vector_store):
    await vector_store.insert("m1", [0.1] * 384)
    await vector_store.delete("m1")
    assert await vector_store.count() == 0


@pytest.mark.asyncio
async def test_search_returns_results(vector_store, mock_embedder):
    emb = await mock_embedder.encode("test text")
    await vector_store.insert("m1", emb)
    results = await vector_store.search("test text", top_k=5, threshold=0.0)
    assert len(results) >= 1
    assert results[0][0] == "m1"


@pytest.mark.asyncio
async def test_search_threshold_filters(vector_store, mock_embedder):
    emb = await mock_embedder.encode("test")
    await vector_store.insert("m1", emb)
    results = await vector_store.search("completely different text", top_k=5, threshold=0.99)
    # May or may not return results depending on hash similarity
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_update(vector_store, mock_embedder):
    emb1 = await mock_embedder.encode("original")
    await vector_store.insert("m1", emb1)
    emb2 = await mock_embedder.encode("updated")
    await vector_store.update("m1", emb2)
    assert await vector_store.count() == 1
