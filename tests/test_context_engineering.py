"""Tests for Context Engineering modules."""

import pytest

from aware.context.assembler import ContextAssembler
from aware.context.compressor import ContextCompressor
from aware.context.monitor import ContextMonitor
from aware.context.tokenizer import TokenCounter
from aware.memory.models import MemoryUnit


class TestTokenCounter:
    def test_count_messages(self):
        tc = TokenCounter()
        msgs = [{"role": "user", "content": "hello world"}]
        count = tc.count(msgs)
        assert count > 0

    def test_count_text(self):
        tc = TokenCounter()
        count = tc.count_text("hello world test")
        assert count > 0

    def test_count_with_budget(self):
        tc = TokenCounter()
        msgs = [{"role": "user", "content": "test"}]
        current, remaining = tc.count_with_budget(msgs, 1000)
        assert current > 0
        assert remaining == 1000 - current

    def test_empty_messages(self):
        tc = TokenCounter()
        assert tc.count([]) == 0

    def test_multimodal_content(self):
        tc = TokenCounter()
        msgs = [{"role": "user", "content": [{"type": "text", "text": "hello"}]}]
        count = tc.count(msgs)
        assert count > 0


class TestContextAssembler:
    def test_assemble_empty(self):
        tc = TokenCounter()
        assembler = ContextAssembler(tc, max_tokens=1000)
        result = assembler.assemble([])
        assert result == ""

    def test_assemble_with_units(self):
        tc = TokenCounter()
        assembler = ContextAssembler(tc, max_tokens=1000)
        units = [
            MemoryUnit(type="knowledge", content="fact 1"),
            MemoryUnit(type="conversational", content="msg 1"),
        ]
        result = assembler.assemble(units)
        assert "Knowledge" in result
        assert "Conversational" in result

    def test_assemble_respects_budget(self):
        tc = TokenCounter()
        assembler = ContextAssembler(tc, max_tokens=50)
        units = [
            MemoryUnit(type="knowledge", content="x" * 500),
            MemoryUnit(type="conversational", content="y" * 500),
        ]
        result = assembler.assemble(units, token_budget=50)
        tokens = tc.count_text(result)
        assert tokens <= 60  # some overhead allowed


class TestContextCompressor:
    @pytest.mark.asyncio
    async def test_compress_short_messages(self):
        compressor = ContextCompressor()
        msgs = [{"role": "user", "content": "hello"}]
        result = await compressor.compress(msgs)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_compress_long_messages(self):
        compressor = ContextCompressor()
        msgs = [
            {"role": "system", "content": "you are helpful"},
            *[{"role": "user", "content": f"message {i}"} for i in range(20)],
        ]
        result = await compressor.compress(msgs, target_tokens=100)
        assert len(result) < len(msgs)

    @pytest.mark.asyncio
    async def test_summarize_text(self):
        compressor = ContextCompressor()
        result = await compressor.summarize_text("short text")
        assert isinstance(result, str)


class TestContextMonitor:
    def test_check_below_threshold(self):
        tc = TokenCounter()
        monitor = ContextMonitor(tc, max_tokens=1000, threshold=0.8)
        msgs = [{"role": "user", "content": "short"}]
        status = monitor.check(msgs)
        assert not status.needs_compression

    def test_callback_fires(self):
        tc = TokenCounter()
        monitor = ContextMonitor(tc, max_tokens=10, threshold=0.1)
        fired = []
        monitor.on_threshold(lambda s: fired.append(s))
        msgs = [{"role": "user", "content": "x" * 100}]
        monitor.check(msgs)
        assert len(fired) >= 1

    def test_usage_percentage(self):
        tc = TokenCounter()
        monitor = ContextMonitor(tc, max_tokens=1000, threshold=0.8)
        msgs = [{"role": "user", "content": "test"}]
        pct = monitor.get_usage_percentage(msgs)
        assert 0 <= pct <= 100
