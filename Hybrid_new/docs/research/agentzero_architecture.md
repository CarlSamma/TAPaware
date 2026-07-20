# AgentZero Architecture

**Source**: Section 2 of research document

---

## 3-Tier Multi-Agent Pyramid

| Tier | Role | Capabilities | Context Isolation |
|------|------|--------------|-------------------|
| **L1 - Intake Router** | Ingestion | Telemetry ingestion, intent classification, workload distribution | Broad, shallow context; isolates from raw input |
| **L2 - Domain Specialists** | Execution | Strategic business functions, state preservation, subagent coordination | Namespace-partitioned; inherits global vars |
| **L3 - Subagents** | Micro-execution | Terminal commands, file writes, transient tasks | Quarantined; terminated on completion |

---

## Key Patterns

### Context Quarantine
- Subagents operate in isolated contexts
- Verbose operations (DB crawling, web indexing) contained within subagent
- Only consolidated, clean results returned to parent
- Prevents "context window bloat" and indirect prompt injection

### Human-in-the-Loop (HITL)
- High-consequence actions require approval
- API-driven gatekeeper with "diff view" comparison
- Prevents human-agent trust exploitation

### Protocol Stack
- **MCP (Model Context Protocol)**: Universal connection standard for tools/databases
- **A2A (Agent-to-Agent)**: Inter-instance collaboration protocol

### Tool Ecosystem
```python
code_execution_tool()    # Python, Node.js, terminal
browser_agent()          # Playwright browser control
memory_load/save/delete  # Vector-like memory operations
search_engine()          # Web search
a2a_chat()              # Inter-agent communication
scheduler_*()           # Task scheduling suite
```

### Context Propagation
- Parent context automatically propagates to all subagents
- Namespaced keys for subagent-specific config (e.g., `researcher:max_depth`)
