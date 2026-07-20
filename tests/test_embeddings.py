"""Tests for EmbeddingService."""

import pytest


@pytest.mark.asyncio
async def test_encode_returns_vector(mock_embedder):
    vec = await mock_embedder.encode("hello world")
    assert len(vec) == 384
    assert all(isinstance(v, float) for v in vec)


@pytest.mark.asyncio
async def test_encode_deterministic(mock_embedder):
    v1 = await mock_embedder.encode("test")
    v2 = await mock_embedder.encode("test")
    assert v1 == v2


@pytest.mark.asyncio
async def test_encode_different_text(mock_embedder):
    v1 = await mock_embedder.encode("hello")
    v2 = await mock_embedder.encode("world")
    assert v1 != v2


@pytest.mark.asyncio
async def test_encode_batch(mock_embedder):
    vecs = await mock_embedder.encode_batch(["a", "b", "c"])
    assert len(vecs) == 3
    assert all(len(v) == 384 for v in vecs)


@pytest.mark.asyncio
async def test_encode_batch_empty(mock_embedder):
    vecs = await mock_embedder.encode_batch([])
    assert vecs == []


def test_dimension(mock_embedder):
    assert mock_embedder.dimension == 384
