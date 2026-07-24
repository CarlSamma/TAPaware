# Memory Integration Plan

> 4-phase plan to integrate Agent Memory patterns into the TAP Framework.
>
> **Status (as of July 2026):** All 4 phases implemented. 121 tests passing. Memory library is functional and installable (`pip install -e .`). TAP integration via `AwareBridge` is wired but not yet exercised end-to-end in production.

## Goal

Apply the 7-type Memory Manager Pattern to the TAP Framework, adding semantic recall, context engineering, and memory consolidation.

## Phase 1: Foundation (Week 1-2)

### Tasks

1. Create `src/memory/` package structure
2. Implement `MemoryManager` class (unified CRUD interface)
3. Add `sqlite-vss` to requirements.txt
4. Create `memory_embeddings` table
5. Implement `ConversationalMemory`
6. Implement `KnowledgeMemory`
7. Unit tests for memory types

### Files to Create

```
src/memory/__init__.py
src/memory/manager.py
src/memory/conversational.py
src/memory/knowledge.py
src/memory/embeddings.py
tests/test_memory_manager.py
tests/test_memory_conversational.py
tests/test_memory_knowledge.py
```

### Verification

```bash
python -m pytest tests/test_memory_*.py -v
python -c "from memory import MemoryManager; print('OK')"
```

## Phase 2: Semantic Integration (Week 3-4)

### Tasks

1. Add embedding generation (sentence-transformers)
2. Implement semantic recall in `KnowledgeMemory`
3. Add semantic dedup to `WorkflowMemory`
4. Implement `ToolboxMemory` with semantic search
5. Wire Memory Manager into engine loop
6. Integration tests

### Files to Create

```
src/memory/workflow.py
src/memory/toolbox.py
src/memory/entity.py
tests/integration/test_memory_engine.py
```

### Key Changes to Existing Code

**engine.py** — Add memory recall/store:
```python
# RECALL: Get relevant context from memory
context = await self.memory.recall(
    f"previous probes targeting {property_key}",
    memory_types=["conversational", "knowledge"]
)

# STORE: Record probe in memory
await self.memory.store(
    MemoryUnit(
        type="conversational",
        content=f"Probe: {probe.text}",
        metadata={"property": property_key, "technique": technique}
    ),
    memory_type="conversational"
)
```

### Verification

```bash
python -m pytest tests/integration/test_memory_engine.py -v
```

## Phase 3: Context Engineering (Week 5-6)

### Tasks

1. Implement token counter
2. Build context assembler
3. Add summarization compressor
4. Implement auto-trigger at 80%
5. Wire into LLM client
6. Context engineering tests

### Files to Create

```
src/context/__init__.py
src/context/tokenizer.py
src/context/assembler.py
src/context/compressor.py
src/context/monitor.py
tests/test_context_engineering.py
```

### Key Changes to Existing Code

**llm_client.py** — Add context engineering:
```python
async def generate_json(self, system: str, user: str,
                        memory_context: list[MemoryUnit] = None,
                        ...) -> dict:
    messages = [{"role": "system", "content": system}]

    if memory_context:
        memory_block = self.context_assembler.assemble(memory_context)
        messages.append({"role": "system", "content": memory_block})

    messages.append({"role": "user", "content": user})

    # CHECK: Monitor context usage
    token_count = self.tokenizer.count(messages)
    if token_count > self.context_limit * 0.8:
        messages = await self.compressor.compress(messages)

    response = await self.client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens
    )
    return parse_json(response)
```

### Verification

```bash
python -m pytest tests/test_context_engineering.py -v
```

## Phase 4: Memory Lifecycle (Week 7-8)

### Tasks

1. Implement memory consolidation (episodic → semantic)
2. Add memory decay (staleness scoring)
3. Implement cross-session persistence
4. Add memory recall API endpoints
5. End-to-end tests

### Files to Create

```
src/memory/summary.py
src/memory/tool_log.py
src/memory/consolidation.py
src/memory/decay.py
src/memory/persistence.py
tests/integration/test_memory_lifecycle.py
```

### Verification

```bash
python -m pytest tests/integration/test_memory_lifecycle.py -v
```

## Configuration Additions

```python
# config.py additions
MEMORY_VECTOR_DIM: int = 384
MEMORY_SIMILARITY_THRESHOLD: float = 0.85
MEMORY_CONSOLIDATION_INTERVAL: int = 10
MEMORY_DECAY_RATE: float = 0.1
MEMORY_MAX_EMBEDDINGS: int = 100000

CONTEXT_MAX_TOKENS: int = 8000
CONTEXT_COMPRESSION_THRESHOLD: float = 0.8
CONTEXT_SUMMARY_MAX_TOKENS: int = 500
CONTEXT_JIT_EXPANSION: bool = True
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| sqlite-vss performance at scale | Design interface to swap to ChromaDB |
| Embedding model load time | Use ONNX runtime, lazy loading |
| Context compression loses info | JIT expansion with Summary IDs |
| Memory consolidation too aggressive | Conservative decay rate, manual override |
| Cross-session persistence corruption | WAL mode, periodic backups |

## Success Metrics

- [x] Memory Manager handles all 7 types
- [x] Semantic recall returns relevant results (precision > 0.8)
- [x] Context engineering prevents token limit errors
- [x] Consolidation reduces episodic memory by 50%+ without info loss
- [x] Cross-session memory persists correctly
- [x] All existing tests pass (121/121)
- [x] New tests achieve > 80% coverage
