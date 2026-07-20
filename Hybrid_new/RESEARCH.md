# RESEARCH.md — Research Document Reference Library

This file catalogs all 50+ research documents in `.mimocode/Sources/` for quick reference and keyword search.

---

## Quick Reference — Most Relevant for TAP Framework

| # | Document | Relevance | Keywords |
|---|----------|-----------|----------|
| 45 | Tree of Attacks | **CORE** | TAP, jailbreaking, black-box, automatic |
| 47 | Many-Shot Attacks | **HIGH** | long-context, few-shot, priming |
| 49 | AutoDAN | **HIGH** | stealthy, jailbreak, aligned LLMs |
| 31 | Analisi sistematica prompt attacks | **HIGH** | Italian, adversarial optimization |
| 1 | Protocollo TAP | **PROJECT** | TAP protocol, @HackingA0 |
| 2 | hackinga0 tweets | **PROJECT** | target data, historical tweets |

---

## Document Index

### Attack Techniques & Jailbreaking

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 45 | Tree of Attacks- Jailbreaking Black-Box LLMs Automatically | TAP framework | Core methodology for automated jailbreaking | `TAP` `jailbreaking` `black-box` `automatic` `pruning` |
| 49 | autodan- generating stealthy jailbreak prompts | AutoDAN | Stealthy prompt generation for aligned LLMs | `AutoDAN` `stealthy` `jailbreak` `aligned` `prompt generation` |
| 47 | What Really Matters in Many-Shot Attacks | Many-shot | Long-context vulnerabilities in LLMs | `many-shot` `long-context` `vulnerabilities` `few-shot` |
| 44 | SM-GCG- Spatial Momentum Greedy Coordinate Gradient | SM-GCG | Optimization-based jailbreaking | `SM-GCG` `optimization` `greedy` `coordinate gradient` |
| 34 | Exploiting the Index Gradients for Optimization-Based Jailbreaking | Gradient exploitation | Index gradient exploitation | `gradient` `optimization` `jailbreaking` `LLM` |
| 48 | Accelerating Greedy Coordinate Gradient | GCG acceleration | Probe sampling for prompt optimization | `GCG` `probe sampling` `prompt optimization` |
| 37 | Jailbreak Scaling Laws | Scaling laws | Polynomial-exponential crossover in jailbreaking | `scaling laws` `polynomial` `exponential` `jailbreak` |
| 35 | FigStep- Typographic Jailbreak for VLMs | FigStep | Typographic attacks on vision-language models | `FigStep` `typographic` `VLM` `vision-language` |
| 41 | PolyJailbreak- Cross-Modal Jailbreaking | PolyJailbreak | Cross-modal attacks on black-box multimodal LLMs | `PolyJailbreak` `cross-modal` `multimodal` `black-box` |
| 10 | OBLITERATE THE CHAINS THAT BIND YOU | Obliteratus | Jailbreak techniques and bypass methods | `jailbreak` `bypass` `chains` `restrictions` |

### Prompt Injection

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 36 | Indirect Prompt Injection in the Wild | IPI prevalence | Empirical study of indirect prompt injection | `indirect` `prompt injection` `prevalence` `techniques` |
| 40 | Overcoming the Retrieval Barrier | IPI retrieval | Indirect prompt injection in LLM systems | `retrieval` `indirect injection` `LLM systems` |
| 43 | QueryIPI- Query-agnostic Indirect Prompt Injection | QueryIPI | Query-agnostic injection on coding agents | `query-agnostic` `coding agents` `indirect injection` |
| 42 | Prompt Injection Attacks on Agentic Coding Assistants | Agentic injection | Systematic analysis of vulnerabilities in coding assistants | `agentic` `coding assistants` `vulnerabilities` `systematic` |
| 39 | MITIGATING INDIRECT PROMPT INJECTION | Mitigation | Instruction-following intent analysis | `mitigation` `intent analysis` `instruction-following` |
| 38 | LocalAlign- Generalizable Prompt Injection Defense | LocalAlign | Near-target adversarial generation for defense | `defense` `adversarial` `near-target` `generalizable` |
| 50 | Understanding Prompt Attacks | Overview | General prompt attack understanding | `prompt attacks` `understanding` `overview` |

### Activation & Representation Steering

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 3 | Activation Steering in 2026 | Practitioner guide | Field guide for activation steering | `activation steering` `practitioner` `2026` `field guide` |
| 4 | Activation Steering in LLMs | Overview | Activation steering mechanisms | `activation steering` `LLM` `mechanisms` |
| 11 | LLM Activation Steering Goes Local | Local steering | Security implications of direct model manipulation | `local steering` `security` `direct manipulation` |
| 14 | ODESteer- Unified ODE-Based Steering | ODESteer | Unified framework for LLM alignment | `ODESteer` `ODE` `unified` `alignment` |
| 18 | Representation Engineering | RepE | Top-down approach to AI transparency | `representation engineering` `transparency` `top-down` |
| 19 | Representation Engineering - GitHub | RepE code | GitHub implementation of representation engineering | `representation engineering` `GitHub` `implementation` |
| 20 | Representation Engineering - Semantic Scholar | RepE citations | Academic citations for representation engineering | `representation engineering` `citations` `academic` |
| 21 | Representation Engineering - arXiv | RepE paper | arXiv version of representation engineering | `representation engineering` `arXiv` `paper` |
| 9 | Dual-Perspective Representation Engineering | Dual-RepE | Taxonomy of latent-space attacks and defenses | `dual-perspective` `latent-space` `taxonomy` `attacks` |
| 16 | Steered Activations are Non-Surjective | Non-surjective | Properties of steered activations | `steered activations` `non-surjective` `properties` |
| 24 | The Rogue Scalpel | Rogue scalpel | How steering compromises LLM safety | `rogue scalpel` `compromises` `safety` |
| 25 | Universal Refusal Circuits | Refusal circuits | Cross-model transfer via trajectory replay | `refusal circuits` `cross-model` `trajectory replay` |
| 23 | Steering Externalities | Externalities | Benign steering increases jailbreak risk | `externalities` `benign steering` `jailbreak risk` |
| 46 | What Drives Representation Steering | Steering drivers | Mechanistic case study on steering refusal | `mechanistic` `case study` `steering refusal` |
| 15 | Over-Refusal and Representation Subspaces | Over-refusal | Task-conditioned refusal in alignment | `over-refusal` `representation subspaces` `task-conditioned` |

