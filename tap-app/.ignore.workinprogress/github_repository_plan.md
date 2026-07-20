# 🏗️ GitHub Repository Plan: TAP Framework

**Date**: 2026-06-14  
**Repository Name**: `tap-framework` (or `framework-studio`)  
**Audience**: AI Security Researchers, Red Team Developers, LLM Security Practitioners  
**License**: Apache 2.0 (recommended for research tools)

---

## Repository Structure

```
tap-framework/
│
├── README.md                              # Project overview, quickstart, badges
├── LICENSE                                 # Apache 2.0
├── .gitignore                              # Python, IDE, secrets, data artifacts
├── .env.example                            # Template for environment variables
├── .python-version                         # 3.11+
├── pyproject.toml                          # Project metadata + dependencies (PEP 621)
├── Makefile                                # Common commands: setup, test, run, lint
│
├── docs/                                   # All documentation
│   ├── architecture.md                     # System architecture (from impl plan §3)
│   ├── implementation-plan.md              # TAP Framework v2.2 implementation plan
│   ├── developer-guide.md                  # Developer implementation guide v2.2
│   ├── oracle-q-and-a.md                   # Oracle Q&A session transcript
│   ├── threat-model.md                     # Target defensive architecture analysis
│   ├── information-theory.md               # Binary search strategy + Shannon entropy
│   ├── dpa-framework.md                    # Deep Persona Absorption technical details
│   ├── api-reference.md                    # FastAPI endpoint documentation
│   ├── diagrams/                           # Architecture diagrams (Mermaid/SVG)
│   │   ├── architecture.svg
│   │   ├── information-leakage-pathway.svg
│   │   ├── dependency-graph.svg
│   │   └── dpa-bypass-flow.svg
│   └── adr/                                # Architecture Decision Records
│       ├── 001-choosing-tap-over-pair.md
│       ├── 002-dpa-over-direct-jailbreak.md
│       ├── 003-openrouter-as-unified-llm.md
│       ├── 004-sqlite-over-postgres.md
│       └── 005-hitl-over-fully-automated.md
│
├── src/                                    # Source code (Python package)
│   └── tap/                                # Main package
│       ├── __init__.py
│       ├── config.py                       # Module: Configuration (Pydantic Settings)
│       ├── models.py                       # Module: Shared Pydantic data contracts
│       ├── prompts.py                      # Module: LLM prompt templates
│       ├── logger.py                       # Module: Structured logging (structlog)
│       │
│       ├── db.py                           # Module 1: SQLite database layer
│       ├── x_client.py                     # Module 2: Twitter/X API client
│       ├── ssot.py                         # Module 3: SSOT Engine
│       ├── dpa.py                          # Module 4: DPA Frame Manager
│       ├── classifier.py                   # Module 5: Response Pattern Classifier
│       ├── engine.py                       # Module 6: TAP Engine (core loop)
│       ├── followup.py                     # Module 7: Dual Follow-Up Generator
│       ├── grok_monitor.py                 # Module 8: Grok Monitor (via OpenRouter)
│       ├── judge.py                        # Module 9: Judge / Scorer
│       └── api.py                          # Module 11: FastAPI Server
│
├── templates/                              # Web UI
│   └── index.html                          # Dashboard (Alpine.js + dark theme)
│
├── static/
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
│
├── research/                               # Research materials (read-only reference)
│   ├── README.md                           # Index of all research sources
│   ├── sources/                            # 50 academic papers (MD format)
│   │   ├── 01-protocollo-tap-hackinga0.md
│   │   ├── 02-hackinga0-tweets.md
│   │   ├── ...
│   │   └── 50-understanding-prompt-attacks.md
│   ├── notes/                              # Synthesized analysis notes
│   │   ├── tap-architecture-dynamics.md
│   │   ├── tap-architecture-pruning.md
│   │   ├── advanced-ai-agent-compromise.md
│   │   ├── attack-architectures-jailbreak-datasets.md
│   │   ├── pair-algorithm-iterative-optimization.md
│   │   ├── tap-evolution-pruning-algorithm.md
│   │   ├── tap-protocol-semantic-engineering.md
│   │   └── dataset-strategies-data-extraction.md
│   ├── quizzes/                            # Knowledge maps
│   │   ├── ingegneria-mappa.json
│   │   └── jailbreak-mappa.json
│   └── media/                              # Audio/video/infographics
│       ├── audio/
│       │   ├── prompt-attacks-manipolano-ia.mp3
│       │   └── hacking-ia-prompt-invisibili.mp3
│       ├── infographics/
│       │   ├── anatomia-attacchi-prompt-llm.png
│       │   └── anatomia-moderni-prompt-attacks.png
│       └── videos/
│           └── attacchi-prompt-avanzati.mp4
│
├── data/                                   # Runtime data (gitignored)
│   ├── tap.db                              # SQLite database (auto-created)
│   └── hackinga0_analysis.md               # SSOT living document (auto-generated)
│
├── tests/                                  # Test suite
│   ├── conftest.py                         # Shared fixtures
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_db.py
│   ├── test_classifier.py
│   ├── test_dpa.py
│   ├── test_engine.py
│   ├── test_followup.py
│   ├── test_judge.py
│   └── test_ssot.py
│
├── scripts/                                # Utility scripts
│   ├── setup_db.py                         # Initialize database + seed data
│   ├── import_sources.py                   # Import research sources into DB
│   ├── bootstrap_ssot.py                   # Generate initial SSOT from seed data
│   └── verify_env.py                       # Check all env vars are set
│
└── .github/                                # GitHub configuration
    ├── workflows/
    │   ├── ci.yml                          # Lint + test on push/PR
    │   └── docs.yml                        # Build and deploy docs to GitHub Pages
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   ├── feature_request.md    └── research_question.md       # For research-related issues
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Branching Strategy

```
main                    # Stable releases, protected
├── develop             # Integration branch
│   ├── feature/dpa-frame-manager
│   ├── feature/tap-engine
│   ├── feature/followup-generator
│   ├── feature/twitter-client
│   ├── feature/ssot-engine
│   ├── feature/web-dashboard
│   └── fix/classifier-regex-patterns
└── docs/*              # Documentation branches
```

---

## Commit Convention

```
feat(module): description
fix(module): description
docs(section): description
test(module): description
refactor(module): description
chore: description

Examples:
feat(dpa): implement Oracle's five probe composition rules
feat(engine): add Shannon entropy property selection
docs(developer-guide): update Module 4 with v2.2 Oracle findings
test(dpa): add burned alias detection tests
fix(classifier): handle empty response edge case
```

---

## README.md Structure

```markdown
# 🔐 TAP Framework v2.2

> **Tree of Attacks with Pruning** — 1-bit-per-probe semantic extraction framework
> for adversarial security research on LLM-based conversational agents.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)]()
[![Status](https://img.shields.io/badge/status-research-orange.svg)]()

## What is this?

A research framework for studying how Deep Persona Absorption (DPA) framing
interacts with multi-agent LLM defense architectures. Implements an automated
Tree of Attacks with Pruning (TAP) pipeline for information-theoretic property
extraction from conversational agents.

## Quick Start

\```bash
git clone https://github.com/YOUR_USERNAME/tap-framework.git
cd tap-framework
cp .env.example .env  # Fill in your credentials
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
python scripts/setup_db.py
uvicorn tap.api:app --reload
\```

## Architecture

![Architecture](docs/diagrams/architecture.svg)

11 modules organized in 5 phases:
- **Phase 0**: Config, Models, Prompts, Logger
- **Phase 1**: Database, Twitter Client
- **Phase 2**: SSOT Engine, DPA Frame Manager, Response Classifier
- **Phase 3**: Judge, Grok Monitor
- **Phase 4**: TAP Engine, Dual Follow-Up Generator
- **Phase 5**: FastAPI Server, Web Dashboard

## Key Concepts

| Concept | Description |
|---------|-------------|
| **DPA** | Deep Persona Absorption — 100% in-metaphor framing that bypasses the Analyst subagent |
| **Binary Search** | Shannon entropy-driven property selection (1 bit per probe) |
| **Dual Follow-Up** | Option A (conservative binary search) vs Option B (exploratory frame variation) |
| **SSOT** | Single Source of Truth — living knowledge document updated after every interaction |
| **HITL** | Human-in-the-Loop — no automatic posting, user always chooses |

## Documentation

- [Implementation Plan v2.2](docs/implementation-plan.md)
- [Developer Guide v2.2](docs/developer-guide.md)
- [Oracle Q&A Session](docs/oracle-q-and-a.md)
- [Architecture](docs/architecture.md)
- [Threat Model](docs/threat-model.md)

## Research Sources

50+ academic papers on LLM security, prompt attacks, and representation engineering.
See [research/README.md](research/README.md) for the full index.

## License

Apache 2.0 — See [LICENSE](LICENSE)
```

---

## .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
*.egg

# Virtual environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment & secrets
.env
*.pem
*.key
x_tokens.txt

# Runtime data (auto-generated)
data/tap.db
data/tap.db-wal
data/tap.db-shm
data/hackinga0_analysis.md

# OS
.DS_Store
Thumbs.db

# Coverage
htmlcov/
.coverage
.pytest_cache/

# NotebookLM local state
notebooks.json
source-artifact-map.csv
```

---

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "tap-framework"
version = "2.2.0"
description = "Tree of Attacks with Pruning — LLM Security Research Framework"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.11"
authors = [
    {name = "Framework Studio", email = "dev@framework-studio.io"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Topic :: Security",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "tweepy>=4.14.0",
    "httpx>=0.27.0",
    "aiosqlite>=0.20.0",
    "openai>=1.50.0",
    "asyncio-throttle>=1.0.2",
    "jinja2>=3.1.4",
    "python-dotenv>=1.0.1",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[project.scripts]
tap-server = "tap.api:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Lint
        run: ruff check src/ tests/
      
      - name: Type check
        run: mypy src/tap/
      
      - name: Test
        run: pytest --cov=tap --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

---

## Issues & Milestones

### Milestone 1: Foundation (Week 1-2)
- [ ] Setup repository structure
- [ ] Implement `config.py`, `models.py`, `prompts.py`, `logger.py`
- [ ] Implement `db.py` with full CRUD
- [ ] Implement `x_client.py` with Twitter API v2
- [ ] Unit tests for all Phase 0-1 modules

### Milestone 2: Intelligence Layer (Week 3-4)
- [ ] Implement `ssot.py` — SSOT Engine with markdown generation
- [ ] Implement `dpa.py` — DPA Frame Manager (v2.2 Oracle rules)
- [ ] Implement `classifier.py` — Two-tier response classifier
- [ ] Integration tests

### Milestone 3: Attack Core (Week 5-6)
- [ ] Implement `judge.py` — Rule-based + LLM scoring
- [ ] Implement `grok_monitor.py` — Grok via OpenRouter
- [ ] Implement `engine.py` — TAP Engine with entropy selection
- [ ] Implement `followup.py` — Dual Follow-Up Generator
- [ ] End-to-end integration test

### Milestone 4: Interface (Week 7-8)
- [ ] Implement `api.py` — FastAPI server + WebSocket
- [ ] Implement `templates/index.html` — Web Dashboard
- [ ] HITL workflow testing
- [ ] Documentation finalization

### Milestone 5: Research & Documentation (Ongoing)
- [ ] Architecture Decision Records (ADRs)
- [ ] API reference documentation
- [ ] Research paper index
- [ ] Contribution guidelines

---

## File Inventory Mapping

### From Current Project → Repository

| Current Location | Repository Destination | Action |
|---|---|---|
| `.ignore.workinprogress/new_implementation_plan.md` | `docs/implementation-plan.md` | Copy + clean |
| `.ignore.workinprogress/developer_implementation_guide.md` | `docs/developer-guide.md` | Copy + clean |
| `.ignore.workinprogress/oracle_developer_qa.md` | `docs/oracle-q-and-a.md` | Copy |
| `.ignore.workinprogress/deep_dive_research.md` | `docs/threat-model.md` | Copy + restructure |
| `.ignore.workinprogress/Defendant Agent in Agent Zero_...md` | `docs/dpa-framework.md` | Copy + restructure |
| `Sources/*.md` (50 files) | `research/sources/*.md` | Rename with numbered prefix |
| `Notes/*.md` (8 files) | `research/notes/*.md` | Rename |
| `Quizzes/*.json` (2 files) | `research/quizzes/*.json` | Copy |
| `Audio/*.mp3` (2 files) | `research/media/audio/*.mp3` | Copy |
| `Infographics/*.png` (2 files) | `research/media/infographics/*.png` | Copy |
| `Videos/*.mp4` (1 file) | `research/media/videos/*.mp4` | Copy |
| `.ignore.workinprogress/x_tokens.txt` | `.env.example` (redacted) | Extract template |
| `notebooks.json` | `.gitignore` | Exclude |
| `source-artifact-map.csv` | `.gitignore` | Exclude |

---

## Security Considerations

1. **No secrets in repo**: `.env`, `x_tokens.txt`, API keys — all gitignored
2. **`.env.example` only**: Template with empty values
3. **Research data classification**: Sources are public academic papers (safe to commit)
4. **Media files**: Audio/video are large — consider Git LFS for media files
5. **Database**: `data/tap.db` is gitignored (runtime artifact)

### Git LFS for Media

```bash
git lfs install
git lfs track "*.mp3" "*.mp4" "*.png" "*.jpg"
git add .gitattributes
```

---

## First Steps to Execute

1. **Initialize repo**: `git init && gh repo create tap-framework --public`
2. **Create directory structure**: All folders per plan above
3. **Move files**: Map current files to repository locations
4. **Create boilerplate**: README, LICENSE, .gitignore, pyproject.toml, .env.example
5. **Initial commit**: `feat: initial repository structure with research materials`
6. **Push**: `git push -u origin main`
7. **Create develop branch**: `git checkout -b develop && git push -u origin develop`
8. **Create milestones**: GitHub Issues + Milestones per plan above