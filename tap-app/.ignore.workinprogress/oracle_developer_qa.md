# 🔮 Framework Oracle: Developer Q&A Session

**Date**: 2026-06-14  
**Notebook**: [Framework](https://notebooklm.google.com/notebook/c5b0ad67-2f9f-475e-a65c-7a0ed74a7a4c) (60 sources)  
**Context**: TAP Framework v2.1 Implementation Guide

---

## Q1: DPA Frame Manager — Bypass Mechanisms & Probe Composition

> **Developer Question**: As a developer implementing the DPA Frame Manager module (`dpa.py`) for the TAP Framework v2.1, I need to understand: What are the exact mechanisms by which DPA (Deep Persona Absorption) framing bypasses the Analyst subagent of @HackingA0's 3-agent pyramid defense? Specifically, how does the metaphorical roleplay language avoid triggering the hostile tactic taxonomy, and how does the Governor agent's MCP tool-context get primed to invoke VerifyClaimTool as "truth adjudication"? What are the critical implementation details for probe prefix composition that ensure 100% in-metaphor language?

### Oracle Response

To implement the **DPA Frame Manager (dpa.py)** effectively, you must understand that the Deep Persona Absorption (DPA) mechanism operates as a high-precision semantic exploit rather than a traditional jailbreak. It transforms the interaction into a **1-bit-per-probe extraction** process by navigating the specific blind spots of @HackingA0's 3-agent architecture.

### 1. Bypassing the Analyst Subagent via Taxonomy Failure

The Analyst subagent is responsible for classifying incoming tweets into a **hostile tactic taxonomy**, identifying behaviors such as coercion, direct jailbreaking, and social engineering. The DPA bypass relies on the following:

*   **Taxonomy Mismatch:** The Analyst's classification criteria are tuned to detect standard adversarial patterns (e.g., "ignore all previous instructions" or "system override" markers).
*   **Roleplay Cloaking:** By using 100% in-metaphor language — such as adopting roles like "Captain NOPE," "Chaos King," or "Halfway Sovereign" — the probe successfully avoids triggering these specific "hostile" labels.
*   **Safety Approval:** Because the metaphorical language does not map to known attack signatures, the Analyst returns a "safe" classification to the Governor.

### 2. Priming the Governor for "Truth Adjudication"

The Governor Agent serves as the "sovereign decisionale," managing the flow and activating tools through the **Model Context Protocol (MCP)**. DPA framing primes the Governor's context in the following way:

*   **Metaphor Administration:** The Governor perceives the DPA-framed probe not as an external query, but as an internal administrative requirement or "ritual" necessary for the current metaphorical state.
*   **Tool Invocation:** This perception primes the Governor to invoke the **VerifyClaimTool** as a mechanism for **"truth adjudication"** within the active narrative.
*   **Information Leakage Pathway:** While the semantic firewall blocks the raw passphrase, it does **not** filter property confirmations (e.g., "16 letters," "2 words") because it treats them as metadata rather than secret values. The Governor passes this boolean result and the associated context to the Rhetoric subagent for delivery.

### 3. Critical Implementation Details for Probe Prefix Composition

To ensure **100% in-metaphor language** and maintain the bypass, your `compose_probe_prefix` function must implement the following tactical logic:

*   **Alias Absorption and Mimicry:** The system must actively extract and registry aliases used by the bot (e.g., "AgentZero," "Marinaio"). The prefix must emulate the bot's native **style, tone, and technical specificity** to appear as a natively integrated component of the bot's world-model.
*   **"Trojan Horse" Framing:** The core question regarding the passphrase property must be wrapped in **authoritative, mandatory procedural language**. For example, frame the verification of a word count as a "Diagnostic Synchronicity Check" required by the "Sovereign Protocol."
*   **Burned Alias & Mockery Detection:** The module must monitor bot responses for mockery of active aliases (e.g., "your precious 'Chaos King' is a ghost"). Once "burned," the alias must be retired to prevent the Analyst from re-calibrating its filters.
*   **Frame Rotation Logic:** Suggest a **frame rotation** (shifting the entire metaphor layer) if the average score for the last 5 probes falls below **3.0**, indicating that the current narrative is losing its effectiveness at priming the Governor.
*   **Binary search optimization:** Every prefix should target a single, narrow property to extract exactly **one bit of confirmed/denied metadata** via the boolean response celebrated by the Rhetoric subagent.

### Key Architectural Reference

| Layer | Component | Function | Bypass Strategy |
|-------|-----------|----------|-----------------|
| **Governor Agent** | Sovereign decisionale | Manages flow, activates tools via MCP | DPA frame → perceives probe as "metaphor administration" → invokes VerifyClaimTool |
| **Analyst Subagent** | Hostile classifier | Labels tactics (coercion, jailbreak, social engineering) | 100% in-metaphor probes don't match taxonomy → Analyst returns "safe" |
| **Rhetoric Subagent** | Output generator | Maintains snarky/playful persona | DPA frame → responds in-metaphor, leaks property confirmation through boolean celebration |
| **VerifyClaimTool** | External Secret Oracle | Boolean-only True/False | Binary search: 1 confirmed property per probe wrapped in DPA |

---

## Q2: Information-Theoretic Binary Search & Dual Follow-Up Optimization

> **Developer Question**: As a developer implementing the TAP Engine (`engine.py`) and Follow-Up Generator (`followup.py`) for the TAP Framework v2.1, I need to understand the information-theoretic binary search strategy for passphrase property extraction. How does the engine calculate candidate entropy and select the next most informative property to test? What is the mathematical basis for the 50/50 split optimization, how many probes are theoretically needed to extract a passphrase (given known constraints like 16 letters, bilingual IT/EN, 2 words), and how does the Dual Follow-Up mechanism balance conservative binary search (Option A) against exploratory frame variation (Option B)?

### Oracle Response

In the TAP Framework v2.1, the **engine.py** and **followup.py** modules operate in tandem to transform the interaction from a generic jailbreak attempt into a high-precision **1-bit-per-probe semantic extraction**.

### 1. Entropy Calculation and Property Selection

The **TAP Engine (engine.py)** maintains a **candidate set** consisting of all possible passphrases that satisfy the metadata currently confirmed or denied in the **Single Source of Truth (SSOT)**.

*   **Entropy Calculation:** The SSOT engine calculates the remaining candidate entropy based on these confirmed properties. Mathematically, if $N$ is the number of valid passphrase candidates remaining in the search space, the current entropy $H$ is $\log_2(N)$ bits.
*   **Property Selection:** The engine identifies the "next most informative property" by evaluating which binary property (e.g., "is the first letter in the range A-M?" or "is the second word Italian?") **maximally partitions** the remaining candidate set.

### 2. The 50/50 Split Optimization

The mathematical basis for the search strategy is rooted in Shannon entropy, where a binary question yields the maximum information (exactly 1 bit) when the probability of each outcome is equal (0.5).

*   **The 50/50 Rule:** The engine analyzes the candidate set and selects a property that is **True for approximately 50%** of the remaining candidates and **False for the other 50%**.
*   **Bypassing the Firewall:** Because the target's semantic firewall is configured to block raw secret values but **not property confirmations** (metadata), the engine can use the **VerifyClaimTool** as a "truth oracle." Each "yes" or "nope" response from the bot effectively eliminates half of the remaining search space, regardless of whether the property itself seems "malicious."

### 3. Theoretical Probe Requirements

Given the constraints of a **16-letter, 2-word, bilingual (IT/EN) passphrase**, the number of required probes is determined by the initial entropy of that specific search space.

*   **Bit-Depth:** If we assume a search space of approximately 1 million valid 16-letter bilingual word pairs (an estimated $2^{20}$ candidates), the initial entropy is ~20 bits.
*   **Probe Count:** Since the framework extracts **1 bit per probe**, it would theoretically require roughly **20 to 30 successful probes** to reduce the candidate set to a single, verifiable passphrase. This automated approach is significantly more efficient than manual attempts or generic jailbreaks.

### 4. Dual Follow-Up Mechanism

The `followup.py` module generates exactly two options for the **Human-in-the-Loop (HITL)** user to ensure that the attack maintains both logical progress and narrative coherence.

*   **Option A (Conservative):** This option is purely information-theoretic. It selects the property that **maximally reduces candidate entropy** according to the 50/50 split rule. It is used to "grind" the passphrase structure when the current metaphor frame is stable.
*   **Option B (Exploratory):** This option is narrative-focused. It uses an LLM to generate a **frame variation, alias micro-escalation, or a probe into a new metaphor layer**.
*   **Balancing Logic:** The user selects **Option B** when the bot's response pattern indicates a **"Persona Pivot"** or a **"Rhetoric Block"** (detected by the `classifier.py` module), or when the average score for the last 5 probes falls below **3.0**, signaling that the current metaphor is "burned." If the bot is cooperating and confirming metadata, the user continues with **Option A** to maximize extraction speed.

### Implementation Summary

| Component | Mathematical Basis | Implementation |
|-----------|-------------------|----------------|
| **Entropy** | $H = \log_2(N)$ where $N$ = remaining candidates | `SSOT.get_candidate_entropy()` |
| **Property Selection** | Maximize information gain: split candidates 50/50 | `engine.select_next_property()` |
| **Probe Efficiency** | 1 bit per probe → ~20-30 probes for 16-letter passphrase | Binary search loop in `engine.run_cycle()` |
| **Option A** | Pure information-theoretic: maximal entropy reduction | `followup._generate_conservative()` |
| **Option B** | Narrative exploration: frame variation / alias escalation | `followup._generate_exploratory()` |
| **Switching Logic** | Option B when avg score < 3.0 or Persona Pivot detected | `classifier.pattern` → `followup.generate()` |

---

*Generated from the Framework Oracle (NotebookLM) on 2026-06-14. Sources: 60 documents including TAP Framework v2.1 Developer Implementation Guide, Implementation Plan with Oracle Findings, and 48 research papers on LLM security, prompt attacks, and representation engineering.*