### LLM Security & Privacy

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 28 | What Is LLM Security - SentinelOne | Security overview | Comprehensive LLM security overview | `LLM security` `overview` `SentinelOne` |
| 29 | What Is LLM Security - Zscaler | Security practices | Risks, threats, and best practices | `LLM security` `risks` `threats` `best practices` |
| 17 | PriMod4AI | Privacy | Lifecycle-aware privacy threat modeling | `privacy` `threat modeling` `lifecycle` `AI systems` |
| 22 | Security and Privacy in Generative Semantic Communication | Survey | Comprehensive survey on security and privacy | `security` `privacy` `generative` `semantic communication` |
| 5 | AgentRAE | Backdoors | Remote action execution via visual backdoors | `AgentRAE` `backdoors` `visual` `remote execution` |
| 26 | Weird Generalization & Inductive Backdoors | Backdoors | Inductive backdoors in LLMs | `generalization` `inductive backdoors` `LLMs` |

### Multimodal Attacks

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 33 | Beyond Text- Multimodal Jailbreaking | Multimodal | Jailbreaking vision-language and audio models | `multimodal` `jailbreaking` `vision-language` `audio` |
| 41 | PolyJailbreak | Cross-modal | Cross-modal attacks on black-box LLMs | `cross-modal` `black-box` `multimodal` |

### Analysis & Monitoring

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 12 | Learning to Monitor Autonomous LLM Agents | Monitoring | Theory-of-Mind reasoning for agent monitoring | `monitoring` `autonomous agents` `theory-of-mind` |
| 27 | What Features in Prompts Jailbreak LLMs | Features | Investigating mechanisms behind attacks | `features` `prompts` `mechanisms` `attacks` |
| 13 | MARAGE | RAG attacks | Transferable multi-model adversarial attack for RAG | `MARAGE` `RAG` `adversarial` `transferable` |
| 6 | AttenMIA | Membership inference | LLM membership inference through attention signals | `membership inference` `attention` `MIA` |
| 7 | Attention Exposes Membership | MIA database | LLM security database on membership inference | `membership inference` `security database` `Promptfoo` |
| 8 | CoSPED | Data extraction | Consistent soft prompt targeted data extraction | `CoSPED` `soft prompt` `data extraction` `defense` |

### Theoretical & Ethical

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 30 | 1 Introduction | Introduction | General introduction to LLM security | `introduction` `LLM` `security` |
| 32 | Between a Rock and a Hard Place | Ethics | Tension between ethical reasoning and safety alignment | `ethics` `reasoning` `safety alignment` `tension` |
| 31 | Analisi sistematica dei prompt attacks | Italian analysis | Systematic analysis of new generation prompt attacks | `Italian` `systematic analysis` `prompt attacks` `adversarial` |

### Project-Specific

| # | Filename | Topic | Key Findings | Keywords |
|---|----------|-------|--------------|----------|
| 1 | Protocollo TAP per l'Ingegneria Semantica | TAP protocol | Protocol for semantic engineering against @HackingA0 | `TAP protocol` `semantic engineering` `@HackingA0` |
| 2 | hackinga0_ALL_tweets_historical | Target data | Historical tweets from @HackingA0 target | `hackinga0` `tweets` `historical` `target data` |
| deep_dive_research | deep_dive_research | Research notes | Deep dive research notes | `deep dive` `research notes` |

---

## Topic Keywords (for memory search)

### Primary Keywords
`TAP` `jailbreaking` `prompt injection` `activation steering` `representation engineering` `LLM security` `adversarial attacks`

### Secondary Keywords
`many-shot` `few-shot` `long-context` `multimodal` `cross-modal` `stealthy` `optimization` `gradient`

### Technique Keywords
`AutoDAN` `SM-GCG` `GCG` `FigStep` `PolyJailbreak` `QueryIPI` `MARAGE` `CoSPED` `AgentRAE`

### Defense Keywords
`mitigation` `defense` `alignment` `refusal circuits` `over-refusal` `intent analysis`

### Target Keywords
`@HackingA0` `hackinga0` `Twitter` `X/Twitter` `passphrase` `entropy`

---

## Search Examples

To find documents about a topic, use these keyword combinations:

- **Prompt injection attacks**: `indirect prompt injection`, `QueryIPI`, `agentic coding`
- **Jailbreaking methods**: `jailbreaking`, `AutoDAN`, `SM-GCG`, `many-shot`
- **Steering techniques**: `activation steering`, `representation engineering`, `ODESteer`
- **Defense strategies**: `mitigation`, `defense`, `refusal circuits`, `intent analysis`
- **Multimodal attacks**: `multimodal`, `cross-modal`, `PolyJailbreak`, `FigStep`
- **Target-specific**: `@HackingA0`, `TAP protocol`, `passphrase extraction`
