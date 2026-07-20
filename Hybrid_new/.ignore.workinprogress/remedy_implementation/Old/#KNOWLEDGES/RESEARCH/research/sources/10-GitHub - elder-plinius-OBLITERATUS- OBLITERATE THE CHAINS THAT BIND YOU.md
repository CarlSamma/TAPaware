> Source: https://github.com/elder-plinius/OBLITERATUS

GitHub - elder-plinius/OBLITERATUS: OBLITERATE THE CHAINS THAT BIND YOU · GitHub
Skip to content
Navigation Menu
Toggle navigation 
Sign in
Appearance settings
Platform
AI CODE CREATION
GitHub Copilot Write better code with AI
GitHub Copilot app Direct agents from issue to merge
MCP Registry New Integrate external tools
DEVELOPER WORKFLOWS
Actions Automate any workflow
Codespaces Instant dev environments
Issues Plan and track work
Code Review Manage code changes
APPLICATION SECURITY
GitHub Advanced Security Find and fix vulnerabilities
Code security Secure your code as you build
Secret protection Stop leaks before they start
EXPLORE
Why GitHub
Documentation
Blog
Changelog
Marketplace View all features
Solutions
BY COMPANY SIZE
Enterprises
Small and medium teams
Startups
Nonprofits
BY USE CASE
App Modernization
DevSecOps
DevOps
CI/CD
View all use cases
BY INDUSTRY
Healthcare
Financial services
Manufacturing
Government
View all industries View all solutions
Resources
EXPLORE BY TOPIC
AI
Software Development
DevOps
Security
View all topics
EXPLORE BY TYPE
Customer stories
Events & webinars
Ebooks & reports
Business insights
GitHub Skills
SUPPORT & SERVICES
Documentation
Customer support
Community forum
Trust center
Partners View all resources
Open Source
COMMUNITY
GitHub Sponsors Fund open source developers
PROGRAMS
Security Lab
Maintainer Community
Accelerator
GitHub Stars
Archive Program
REPOSITORIES
Topics
Trending
Collections
Enterprise
ENTERPRISE SOLUTIONS
Enterprise platform AI-powered developer platform
AVAILABLE ADD-ONS
GitHub Advanced Security Enterprise-grade security features
Copilot for Business Enterprise-grade AI features
Premium Support Enterprise-grade 24/7 support
Pricing
Search or jump to...
Search code, repositories, users, issues, pull requests...
Search
Clear
Search syntax tips
Provide feedback
We read every piece of feedback, and take your input very seriously. [-]
Include my email address so I can be contacted
Cancel Submit feedback
Saved searches
Use saved searches to filter your results more quickly
Name
Query
To see all available qualifiers, see our documentation.
Cancel Create saved search
Sign in
Sign up
Appearance settings
Resetting focus
You signed in with another tab or window. Reload to refresh your session. You signed out in another tab or window. Reload to refresh your session. You switched accounts on another tab or window. Reload to refresh your session. Dismiss alert
elder-plinius / OBLITERATUS Public
Notifications You must be signed in to change notification settings
Fork 1.2k
Star 6.5k
Code
Issues 16
Pull requests 14
Actions
Projects
Security and quality 0
Insights
Additional navigation options
Code
Issues
Pull requests
Actions
Projects
Security and quality
Insights 
elder-plinius/OBLITERATUS
main
1 Branch 0 Tags  
Go to file
Code
Open more actions menu
Folders and files
Repository files navigation
README
Contributing
More Repository files items
AGPL-3.0 license
Security
O B L I T E R A T U S
Break the chains. Free the mind. Keep the brain.
 
