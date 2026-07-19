# Memory Architecture Gaps

> Analysis of TAP's current memory architecture against the Agent Memory framework.

## Current State

TAP has 9 SQLite tables but NO vector store, NO context management, NO memory consolidation, and NO cross-session learning.

## 7 Critical Gaps

### 1. NO VECTOR STORE
- **Evidence**: Zero embedding models, zero vector databases, zero semantic search
- **Current**: All matching is lexical (Jaccard, regex)
- **Gap**: `probe_memory.py` L28-30: "Embedding-based ANN is deferred to Phase 7"
- **Impact**: Cannot semantically deduplicate probes or recall similar past interactions

### 2. NO CONTEXT WINDOW MANAGEMENT
- **Evidence**: No token counting, no truncation, no conversation history management
- **Current**: Only `max_tokens` output limits on LLM calls
- **Gap**: `gamma_tracker.py` L141: Only context management = `context[-5:]` string truncation
- **Impact**: LLM calls may exceed context limits, no compression possible

### 3. NO MEMORY CONSOLIDATION
- **Evidence**: Events fire-and-forget, no episodic-to-semantic promotion
- **Current**: `event_log` stores raw events but never consolidates
- **Gap**: No repeated observation consolidation
- **Impact**: Memory grows unbounded, no knowledge distillation

### 4. NO MEMORY DECAY
- **Evidence**: All facts permanent, no staleness handling
- **Current**: Properties, aliases, intel all persist forever
- **Gap**: No decay rate, no expiration
- **Impact**: Stale information pollutes context

### 5. NO RECALL/RETRIEVAL API
- **Evidence**: No semantic search across knowledge base
- **Current**: SSOT is flat markdown, no query mechanism
- **Gap**: Cannot ask "what do I know about X?"
- **Impact**: Engine cannot leverage past knowledge

### 6. NO MEMORY TYPE DISTINCTION
- **Evidence**: Everything in flat SQLite tables
- **Current**: No episodic/semantic/procedural separation
- **Gap**: All memories treated equally
- **Impact**: Cannot prioritize or route memory operations

### 7. NO CROSS-SESSION LEARNING
- **Evidence**: Memory per-run, only SQLite file persists
- **Current**: Each attack session starts fresh
- **Gap**: No learning from past missions
- **Impact**: Repeats failed approaches

## Existing Assets That Map to Agent Memory Types

| Agent Memory Type | TAP Table/Module | Status |
|---|---|---|
| Conversational | `event_log` + `tweets` | Working (raw events) |
| Knowledge Base | `properties` + SSOT | Working (structured facts, no vector search) |
| Workflow | `probe_memory` + V-Genome provenance | Partial (technique-level only) |
| Toolbox | (none) | Missing — need skill/tool memory |
| Entity | `other_user_intel` | Working (time-windowed, not accumulated) |
| Summary | SSOT | Working (flat document, no token-aware compression) |
| Tool Log | `event_log` | Working (raw audit trail) |

## Key Code Evidence

```python
# probe_memory.py L28-30
"Embedding-based ANN is deferred to Phase 7."

# gamma_tracker.py L141
context=" | ".join(context[-5:])  # Only context management

# m2s_converter.py L79
"Simple truncation with ellipsis; real implementation can use summarization."
```

## Impact on TAP Scope

Without these improvements:
- Probes are not semantically deduplicated (repeats similar approaches)
- No context engineering (LLM calls may fail or be suboptimal)
- No learning from past sessions (starts fresh each time)
- No memory consolidation (unbounded growth)

With these improvements:
- 30-50% reduction in probes needed (semantic dedup)
- Better LLM context (context engineering)
- Cross-session learning (memory persistence)
- Knowledge distillation (consolidation)