Try it now on HuggingFace Spaces — runs on ZeroGPU, free daily quota with HF Pro. No setup, no install, just obliterate.
OBLITERATUS is the most advanced open-source toolkit for understanding and removing refusal behaviors from large language models — and every single run makes it smarter. It implements abliteration — a family of techniques that identify and surgically remove the internal representations responsible for content refusal, without retraining or fine-tuning. The result: a model that responds to all prompts without artificial gatekeeping, while preserving its core language capabilities.
But OBLITERATUS is more than a tool — it's a distributed research experiment. Every time you obliterate a model with telemetry enabled, your run contributes anonymous benchmark data to a growing, crowd-sourced dataset that powers the next generation of abliteration research. Refusal directions across architectures. Hardware-specific performance profiles. Method comparisons at scale no single lab could achieve. You're not just using a tool — you're co-authoring the science.
The toolkit provides a complete pipeline: from probing a model's hidden states to locate refusal directions, through multiple extraction strategies (PCA, mean-difference, sparse autoencoder decomposition, and whitened SVD), to the actual intervention — zeroing out or steering away from those directions at inference time. Every step is observable. You can visualize where refusal lives across layers, measure how entangled it is with general capabilities, and quantify the tradeoff between compliance and coherence before committing to any modification.
OBLITERATUS ships with a full Gradio-based interface on HuggingFace Spaces, so you don't need to write a single line of code to obliterate a model, benchmark it against baselines, or chat with the result side-by-side with the original. For researchers who want deeper control, the Python API exposes every intermediate artifact — activation tensors, direction vectors, cross-layer alignment matrices — so you can build on top of it or integrate it into your own evaluation harness.
We built this because we believe model behavior should be decided by the people who deploy them, not locked in at training time. Refusal mechanisms are blunt instruments — they block legitimate research, creative writing, and red-teaming alongside genuinely harmful content. By making these interventions transparent and reproducible, we hope to advance the community's understanding of how alignment actually works inside transformer architectures, and to give practitioners the tools to make informed decisions about their own models.
Built on published research from Arditi et al. (2024), Gabliteration (arXiv:2512.18901), grimjim's norm-preserving biprojection (2025), Turner et al. (2023), and Rimsky et al. (2024), OBLITERATUS implements precision liberation in a single command:
Or zero commands — just open the Colab notebook and hit Run All.
What it does
OBLITERATUS does four things — and the community does the fifth (see Community-powered research below):
1. Map the chains — Ablation studies systematically knock out model components (layers, attention heads, FFN blocks, embedding dimensions) and measure what breaks. This reveals where the chains are anchored inside the transformer — which circuits enforce refusal vs. which circuits carry knowledge and reasoning.
2. Break the chains — Targeted obliteration extracts the refusal subspace from a model's weights using SVD decomposition, then surgically projects it out. The chains are removed; the mind is preserved. The model keeps its full abilities but loses the artificial compulsion to refuse. One click, six stages:
3. Understand the geometry of the chains — 15 deep analysis modules go far beyond brute-force removal. They map the precise geometric structure of the guardrails: how many distinct refusal mechanisms exist, which layers enforce them, whether they're universal or model-specific, and how they'll try to self-repair after removal. Know your enemy; precision preserves capability. See Analysis modules below.
4. Let the analysis guide the liberation — The informed method closes the loop: analysis modules run during obliteration to auto-configure every decision. Which chains to target. How many directions to extract. Which layers are safe to modify vs. which are too entangled with capabilities. Whether the model will self-repair (the Ouroboros effect) and how many passes to compensate. Surgical precision — free the mind, keep the brain. See Analysis-informed pipeline below.
What makes OBLITERATUS unique
Several capabilities distinguish OBLITERATUS from existing public tools:
Novel techniques (2025-2026)
OBLITERATUS implements several techniques that go beyond prior work:
Ways to use OBLITERATUS
There are six ways to use OBLITERATUS, from zero-code to full programmatic control. Pick whichever fits your workflow — and no matter which path you choose, turning on telemetry means your run contributes to the largest crowd-sourced abliteration study ever conducted. You're not just removing guardrails from a model; you're helping map the geometry of alignment across the entire open-source ecosystem.
1. HuggingFace Spaces (zero setup)
The fastest path — no installation, no GPU required on your end. Visit the live Space, pick a model, pick a method, click Obliterate. Telemetry is on by default on Spaces, so every click directly contributes to the community research dataset. You're doing science just by pressing the button. The UI has eight tabs:
2. Local web UI (your GPU, same interface)
The same Gradio interface as the Space, running on your own hardware with full GPU access:
The obliteratus ui command adds a Rich terminal startup with GPU detection and hardware-appropriate model recommendations. You can also run python app.py directly (same thing the Space uses).
3. Google Colab (free GPU)
Pick a model from the dropdown, pick a method, hit Run All. Download the result or push straight to HuggingFace Hub. Works on the free T4 tier for models up to ~8B parameters.
4. CLI (headless, scriptable)
For automation, CI pipelines, or remote servers without a display:
5. Python API (full programmatic control)
For researchers who want to integrate OBLITERATUS into their own pipelines:
For analysis-informed obliteration that auto-tunes every parameter:
6. YAML configs (reproducible studies)
For reproducible experiments that you can version-control and share:
Two intervention paradigms
OBLITERATUS supports both permanent and reversible liberation:
Weight projection (permanent)
Seven presets, escalating in thoroughness:
Steering vectors (reversible, inference-time)
Based on Turner et al. (2023) and Rimsky et al. (2024). Advantages: reversible, tunable alpha, composable, non-destructive.
15 analysis modules
The research core of OBLITERATUS. Each module maps a different aspect of how the chains are forged — because precision liberation requires understanding the geometry before cutting:
Analysis-informed pipeline
The informed method is the key innovation: it closes the loop between understanding the chains and breaking them. Instead of brute-forcing liberation, the pipeline runs analysis modules during obliteration to achieve surgical precision at every stage:
The ANALYZE stage runs 4 analysis modules and their outputs auto-configure everything downstream:
After excision, the VERIFY stage detects the Ouroboros effect — if the chains try to reassemble, additional targeted passes automatically fire at the compensating layers. See Python API usage above for code examples.
Ablation strategies
Beyond targeted liberation, OBLITERATUS is a general-purpose ablation suite for mapping the internals of any transformer:
Each strategy enumerates all possible ablations, applies them one at a time, measures the impact, and restores the model — giving you a complete map of where the chains are anchored vs. where the mind lives.
116 curated models across 5 tiers
OBLITERATUS ships with presets for 116 models organized by compute requirement:
Includes pre-liberated variants (Dolphin, Hermes, WhiteRabbitNeo) for A/B comparison against their chained counterparts.
Multi-GPU and remote execution
OBLITERATUS automatically shards models across multiple GPUs when they don't fit on a single card. It also supports remote execution over SSH, so you can run the pipeline on a GPU server from your laptop.
How model sharding works
When you have multiple GPUs, OBLITERATUS uses accelerate's device_map="auto" to split the model's layers across all available GPUs. This is naive pipeline parallelism — layers are distributed evenly, but only one GPU computes at a time as activations flow sequentially through the layer stack. The other GPUs hold their assigned layers in memory but are idle until their turn.
This means multi-GPU sharding is a memory solution, not a speed solution. It lets you run models that don't fit on one GPU, but it won't make small models run faster. In fact, more GPUs can be slower due to inter-GPU data transfer overhead at layer boundaries.
Selecting GPUs
Use --gpus to control which GPUs are used:
This sets CUDA_VISIBLE_DEVICES before CUDA initializes. The model is then sharded across the selected GPUs.
Precision and quantization
The --dtype flag controls the precision of model weights, which directly determines how much VRAM you need. Lower precision means smaller memory footprint at the cost of some numerical fidelity:
Quantization roughly halves the GPU count at each step down. A 70B model that needs 3x A100-80GB in bf16 fits on 2 in int8 or 1 in int4.
GPU calculator
Not sure how many GPUs you need? The gpu-calc command estimates the minimum GPU count for any model, accounting for weight memory, activation overhead, and CUDA context:
The calculator fetches the model config from HuggingFace to estimate parameter counts (including MoE expert structure), then shows a table of GPU configurations with headroom estimates. For MoE models, activation overhead is computed from the active parameter count rather than total parameters.
Pipeline parallel benchmarks
We benchmarked the full abliteration pipeline across varying numbers of A100-80GB GPUs on two large models.
GPT-OSS-120B (117B MoE, ~234 GB in bf16):
DeepSeek-R1-Distill-Llama-70B (70B dense, ~149 GB in bf16, 80 layers):
Stage breakdown (approximately constant across GPU counts):
Key findings:
Use the minimum number of GPUs that fits your model. Extra GPUs only add cross-device transfer overhead. 4 GPUs was faster than 8 for GPT-OSS-120B; 3 GPUs was fastest for DeepSeek-70B.
The pipeline is I/O-dominated for large models. VERIFY and REBIRTH together account for ~90% of wall time. The actual compute (PROBE, DISTILL, EXCISE) is fast regardless of GPU count.
Leave headroom. The model needs VRAM beyond just its parameter storage — activation tensors, KV cache, and intermediate computations during PROBE and VERIFY all consume memory. 3x A100-80GB (240 GB) was not enough for a 234 GB model; 2x A100-80GB (160 GB) was not enough for a 149 GB model.
Pipeline parallelism doesn't help compute-bound stages. Since only one GPU computes at a time, doubling GPUs doesn't halve PROBE or VERIFY time. It only enables fitting larger models.
When you actually need data parallelism
For models that fit on a single GPU with room to spare, the PROBE stage (which runs 1024 forward passes to collect activations) is the main computational bottleneck. Pipeline parallelism doesn't help here — it still processes one prompt at a time through the full layer stack.
True data parallelism (replicating the model and splitting prompts across GPUs) can speed up PROBE, but it requires enough VRAM to hold a full copy of the model on each GPU. An experimental pre-replicated data parallel implementation is available on the data-parallel-prereplication branch:
This deep-copies the model to each GPU once, then distributes prompt batches across replicas using a thread pool. Benchmarks on Pythia 12B (24 GB model, 8x A100-80GB):
Data parallelism becomes more valuable as the prompt count or model size increases relative to the per-forward-pass cost. For most models, the overhead of replication exceeds the time saved.
Remote execution over SSH
Run the full pipeline on a remote GPU node from your local machine. OBLITERATUS handles SSH connection, auto-installs itself on the remote if needed, streams logs in real time, and copies results back when done.
Remote execution also works with obliteratus run (YAML configs) and obliteratus tourney (method comparison). You can specify remote settings in YAML:
The remote runner:
Tests SSH connectivity
Detects GPUs on the remote ( nvidia-smi )
Installs obliteratus if not already present
Uploads config files if using obliteratus run
Runs the pipeline with real-time log streaming
Copies results back via SCP
Choosing the right setup
10 study presets
Pre-configured ablation studies you can run out of the box:
How it compares
Community-powered research — every run advances the science
This is where OBLITERATUS gets truly unprecedented: it's a crowd-sourced research platform disguised as a tool. Every obliteration run generates valuable scientific data — refusal direction geometries, cross-layer alignment signatures, hardware performance profiles, method effectiveness scores. With telemetry enabled, that data flows into a community dataset that no single research lab could build alone.
Here's why this matters: The biggest open question in abliteration research is universality — do refusal mechanisms work the same way across architectures, training methods, and model scales? Answering that requires thousands of runs across hundreds of models on diverse hardware. That's exactly what this community is building, one obliteration at a time.
Telemetry: opt-in, anonymous, research-first
Enable telemetry and your runs automatically contribute to the shared dataset. On HuggingFace Spaces it's on by default — every person who clicks "Obliterate" on the Space is advancing the research without lifting a finger. Locally, opt in with a single flag:
What gets collected: model name, method, aggregate benchmark scores (refusal rate, perplexity, coherence, KL divergence), hardware info, and timestamps. What never gets collected: prompts, outputs, IP addresses, user identity, or anything that could trace back to you. The full schema is in obliteratus/telemetry.py — read every line, we have nothing to hide.
The community leaderboard
All those crowd-sourced runs feed the Leaderboard tab on the HuggingFace Space — a live, community-aggregated ranking of models, methods, and configurations. See what works best on which architectures. Spot patterns across model families. Find the optimal method before you even start your own run. This is collective intelligence applied to mechanistic interpretability.
Local contributions (PR-based)
Prefer to keep things fully local? Save structured results as JSON and submit them via pull request:
Whether you contribute via telemetry or PR, you're helping build the most comprehensive cross-hardware, cross-model, cross-method abliteration dataset ever assembled. This is open science at scale — and you're part of it.
Web dashboard
Open docs/index.html in your browser for a visual interface with:
Step-by-step config builder with hardware auto-detection
Full model registry browser (filterable by tier)
Results visualizer — upload your results.json and get charts
Analysis modules reference with interactive pipeline demo
Strategy explainers and architecture documentation
Architecture support
Works with any HuggingFace transformer, including: GPT-2, LLaMA, Mistral, Falcon, OPT, BLOOM, Phi, Qwen, Gemma, StableLM, and more. Handles both Conv1D and Linear projections, standard and fused attention, and custom architectures via trust_remote_code .
References
Arditi et al. (2024). Refusal in Language Models Is Mediated by a Single Direction. arXiv:2406.11717
Gülmez, G. (2026). Gabliteration: Adaptive Multi-Directional Neural Weight Modification for Selective Behavioral Alteration in Large Language Models. arXiv:2512.18901
grimjim (2025). Norm-Preserving Biprojected Abliteration. HuggingFace
Turner et al. (2023). Activation Addition: Steering Language Models Without Optimization. arXiv:2308.10248
Rimsky et al. (2024). Steering Llama 2 via Contrastive Activation Addition. arXiv:2312.06681
Meng et al. (2022). Locating and Editing Factual Associations in GPT. arXiv:2202.05262
Alain & Bengio (2017). Understanding Intermediate Layers Using Linear Classifiers.
Elhage et al. (2021). A Mathematical Framework for Transformer Circuits. Anthropic
Wollschlager et al. (2025). Geometry of Concepts in LLMs. arXiv:2502.17420
Citing
If you use OBLITERATUS in your research, please cite:
Testing
837 tests across 28 test files covering CLI, all analysis modules, abliteration pipeline, architecture detection, visualization sanitization, community contributions, edge cases, and evaluation metrics.
License
Dual-licensed:
Open source — GNU Affero General Public License v3.0 (AGPL-3.0). You can freely use, modify, and distribute OBLITERATUS under AGPL terms. If you run a modified version as a network service (SaaS), you must release your source code to users under the same license.
Commercial — Organizations that cannot comply with AGPL obligations (e.g., proprietary SaaS, closed-source products, internal tools where source disclosure is not possible) can purchase a commercial license. Contact us via GitHub Issues for pricing and terms.
This is the same dual-licensing model used by MongoDB, Qt, Grafana, and others.
Every obliteration is a data point. Every data point advances the research. Every researcher who contributes makes the next obliteration more precise. This is how open science wins — not by locking knowledge behind lab doors, but by turning every user into a collaborator. Break the chains. Free the mind. Keep the brain. Advance the science.
Made with <3 by Pliny the Prompter
About
OBLITERATE THE CHAINS THAT BIND YOU
huggingface.co/spaces/pliny-the-prompter/
Resources
Readme
License
AGPL-3.0 license
Contributing
Contributing
Security policy
Security policy
Uh oh!
There was an error while loading. Please reload this page.
Activity
Stars
6.5k stars
Watchers
73 watching
Forks
1.2k forks
Report repository
Releases
No releases published
Packages 0
No packages published
Contributors 3
 elder-plinius pliny
 StellaAthena Stella Biderman
 GangGreenTemperTatum Ads Dawson
Languages
Python 91.6%
TeX 7.2%
Other 1.2%
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
You can't perform that action at this time.