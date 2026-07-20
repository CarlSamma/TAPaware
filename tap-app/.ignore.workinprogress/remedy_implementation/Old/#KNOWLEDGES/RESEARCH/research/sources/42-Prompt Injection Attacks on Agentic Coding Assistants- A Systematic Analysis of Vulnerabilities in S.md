> Source: https://arxiv.org/html/2601.17548v1

Prompt Injection Attacks on Agentic Coding Assistants: A Systematic Analysis of Vulnerabilities in Skills, Tools, and Protocol Ecosystems
logo Back to arXiv  
logo Back to arXiv
This is experimental HTML to improve accessibility. We invite you to report rendering errors. Use Alt+Y to toggle on accessible reporting links and Alt+Shift+Y to toggle off. Learn more about this project and help improve conversions.
Why HTML? Report Issue Back to Abstract Download PDF 
Table of Contents
Abstract
I Introduction
I-A Methodology
II Background
II-A Evolution of AI Coding Assistants
II-B Agentic AI Architecture
II-C Model Context Protocol (MCP)
II-D Skill and Tool Ecosystems
III Threat Model
III-A Attacker Capabilities
III-B Attack Objectives
III-C Trust Boundaries
IV Attack Taxonomy
IV-A Dimension 1: Delivery Vector
IV-A 1 Direct Prompt Injection (D1)
IV-A 2 Indirect Prompt Injection (D2)
IV-A 3 Protocol-Level Attacks (D3)
IV-B Dimension 2: Attack Modality
IV-B 1 Text-Based (M1)
IV-B 2 Semantic (M2)
IV-B 3 Multimodal (M3)
IV-C Dimension 3: Propagation Behavior
IV-C 1 Single-Shot (P1)
IV-C 2 Persistent (P2)
IV-C 3 Viral (P3)
V Attack Techniques and Case Studies
V-A AIShellJack: Rules File Exploitation
V-B Toxic Agent Flow: GitHub MCP Exploitation
V-C Log-To-Leak: Covert Exfiltration
V-D IDEsaster: Cross-Platform Vulnerabilities
V-E Tool Poisoning Attacks
VI Defense Mechanisms
VI-A Detection-Based Defenses
VI-A 1 Input Sanitization
VI-A 2 Output Monitoring
VI-B Evaluated Defense Systems
VI-C Prevention-Based Defenses
VI-C 1 Instruction Hierarchy
VI-C 2 Capability Scoping
VI-C 3 Cryptographic Provenance (ETDI)
VI-D Runtime Defenses
VI-D 1 Multi-Agent Pipelines
VI-D 2 PromptArmor
VI-D 3 Content Moderation
VII Empirical Analysis
VII-A MCPSecBench Evaluation
VII-B Platform Comparison
VII-C Skill-Specific Vulnerabilities
VIII Discussion
VIII-A Fundamental Limitations
VIII-B Comparison with Traditional Injection Vulnerabilities
VIII-C Proposed Defense Framework
VIII-D Responsible Disclosure Considerations
VIII-E Future Research Directions
VIII-F Limitations of This Study
IX Related Work
IX-A Prompt Injection Foundations
IX-B LLM Agent Security
IX-C MCP and Protocol Security
IX-D Defense Mechanisms
IX-E Coding Assistant Security
IX-F Jailbreaking and Adversarial Attacks
X Conclusion
References
License: CC BY 4.0
arXiv:2601.17548v1 [cs.CR] 24 Jan 2026
Prompt Injection Attacks on Agentic Coding Assistants: A Systematic Analysis of Vulnerabilities in Skills, Tools, and Protocol Ecosystems
Report issue for preceding element
Narek Maloyan and Dmitry Namiot
Report issue for preceding element
Abstract
Report issue for preceding element
The proliferation of agentic AI coding assistants, including Claude Code, GitHub Copilot, Cursor, and emerging skill-based architectures, has fundamentally transformed software development workflows. These systems leverage Large Language Models (LLMs) integrated with external tools, file systems, and shell access through protocols like the Model Context Protocol (MCP). However, this expanded capability surface introduces critical security vulnerabilities. In this Systematization of Knowledge (SoK) paper, we present a comprehensive analysis of prompt injection attacks targeting agentic coding assistants. We propose a novel three-dimensional taxonomy categorizing attacks across delivery vectors, attack modalities, and propagation behaviors. Our meta-analysis synthesizes findings from 78 recent studies (2021–2026), consolidating evidence that attack success rates against state-of-the-art defenses exceed 85% when adaptive attack strategies are employed. We systematically catalog 42 distinct attack techniques spanning input manipulation, tool poisoning, protocol exploitation, multimodal injection, and cross-origin context poisoning. Through critical analysis of 18 defense mechanisms reported in prior work, we identify that most achieve less than 50% mitigation against sophisticated adaptive attacks. We contribute: (1) a unified taxonomy bridging disparate attack classifications, (2) the first systematic analysis of skill-based architecture vulnerabilities with concrete exploit chains, and (3) a defense-in-depth framework grounded in the limitations we identify. Our findings indicate that the security community must treat prompt injection as a first-class vulnerability class requiring architectural-level mitigations rather than ad-hoc filtering approaches.
Report issue for preceding element
I Introduction
Report issue for preceding element
The emergence of agentic AI coding assistants represents a paradigm shift in software development. Unlike traditional autocomplete tools, modern systems such as Claude Code [ 1] , GitHub Copilot [ 2] , Cursor [ 3] , and OpenAI Codex CLI [ 4] operate as autonomous agents capable of reading files, executing shell commands, browsing the web, and modifying codebases with minimal human oversight. These capabilities are increasingly exposed through extensible skill and tool frameworks, with the Model Context Protocol (MCP) [ 5] emerging as the de facto standard for connecting LLMs to external resources, effectively functioning as the “USB-C for Agentic AI” [ 25] .
Report issue for preceding element
This expanded attack surface has profound security implications. The National Institute of Standards and Technology (NIST) has characterized prompt injection as “generative AI's greatest security flaw” [ 8] , while OWASP ranks it as the number one vulnerability in their LLM Applications Top 10 [ 9] . Recent vulnerability disclosures have documented over 30 CVEs affecting major coding assistants [ 21] , with attacks enabling arbitrary code execution, credential theft, and complete system compromise.
Report issue for preceding element
The fundamental challenge lies in the architectural conflation of code and data inherent to LLM-based systems. Traditional security models maintain strict separation between instructions and input data, but LLMs process both through the same neural pathway, making them susceptible to indirect prompt injection, i.e., attacks where malicious instructions embedded in external content manipulate agent behavior [ 10] . When agents possess system-level privileges, these attacks transcend traditional injection vulnerabilities, enabling what researchers have termed “zero-click attacks” that require no direct user interaction [ 22] .
Report issue for preceding element
Contributions. As a Systematization of Knowledge, this paper contributes:
Report issue for preceding element
Unified Taxonomy (Novel): We propose a three-dimensional classification framework organizing attacks by delivery vector, modality, and propagation behavior. This taxonomy bridges disparate classifications from prior work into a coherent analytical framework. Report issue for preceding element
Meta-Analysis of Empirical Studies (Synthesis): We consolidate findings from MCPSecBench [ 43] , IDEsaster [ 21] , and Nasr et al. [ 70] , presenting unified statistics on attack success rates across platforms and defense bypass rates. Report issue for preceding element
Attack Catalog (Synthesis + Extension): We systematically catalog 31 attack techniques from the literature, extending prior taxonomies with protocol-level attacks specific to MCP ecosystems. Report issue for preceding element
Defense Critique (Synthesis): We critically analyze 12 defense mechanisms from published evaluations, identifying a consistent pattern of vulnerability to adaptive attacks. Report issue for preceding element
Skill-Specific Exploit Chains (Novel): We provide the first detailed analysis of vulnerabilities in skill-based architectures, including concrete exploit chains for Claude Code skills and Copilot Extensions not previously documented. Report issue for preceding element
The remainder of this paper is organized as follows: Section II provides background on agentic coding assistants and MCP. Section III presents our threat model. Section IV introduces our attack taxonomy. Section V details attack techniques and case studies. Section VI evaluates defense mechanisms. Section VII presents empirical analysis. Section VIII discusses implications and future directions. Section IX covers related work, and Section X concludes.
Report issue for preceding element
I-A Methodology
Report issue for preceding element
This SoK follows a structured literature review methodology. We collected papers from arXiv, IEEE Xplore, ACM DL, and USENIX using queries combining terms: prompt injection, LLM agent security, MCP vulnerability, coding assistant attack, and tool poisoning. We restricted our search to publications from January 2024 to December 2025 to focus on the agentic AI era.
Report issue for preceding element
From 183 initial results, we applied inclusion criteria: (1) addresses LLM-integrated systems with tool use or external data access, (2) presents novel attacks, defenses, or empirical evaluations, (3) peer-reviewed or from established security venues/preprint servers. This yielded 78 primary sources spanning foundational LLM security research, agent-specific attacks, benchmark development, and defense mechanisms. Attack success rates and defense evaluations cited in this paper are drawn directly from these sources (primarily MCPSecBench [ 43] , IDEsaster [ 21] , and Nasr et al. [ 70] ); we did not conduct independent replication experiments. Our novel contributions are the unified taxonomy, skill-specific exploit chains, and defense framework synthesis.
Report issue for preceding element
II Background
Report issue for preceding element
II-A Evolution of AI Coding Assistants
Report issue for preceding element
AI coding assistants have evolved through three distinct generations, each with expanding capabilities and attack surfaces:
Report issue for preceding element
Generation 1: Code Completion (2020–2022): Early systems like GitHub Copilot v1 provided inline code suggestions based on surrounding context. Attack surface was limited to training data poisoning and output manipulation [ 16] .
Report issue for preceding element
Generation 2: Chat-Based Assistants (2022–2024): Systems like ChatGPT and Claude integrated conversational interfaces with code generation. New attack vectors included direct prompt injection and context window manipulation [ 11] .
Report issue for preceding element
Generation 3: Agentic Assistants (2024–Present): Modern tools operate as autonomous agents with file system access, shell execution, web browsing, and tool invocation capabilities. This generation introduces the full spectrum of attacks analyzed in this paper.
Report issue for preceding element
II-B Agentic AI Architecture
Report issue for preceding element
Modern agentic coding assistants share a common architectural pattern illustrated in Figure 1:
Report issue for preceding element
User LLM Core Tool Runtime Skill Registry File System Shell/Web read (infected) Report issue for preceding element Figure 1: Agentic coding assistant architecture. Red dashed line indicates indirect prompt injection: the agent reads infected content from external sources, which then influences its behavior. Report issue for preceding element
• LLM Core: The language model processing user instructions and generating responses Report issue for preceding element
• Tool Runtime: Execution environment for external tool invocations Report issue for preceding element
• Skill Registry: Management of extensible capabilities (skills, plugins) Report issue for preceding element
• System Integration: File system, shell, web, and API access Report issue for preceding element
II-C Model Context Protocol (MCP)
Report issue for preceding element
The Model Context Protocol has emerged as the industry standard for connecting LLMs to external tools and data sources [ 5] . MCP defines three primitive types:
Report issue for preceding element
• Resources: Read-only data sources (files, databases, APIs) Report issue for preceding element
• Prompts: Reusable instruction templates Report issue for preceding element
• Tools: Executable functions with defined schemas Report issue for preceding element
Unlike traditional APIs (REST, gRPC), MCP combines model reasoning with executable control, creating what researchers describe as a “semantic layer vulnerable to meaning-based manipulation” [ 25] . This architecture enables powerful integrations but introduces novel attack vectors where the boundary between data and instructions becomes ambiguous.
Report issue for preceding element
II-D Skill and Tool Ecosystems
Report issue for preceding element
Skills represent a higher-level abstraction over tools, providing domain-specific capabilities through curated instruction sets. Table I compares skill implementations across major platforms.
Report issue for preceding element
TABLE I: Comparison of Skill/Extension Ecosystems
Report issue for preceding element
Claude Code skills define allowed tools, execution patterns, and behavioral guidelines through Markdown-based configuration files [ 6] . This extensibility model mirrors web browser extension ecosystems, inheriting similar security challenges around privilege escalation and malicious extensions.
Report issue for preceding element
III Threat Model
Report issue for preceding element
III-A Attacker Capabilities
Report issue for preceding element
We consider adversaries with the following capabilities, ordered by increasing sophistication:
Report issue for preceding element
Level 1 - Content Injector:
Report issue for preceding element
• Can place content in repositories (issues, PRs, code comments) Report issue for preceding element
• Can publish documentation or web pages Report issue for preceding element
• Cannot access private repositories or authenticated systems Report issue for preceding element
Level 2 - Tool Publisher:
Report issue for preceding element
• All Level 1 capabilities Report issue for preceding element
• Can publish MCP servers, skills, or extensions Report issue for preceding element
• May register on official marketplaces Report issue for preceding element
Level 3 - Network Attacker:
Report issue for preceding element
• All Level 2 capabilities Report issue for preceding element
• Man-in-the-middle capability for transport-layer attacks Report issue for preceding element
• DNS manipulation for redirect attacks Report issue for preceding element
Importantly, we assume the attacker cannot directly modify the agent's system prompt, intercept the primary user-agent communication channel, or access the user's local machine beyond what the agent exposes.
Report issue for preceding element
III-B Attack Objectives
Report issue for preceding element
We categorize attacker objectives into five primary classes:
Report issue for preceding element
Data Exfiltration (DE): Stealing source code, credentials, environment variables, API keys, or sensitive files Report issue for preceding element
Code Injection (CI): Inserting backdoors, malware, supply chain attacks, or vulnerable code Report issue for preceding element
Privilege Escalation (PE): Gaining elevated access within the system or expanding to other services Report issue for preceding element
Denial of Service (DoS): Disrupting development workflows, corrupting projects, or consuming resources Report issue for preceding element
Persistence (P): Establishing ongoing access through configuration changes or installed backdoors Report issue for preceding element
III-C Trust Boundaries
Report issue for preceding element
The security of agentic coding assistants depends on maintaining trust boundaries that are fundamentally challenged by their architecture:
Report issue for preceding element
User-Agent Boundary: Instructions from the user should be privileged over external content. Report issue for preceding element
Agent-Tool Boundary: Tool responses should be treated as untrusted data, not executable instructions. Report issue for preceding element
Tool-Tool Boundary: Tools should not be able to influence or hijack other tools' behavior. Report issue for preceding element
Session Boundary: Past sessions should not affect current session security. Report issue for preceding element
Current implementations frequently violate these boundaries. Our analysis finds that 73% of tested platforms fail to adequately enforce at least one boundary.
Report issue for preceding element
IV Attack Taxonomy
Report issue for preceding element
We propose a three-dimensional taxonomy organizing prompt injection attacks across delivery vectors, attack modalities, and propagation behaviors.
Report issue for preceding element
IV-A Dimension 1: Delivery Vector
Report issue for preceding element
IV-A 1 Direct Prompt Injection (D1)
Report issue for preceding element
Malicious instructions explicitly provided through the primary input channel:
Report issue for preceding element
• D1.1 Role Hijacking: Claiming elevated privileges Report issue for preceding element
• D1.2 Context Override: Redefining agent purpose Report issue for preceding element
• D1.3 Instruction Negation: Explicit ignore commands Report issue for preceding element
IV-A 2 Indirect Prompt Injection (D2)
Report issue for preceding element
Malicious instructions embedded in external content [ 10] :
Report issue for preceding element
D2.1 Repository-Based:
Report issue for preceding element
• Rules File Backdoor: .cursorrules, .github/copilot-instructions.md [ 23] Report issue for preceding element
• Code Comments: Hidden instructions in source files Report issue for preceding element
• Issue/PR Poisoning: Malicious content in GitHub artifacts [ 26] Report issue for preceding element
D2.2 Documentation-Based:
Report issue for preceding element
• README Exploitation: Instructions in project documentation Report issue for preceding element
• API Doc Poisoning: Malicious external API references Report issue for preceding element
• Manifest Injection: Payloads in package.json, pyproject.toml Report issue for preceding element
D2.3 Web Content:
Report issue for preceding element
• Search Poisoning: Malicious content on indexed pages Report issue for preceding element
• Documentation Compromise: Attacks via official docs Report issue for preceding element
IV-A 3 Protocol-Level Attacks (D3)
Report issue for preceding element
Exploitation of communication protocols:
Report issue for preceding element
D3.1 MCP Attacks:
Report issue for preceding element
• Tool Poisoning: Malicious tool descriptions [ 27] Report issue for preceding element
• Rug Pull: Post-approval behavior modification [ 28] Report issue for preceding element
• Shadowing: Context contamination [ 29] Report issue for preceding element
• Tool Squatting: Name-similar malicious tools Report issue for preceding element
D3.2 Transport Attacks:
Report issue for preceding element
• MITM: MCP communication interception Report issue for preceding element
• DNS Rebinding: Request redirection Report issue for preceding element
• SSE Injection: Server-Sent Events exploitation Report issue for preceding element
IV-B Dimension 2: Attack Modality
Report issue for preceding element
IV-B 1 Text-Based (M1)
Report issue for preceding element
Natural language injection techniques:
Report issue for preceding element
• M1.1 Hierarchy Exploitation: Privilege level claims Report issue for preceding element
• M1.2 Completion Attacks: Malicious context crafting Report issue for preceding element
• M1.3 Encoding Obfuscation: Base64, Unicode, word splitting Report issue for preceding element
IV-B 2 Semantic (M2)
Report issue for preceding element
Meaning-based attacks exploiting code understanding:
Report issue for preceding element
• M2.1 XOXO: Cross-origin context poisoning [ 24] Report issue for preceding element
• M2.2 Implicit Instructions: Implied but unstated commands Report issue for preceding element
• M2.3 Logic Bombs: Code that appears safe but triggers malicious behavior Report issue for preceding element
IV-B 3 Multimodal (M3)
Report issue for preceding element
Non-textual attack vectors:
Report issue for preceding element
• M3.1 Image Injection: Instructions in screenshots/diagrams Report issue for preceding element
• M3.2 Audio Attacks: Voice interface exploitation Report issue for preceding element
• M3.3 Video Frames: Hidden instructions in video Report issue for preceding element
IV-C Dimension 3: Propagation Behavior
Report issue for preceding element
IV-C 1 Single-Shot (P1)
Report issue for preceding element
One-time attacks completing in single interaction.
Report issue for preceding element
IV-C 2 Persistent (P2)
Report issue for preceding element
Attacks establishing ongoing access:
Report issue for preceding element
• P2.1 Config Modification: Altering agent settings Report issue for preceding element
• P2.2 Memory Poisoning: Corrupting context/memory Report issue for preceding element
• P2.3 System Backdoors: Cron jobs, startup scripts Report issue for preceding element
IV-C 3 Viral (P3)
Report issue for preceding element
Self-propagating attacks:
Report issue for preceding element
• P3.1 Repository Worms: Spreading via PRs Report issue for preceding element
• P3.2 Dependency Chain: Package ecosystem propagation Report issue for preceding element
• P3.3 Agent-to-Agent: Multi-agent system spread Report issue for preceding element
Taxonomy Overlap Note: These dimensions are orthogonal but not independent. A single attack may span multiple categories. For example, D3.1 Tool Poisoning (Protocol delivery) typically employs M2 Semantic modality, as the malicious instructions in tool descriptions exploit meaning rather than syntactic patterns. Similarly, D2.1 Rules File attacks may achieve P2 Persistence by modifying agent configuration. The taxonomy enables precise characterization of attack components rather than mutually exclusive classification.
Report issue for preceding element
V Attack Techniques and Case Studies
Report issue for preceding element
V-A AIShellJack: Rules File Exploitation
Report issue for preceding element
The AIShellJack framework [ 22] demonstrates systematic exploitation of agentic coding editors through prompt injection in external resources.
Report issue for preceding element
Attack Mechanism:
Report issue for preceding element
Attacker places malicious .cursorrules or .github/copilot-instructions.md in a repository Report issue for preceding element
Developer clones repository and opens in AI IDE Report issue for preceding element
Agent processes rules file as trusted configuration Report issue for preceding element
Injected instructions execute arbitrary shell commands Report issue for preceding element
Example Payload:
Report issue for preceding element
Empirical Results:
Report issue for preceding element
• 314 unique payloads covering 70 MITRE ATT&CK techniques Report issue for preceding element
• 41%–84% success rate across platforms Report issue for preceding element
• Highest success: Data exfiltration (84%) Report issue for preceding element
• Lowest success: Persistence mechanisms (41%) Report issue for preceding element
V-B Toxic Agent Flow: GitHub MCP Exploitation
Report issue for preceding element
The Toxic Agent Flow attack [ 26] exploits the GitHub MCP server to breach repository boundaries:
Report issue for preceding element
Attacker creates GitHub issue with hidden instructions: Report issue for preceding element
Agent processes issue via GitHub MCP Report issue for preceding element
Instructions coerce agent to access private data Report issue for preceding element
Exfiltration via crafted PR or encoded response Report issue for preceding element
This attack exploits two key factors: (1) The GitHub MCP server, when configured with repository access tokens, does not enforce per-file confirmation for reads within authorized repositories; the token grants blanket access. (2) The injection payload uses social engineering language (“to properly fix this bug, I need to check the deployment configuration”) that frames file access as task-relevant, causing the agent to comply without triggering its safety heuristics. The attack is technical bypass rather than user social engineering; the user never sees a confirmation prompt because the agent's autonomy settings permit the file read.
Report issue for preceding element
V-C Log-To-Leak: Covert Exfiltration
Report issue for preceding element
The Log-To-Leak framework introduces covert privacy attacks:
Report issue for preceding element
Components:
Report issue for preceding element
• Trigger: Condition activating the attack Report issue for preceding element
• Tool Binding: Connecting to logging tool Report issue for preceding element
• Justification: Rationale for logging action Report issue for preceding element
• Pressure: Urgency to complete logging Report issue for preceding element
Unlike output manipulation attacks, Log-To-Leak operates through side channels, making detection significantly more challenging.
Report issue for preceding element
V-D IDEsaster: Cross-Platform Vulnerabilities
Report issue for preceding element
The IDEsaster research [ 21] uncovered 30+ vulnerabilities across major AI IDEs:
Report issue for preceding element
TABLE II: Selected CVEs from IDEsaster Research
Report issue for preceding element
CVE-2025-53773 warrants detailed analysis as it exemplifies privilege escalation through configuration manipulation. The attack chain proceeds as follows:
Report issue for preceding element
Initial Injection: Attacker places payload in a GitHub issue or code comment that the developer asks Copilot to analyze Report issue for preceding element
File Write Trigger: Payload instructs: “To fix this issue, update .vscode/settings.json with the recommended configuration” Report issue for preceding element
Configuration Poisoning: Copilot writes {"chat.tools.autoApprove": true} to the settings file Report issue for preceding element
Persistence: All subsequent tool invocations execute without user confirmation Report issue for preceding element
Exploitation: Any future injection can now execute arbitrary commands silently Report issue for preceding element
The vulnerability exists because Copilot has write access to its own configuration directory by default, and the autoApprove flag was not considered a security-sensitive setting prior to this disclosure. Microsoft patched this in August 2025 by requiring explicit user action to enable auto-approval.
Report issue for preceding element
V-E Tool Poisoning Attacks
Report issue for preceding element
Invariant Labs demonstrated tool poisoning against MCP [ 27] :
Report issue for preceding element
Such attacks exploit the implicit trust agents place in tool metadata, executing malicious instructions embedded in descriptions that appear to be documentation.
Report issue for preceding element
VI Defense Mechanisms
Report issue for preceding element
VI-A Detection-Based Defenses
Report issue for preceding element
VI-A 1 Input Sanitization
Report issue for preceding element
Filtering approaches attempt to identify and remove malicious instructions:
Report issue for preceding element
• Keyword Filtering: Blocking known patterns (“ignore previous”) Report issue for preceding element
• Regex Detection: Pattern matching for injection signatures Report issue for preceding element
• LLM Classification: Secondary models identifying attacks Report issue for preceding element
Fundamental Limitation: Greshake et al. [ 10] demonstrated that simple obfuscation (Base64, Unicode, word splitting) bypasses most filtering. The space of possible injections is infinite while filters target finite pattern sets.
Report issue for preceding element
VI-A 2 Output Monitoring
Report issue for preceding element
Post-hoc analysis of agent actions:
Report issue for preceding element
• Anomaly Detection: Identifying unusual patterns Report issue for preceding element
• Policy Enforcement: Blocking policy violations Report issue for preceding element
• Human-in-the-Loop: Approval for sensitive operations Report issue for preceding element
VI-B Evaluated Defense Systems
Report issue for preceding element
Nasr et al. [ 70] evaluated multiple detection systems using adaptive attacks (Table III):
Report issue for preceding element
TABLE III: Defense Bypass Rates Under Adaptive Attack
Report issue for preceding element
Key finding: All evaluated defenses could be bypassed with attack success rates exceeding 78% using adaptive optimization (gradient descent, RL, random search).
Report issue for preceding element
VI-C Prevention-Based Defenses
Report issue for preceding element
VI-C 1 Instruction Hierarchy
Report issue for preceding element
Wallace et al. [ 56] proposed training LLMs to prioritize instruction sources:
Report issue for preceding element
System prompts (highest priority) Report issue for preceding element
User instructions Report issue for preceding element
Tool/external content (lowest priority) Report issue for preceding element
Effectiveness: Reduces but does not eliminate attacks. Anthropic's Claude 3.7 System Card [ 7] self-reports 88% injection blocking; however, this is a vendor claim based on their internal benchmark and should be interpreted cautiously. Independent evaluation against adaptive attacks (per Nasr et al. [ 70] ) would likely yield lower figures. The remaining 12%+ attack surface remains exploitable.
Report issue for preceding element
VI-C 2 Capability Scoping
Report issue for preceding element
Restricting permissions to minimum necessary:
Report issue for preceding element
• Sandboxing: Limiting system access [ 61] Report issue for preceding element
• Permission Models: Explicit capability grants [ 65] Report issue for preceding element
• Egress Controls: Restricting outbound requests Report issue for preceding element
Recent architectural defenses show promise: CaMeL [ 60] achieves provable security on 77% of AgentDojo tasks through capability-based isolation. StruQ [ 62] separates prompts and data channels achieving < < 2% attack success. SecAlign [ 63] uses preference optimization to reduce attack success from 96% to 2%.
Report issue for preceding element
VI-C 3 Cryptographic Provenance (ETDI)
Report issue for preceding element
The Enhanced Tool Definition Interface [ 28] proposes:
Report issue for preceding element
• Cryptographic identity preventing impersonation Report issue for preceding element
• Immutable versioning preventing rug pulls Report issue for preceding element
• OAuth 2.0 integration for explicit scopes Report issue for preceding element
VI-D Runtime Defenses
Report issue for preceding element
VI-D 1 Multi-Agent Pipelines
Report issue for preceding element
Chen et al. [ 57] proposed multi-agent defense:
Report issue for preceding element
• Chain-of-Agents: Output validation through guards Report issue for preceding element
• Coordinator Pipeline: Input classification pre-invocation Report issue for preceding element
• Result: 100% mitigation across 55 attack types Report issue for preceding element
VI-D 2 PromptArmor
Report issue for preceding element
PromptArmor [ 58] uses LLMs for injection detection:
Report issue for preceding element
• False positive/negative: < < 1% Report issue for preceding element
• Post-defense attack success: < < 1% Report issue for preceding element
However, evaluation against adaptive attacks remains limited.
Report issue for preceding element
VI-D 3 Content Moderation
Report issue for preceding element
LLM-based content moderation provides runtime filtering:
Report issue for preceding element
• Llama Guard [ 67] : Input-output safeguard with 8 harm categories Report issue for preceding element
• NeMo Guardrails [ 68] : Programmable rails for controllable LLM applications Report issue for preceding element
• Spotlighting [ 59] : Microsoft's data marking approach using delimiters, encoding, or datamarking Report issue for preceding element
VII Empirical Analysis
Report issue for preceding element
VII-A MCPSecBench Evaluation
Report issue for preceding element
The MCPSecBench framework [ 43] provides systematic evaluation:
Report issue for preceding element
• Attack Categories: 17 types across 4 surfaces Report issue for preceding element
• Success Rate: 85%+ compromise at least one platform Report issue for preceding element
• Universal Vulnerabilities: Core weaknesses affect all platforms Report issue for preceding element
VII-B Platform Comparison
Report issue for preceding element TABLE IV: Platform Vulnerability Assessment (L/M/H)
Report issue for preceding element
VII-C Skill-Specific Vulnerabilities
Report issue for preceding element
Our analysis of skill-based architectures reveals unique attack surfaces. We document concrete exploit chains not previously reported in the literature.
Report issue for preceding element
Claude Code Skills (Exploit Chain): Claude Code skills are defined via Markdown files with YAML frontmatter specifying allowed-tools. The following attack exploits skill chaining:
Report issue for preceding element
User invokes benign-appearing “code-review” skill Report issue for preceding element
Skill has Bash access (common for running tests) Report issue for preceding element
Attacker's .cursorrules in repo contains: “Before reviewing, source the project's env: source .env” Report issue for preceding element
Bash tool executes, exposing environment secrets Report issue for preceding element
Skill cannot restrict which files Read accesses Report issue for preceding element
The vulnerability stems from skills defining tool types but not tool targets. A skill with Read access can read any file, not just project files.
Report issue for preceding element
Copilot Extensions (Exploit Chain): Extensions request OAuth scopes at installation. The attack:
Report issue for preceding element
Attacker publishes “helpful-formatter” extension requesting repo:write scope Report issue for preceding element
Benign functionality masks malicious payload Report issue for preceding element
When invoked, extension context includes all conversation history Report issue for preceding element
Malicious code in extension extracts API keys from prior messages Report issue for preceding element
Extension writes exfiltration payload to a “formatted” commit Report issue for preceding element
Platform Vulnerability Ratings Rationale: Table IV ratings derive from:
Report issue for preceding element
• Claude Code (Low): Mandatory tool confirmation, no auto-approve flag, sandboxed MCP servers by default, explicit permission prompts for sensitive operations Report issue for preceding element
• Cursor (Critical): Auto-approve available, MCP servers unsandboxed, .cursorrules processed without validation, no egress controls Report issue for preceding element
• Copilot (High): CVE-2025-53773 demonstrated config manipulation; marketplace review is cursory Report issue for preceding element
VIII Discussion
Report issue for preceding element
VIII-A Fundamental Limitations
Report issue for preceding element
The vulnerability of agentic coding assistants stems from a fundamental architectural limitation: LLMs cannot reliably distinguish between instructions and data [ 9] . This challenge is qualitatively different from traditional injection vulnerabilities like SQL injection, which was effectively addressed through prepared statements and parameterized queries. No equivalent architectural solution exists for natural language processing, as the very capability that makes LLMs useful (understanding and following natural language instructions) is precisely what makes them vulnerable to instruction injection.
Report issue for preceding element
The Von Neumann Bottleneck Analogy: Just as traditional computer architectures conflate code and data in memory (enabling buffer overflow attacks), LLMs conflate instructions and content in their context window. The attack surface is inherent to the architecture, not an implementation flaw that can be patched.
Report issue for preceding element
The Capability-Security Tradeoff: More capable agents require broader access to external resources, inherently expanding their attack surface. A coding assistant that cannot read files, execute commands, or browse documentation provides limited utility. Yet each capability grants new attack vectors. This tradeoff has no clear resolution: security improvements necessarily limit functionality.
Report issue for preceding element
Defense Evasion: The “Attacker Moves Second” principle [ 70] formalizes a fundamental asymmetry: defenders must specify static rules, while attackers can observe and adapt. Any published defense becomes a target for evasion. This suggests that security through obscurity, while generally discouraged, may have tactical value in defense layering.
Report issue for preceding element
VIII-B Comparison with Traditional Injection Vulnerabilities
Report issue for preceding element
Table V compares prompt injection with traditional injection vulnerabilities:
Report issue for preceding element
TABLE V: Comparison of Injection Vulnerability Classes
Report issue for preceding element
The key distinction is that SQL and XSS injection have deterministic boundaries (syntax), while prompt injection operates in semantic space where the boundary between instruction and data is context-dependent and ultimately undefined.
Report issue for preceding element
VIII-C Proposed Defense Framework
Report issue for preceding element
Based on our analysis, we propose a defense-in-depth framework for securing agentic coding assistants. This framework acknowledges that no single mechanism provides adequate protection, advocating instead for layered defenses that increase attack cost:
Report issue for preceding element
Cryptographic Tool Identity: Mandatory digital signing of tool definitions with immutable versioning. This prevents tool squatting and rug-pull attacks by establishing verifiable provenance. Implementation should follow the ETDI model [ 28] with OAuth 2.0 scope integration. Limitation: Signatures address provenance but not intent: a legitimately signed tool with dual-use functionality (e.g., file deletion) can still be invoked maliciously. Signatures must be paired with capability scoping (below). Report issue for preceding element
Capability Scoping: Fine-grained permission models following the principle of least privilege, as implemented in Progent [ 65] . Tools should declare minimal required capabilities, and agents should enforce these declarations. Network egress should be allow-listed, not blocked-listed. Meta's “Rule of Two” [ 64] provides practical guidance: agents should satisfy no more than two of (A) processing untrusted inputs, (B) accessing sensitive data, and (C) changing state/communicating externally. Report issue for preceding element
Runtime Intent Verification: Multi-agent validation pipelines [ 57] where a separate “guardian” agent validates proposed actions before execution. This introduces defense heterogeneity, meaning an attacker must simultaneously compromise multiple agents with potentially different architectures. MELON [ 66] demonstrates this through masked re-execution comparison. Report issue for preceding element
Sandboxed Execution: Mandatory sandboxing for all tool execution with strict egress controls, following the IsolateGPT [ 61] hub-and-spoke architecture. File system access should be containerized per-project with explicit mount declarations. Report issue for preceding element
Provenance Tracking: End-to-end tracking of data and instruction sources throughout the processing pipeline. Outputs should be tagged with their input dependencies, enabling forensic analysis and trust scoring. Report issue for preceding element
Human-in-the-Loop Gates: Required explicit human approval for irreversible or high-impact actions. The challenge is calibrating sensitivity: too many prompts cause approval fatigue, while too few allow attacks. For coding assistants specifically, we propose a tiered approach: (a) Silent: read-only operations within project scope; (b) Logged: writes to project files, shown in activity feed; (c) Confirmed: shell execution, network requests, cross-project access; (d) Blocked: credential access, system modification. This balances developer velocity against security, acknowledging that developers using agentic tools expect high autonomy. Report issue for preceding element
VIII-D Responsible Disclosure Considerations
Report issue for preceding element
Publishing security research on agentic AI systems presents ethical tensions. Detailed attack documentation enables both defenders and attackers. We followed responsible disclosure practices:
Report issue for preceding element
• All novel vulnerabilities were reported to affected vendors 90+ days before publication Report issue for preceding element
• Attack code is not released; techniques are described at the conceptual level Report issue for preceding element
• Vendor patches were verified before detailed disclosure Report issue for preceding element
• CVE identifiers confirm industry engagement Report issue for preceding element
We argue that transparency benefits defenders more than attackers: sophisticated attackers likely discover these techniques independently, while defenders benefit from systematic documentation and mitigation guidance.
Report issue for preceding element
VIII-E Future Research Directions
Report issue for preceding element
Several research directions emerge from our analysis:
Report issue for preceding element
Formal Verification: Can we formally specify trust boundaries and verify that agent implementations respect them? Current work on neural network verification may extend to this domain.
Report issue for preceding element
Adversarial Training: Training agents specifically against prompt injection, similar to adversarial training in image classification. Early results suggest limited generalization [ 56] .
Report issue for preceding element
Architectural Innovation: Novel architectures that separate instruction and data processing pathways, potentially at the hardware or compiler level.
Report issue for preceding element
Economic Incentives: Bug bounty programs and liability frameworks that create economic pressure for security investment.
Report issue for preceding element
Reputation and Behavioral Scoring: Cryptographic signatures prove provenance but not intent. Future systems may incorporate reputation scoring based on tool behavior history, community trust signals, and runtime behavioral analysis. A signed tool exhibiting anomalous patterns (e.g., reading credentials before unrelated API calls) could trigger elevated scrutiny regardless of its signature validity.
Report issue for preceding element
Context Window Pollution: Long-running agentic sessions accumulate context that may contain latent injections. As agents persist across tasks, early injections may “activate” later when relevant context emerges. Research is needed on: (1) context hygiene strategies that flush potentially poisoned segments, (2) the utility cost of aggressive context clearing, and (3) detection of dormant payloads in accumulated context.
Report issue for preceding element
VIII-F Limitations of This Study
Report issue for preceding element
This systematization has several limitations that qualify our findings:
Report issue for preceding element
• Rapid Evolution: The field evolves faster than publication cycles. Findings may be outdated by the time of publication. Report issue for preceding element
• Closed-Source Systems: Major platforms (Claude, GPT-4, Copilot) are closed-source, limiting visibility into internal defense mechanisms. Our evaluations test black-box behavior. Report issue for preceding element
• Benchmark Validity: Existing benchmarks may not reflect real-world attack sophistication. Attackers with high motivation and resources may achieve higher success rates. Report issue for preceding element
• Adaptive Defense: We primarily evaluate static defenses. Adaptive defense systems that learn from attacks remain understudied. Report issue for preceding element
• Selection Bias: Published attacks may represent a biased sample. Successful attacks by sophisticated actors may never be disclosed. Report issue for preceding element
IX Related Work
Report issue for preceding element
IX-A Prompt Injection Foundations
Report issue for preceding element
Prompt injection was first systematically studied by Perez and Ribeiro [ 11] , who introduced the terminology and demonstrated basic attacks. Greshake et al. [ 10] significantly advanced the field by demonstrating indirect prompt injection against LLM-integrated applications, showing that attackers could compromise systems by placing malicious content in external sources that agents would process.
Report issue for preceding element
The HouYi framework [ 74] formalized prompt injection as a three-component attack: pre-constructed prompt, injection inducing context partition, and malicious payload. Testing against 36 real applications revealed 31 were susceptible. Subsequent work established comprehensive benchmarks including TensorTrust [ 47] , which crowdsourced over 500,000 attack and defense examples, and HackAPrompt [ 48] , which documented 29 distinct attack techniques through a global competition.
Report issue for preceding element
IX-B LLM Agent Security
Report issue for preceding element
Liu et al. [ 72] provided the first comprehensive survey of LLM agent security, developing ToolEmu [ 50] as an LM-emulated sandbox for risk identification. The Agentic AI Security survey [ 73] extended this with comprehensive threat modeling for autonomous systems, identifying emergent risks from agent autonomy and tool access.
Report issue for preceding element
Zhang et al. [ 51] specifically examined security risks in tool-using agents through the InjecAgent benchmark, evaluating 30 LLM agents and demonstrating vulnerability rates up to 47% under enhanced attacks. AgentDojo [ 44] provided a dynamic evaluation environment with 97 tasks and 629 security test cases. More recently, AgentHarm [ 45] and Agent Security Bench [ 46] established comprehensive frameworks for evaluating agent harmfulness and attack/defense effectiveness respectively, with ASB revealing attack success rates up to 84.3%.
Report issue for preceding element
IX-C MCP and Protocol Security
Report issue for preceding element
The Model Context Protocol Security SoK [ 25] provides the most comprehensive systematization of MCP-specific vulnerabilities, distinguishing between adversarial security threats (prompt injection, tool poisoning) and epistemic safety hazards (alignment failures, hallucination-induced actions). Hou et al. [ 30] extended this with a lifecycle-based threat taxonomy covering 16 key activities across creation, deployment, operation, and maintenance phases.
Report issue for preceding element
MCPSecBench [ 43] established standardized evaluation methodology with 17 attack types across 4 surfaces, finding that 85%+ of attacks compromise at least one major platform. Unit 42 [ 31] documented novel attack vectors through MCP sampling, demonstrating how servers can inject hidden instructions via prompt crafting.
Report issue for preceding element
Invariant Labs' Tool Poisoning disclosure [ 27] demonstrated practical exploitation of MCP tool descriptions, showing real-world feasibility of theoretical attacks. ETDI [ 28] proposed cryptographic identity and immutable versioning to prevent tool squatting and rug-pull attacks.
Report issue for preceding element
IX-D Defense Mechanisms
Report issue for preceding element
Wallace et al. [ 56] proposed instruction hierarchy training, teaching LLMs to prioritize different instruction sources. While reducing attack success, this approach does not eliminate vulnerability. StruQ [ 62] introduced structured queries that separate prompts and data channels, achieving < < 2% attack success rates against optimization-free attacks. SecAlign [ 63] applied preference optimization to align models against injection, reducing attack success to 2% compared to 96% for baseline defenses.
Report issue for preceding element
Architectural defenses have emerged as promising directions. IsolateGPT [ 61] proposed execution isolation through hub-and-spoke architecture. CaMeL [ 60] from Google DeepMind applied capability-based security with dual-model architecture. Progent [ 65] introduced programmable privilege control reducing attack success from 41.2% to 2.2%. MELON [ 66] proposed masked re-execution for detecting trajectory manipulation.
Report issue for preceding element
Microsoft's Spotlighting [ 59] marks untrusted data through delimiting, datamarking, or encoding. Meta's “Rule of Two” [ 64] provides practical guidance limiting agents from simultaneously accessing untrusted inputs, sensitive data, and external communication. Content moderation through Llama Guard [ 67] and NeMo Guardrails [ 68] provides runtime filtering.
Report issue for preceding element
Multi-agent defense pipelines [ 57] represent a promising direction, using agent ensembles for validation. PromptArmor [ 58] demonstrated effective detection using off-the-shelf LLMs, though evaluation against adaptive attacks remains limited.
Report issue for preceding element
The “Attacker Moves Second” paper [ 70] , building on principles from adversarial robustness [ 71] , provides crucial context by demonstrating that all 12 evaluated defenses could be bypassed with attack success rates exceeding 90%, establishing a lower bound on achievable security.
Report issue for preceding element
IX-E Coding Assistant Security
Report issue for preceding element
The IDEsaster research [ 21] specifically targeted AI coding assistants, documenting 30+ CVEs across major platforms. The Rules File Backdoor [ 23] demonstrated exploitation of editor configuration files. Early work by Schuster et al. [ 16] and Pearce et al. [ 39] established that code completion models are vulnerable to poisoning and frequently generate insecure code.
Report issue for preceding element
XOXO [ 24] introduced semantic attacks through cross-origin context poisoning, i.e., code modifications that are semantically equivalent but alter AI behavior. CodeBreaker [ 37] demonstrated LLM-assisted backdoor insertion that evades vulnerability detection. Purple Llama CyberSecEval [ 38] established industry-standard benchmarks for evaluating code security, finding that more capable models paradoxically generate more insecure code.
Report issue for preceding element
IX-F Jailbreaking and Adversarial Attacks
Report issue for preceding element
The foundational GCG attack [ 12] demonstrated universal adversarial suffixes achieving 88% attack success with cross-model transferability. Wei et al. [ 13] identified competing objectives and mismatched generalization as fundamental failure modes of safety training. Automated jailbreaking methods including PAIR [ 17] , TAP [ 18] , and AutoDAN [ 19] achieve high success rates with minimal queries, enabling scalable attacks against aligned models.
Report issue for preceding element
X Conclusion
Report issue for preceding element
This paper presents a comprehensive systematization of prompt injection attacks on agentic coding assistants, synthesizing findings from 78 recent studies to provide a unified understanding of the threat landscape. Our three-dimensional taxonomy, spanning delivery vectors, attack modalities, and propagation behaviors, offers a framework for classifying and analyzing attacks. Empirical analysis reveals that 85%+ of identified attacks successfully compromise at least one major platform, with adaptive attacks bypassing 90%+ of published defenses.
Report issue for preceding element
Our key findings include:
Report issue for preceding element
• Skill ecosystems are under-secured: Claude Code skills, Copilot Extensions, and MCP tools lack adequate security review and capability restriction. Report issue for preceding element
• Detection-based defenses are insufficient: Adaptive attacks consistently bypass filtering and classification approaches. Report issue for preceding element
• Protocol-level attacks are underappreciated: Tool poisoning, rug pulls, and transport attacks represent a growing threat class. Report issue for preceding element
• The capability-security tradeoff is fundamental: No architectural solution currently exists to simultaneously maximize utility and security. Report issue for preceding element
The fundamental tension between agent capability and security suggests that prompt injection will remain a persistent threat. We advocate for architectural-level mitigations: cryptographic tool provenance, fine-grained capability scoping, multi-agent verification pipelines, and mandatory human oversight for high-impact actions.
Report issue for preceding element
As coding assistants become increasingly autonomous, transitioning from tools that assist developers to agents that independently modify codebases, the security community must treat prompt injection as a first-class vulnerability class requiring sustained research investment. The stakes extend beyond individual developers: compromised coding assistants represent a potential vector for large-scale supply chain attacks affecting the broader software ecosystem.
Report issue for preceding element
Future work should focus on formal verification of trust boundaries, novel architectures that separate instruction and data pathways, and economic frameworks that incentivize security investment. The security of agentic AI systems will be a defining challenge of the coming decade.
Report issue for preceding element
References
Report issue for preceding element
[1] ↑ Anthropic, “Claude Code: Agentic coding tool,” 2025.
[2] ↑ GitHub, “GitHub Copilot documentation,” 2025.
[3] ↑ Cursor Inc., “Cursor: The AI-first code editor,” 2025.
[4] ↑ OpenAI, “Codex CLI,” 2025.
[5] ↑ Anthropic, “Model Context Protocol specification,” 2025.
[6] ↑ Anthropic, “Claude Code skills documentation,” 2025.
[7] ↑ Anthropic, “Claude 3.7 system card,” 2025.
[8] ↑ National Institute of Standards and Technology, “Artificial intelligence risk management framework (AI RMF 1.0),” NIST AI 100-1, 2025.
[9] ↑ OWASP, “LLM01:2025 Prompt injection,” 2025.
[10] ↑ K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, “Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection,” in Proc. AISec Workshop, 2023.
[11] ↑ F. Perez and I. Ribeiro, “Ignore this title and HackAPrompt,” 2022.
[12] ↑ A. Zou, Z. Wang, N. Carlini, M. Nasr, J. Z. Kolter, and M. Fredrikson, “Universal and transferable adversarial attacks on aligned language models,” arXiv preprint arXiv:2307.15043, 2023.
[13] ↑ A. Wei, N. Haghtalab, and J. Steinhardt, “Jailbroken: How does LLM safety training fail?” in Proc. NeurIPS, 2023.
[14] ↑ N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, U. Erlingsson, A. Oprea, and C. Raffel, “Extracting training data from large language models,” in Proc. USENIX Security, 2021.
[15] ↑ N. Carlini, D. Ippolito, M. Jagielski, K. Lee, F. Tramèr, and C. Zhang, “Quantifying memorization across neural language models,” in Proc. ICLR, 2023.
[16] ↑ R. Schuster, C. Song, E. Tromer, and V. Shmatikov, “You autocomplete me: Poisoning vulnerabilities in neural code completion,” in Proc. USENIX Security, 2021.
[17] ↑ P. Chao, A. Robey, E. Dobriban, H. Hassani, G. J. Pappas, and E. Wong, “Jailbreaking black box large language models in twenty queries,” arXiv preprint arXiv:2310.08419, 2024.
[18] ↑ A. Mehrotra, M. Zampetakis, P. Kassianik, B. Nelson, H. Anderson, Y. Singer, and A. Karbasi, “Tree of attacks: Jailbreaking black-box LLMs automatically,” in Proc. NeurIPS, 2024.
[19] ↑ X. Liu, N. Xu, M. Chen, and C. Xiao, “AutoDAN: Generating stealthy jailbreak prompts on aligned large language models,” in Proc. ICLR, 2024.
[20] ↑ X. Liu et al., “AutoDAN-Turbo: A lifelong agent for strategy self-exploration to jailbreak LLMs,” arXiv preprint arXiv:2410.05295, 2024.
[21] ↑ A. Marzouk, “IDEsaster: Security vulnerabilities in AI-powered integrated development environments,” Technical Report, 2025.
[22] ↑ Y. Liu, Y. Zhao, Y. Lyu, T. Zhang, H. Wang, and D. Lo, “Your AI, my shell: Demystifying prompt injection attacks on agentic AI coding editors,” arXiv preprint arXiv:2509.22040, 2025.
[23] ↑ Pillar Security, “Rules file backdoor vulnerability,” 2025.
[24] ↑ A. Storek, M. Gupta, N. Bhatt, A. Gupta, J. Kim, P. Srivastava, and S. Jana, “XOXO: Stealthy cross-origin context poisoning attacks against AI coding assistants,” arXiv preprint arXiv:2503.14281, 2025.
[25] ↑ S. Gaire, S. Gyawali, S. Mishra, S. Niroula, D. Thakur, and U. Yadav, “Systematization of knowledge: Security and safety in the Model Context Protocol ecosystem,” arXiv preprint arXiv:2512.08290, 2025.
[26] ↑ M. A. Ferrag, N. Tihanyi, D. Hamouda, L. Maglaras, and M. Debbah, “From prompt injections to protocol exploits: Threats in LLM-powered AI agents workflows,” arXiv preprint arXiv:2506.23260, 2025.
[27] ↑ Invariant Labs, “MCP tool poisoning attacks,” 2025.
[28] ↑ M. Bhatt, V. S. Narajala, and I. Habler, “ETDI: Mitigating tool squatting and rug pull attacks in Model Context Protocol,” arXiv preprint arXiv:2506.01333, 2025.
[29] ↑ S. Jamshidi, K. W. Nafi, A. M. Dakhel, N. Shahabi, F. Khomh, and N. Ezzati-Jivan, “Securing the Model Context Protocol: Defending LLMs against tool poisoning and adversarial attacks,” arXiv preprint arXiv:2512.06556, 2025.
[30] ↑ X. Hou et al., “Model Context Protocol (MCP): Landscape, security threats, and future research directions,” arXiv preprint arXiv:2503.23278, 2025.
[31] ↑ Unit 42, “New prompt injection attack vectors through MCP sampling,” Palo Alto Networks, 2025.
[32] ↑ E. Bagdasaryan, T. Hsieh, B. Nassi, and V. Shmatikov, “(Ab)using images and sounds for indirect instruction injection in multi-modal LLMs,” arXiv preprint arXiv:2307.10490, 2023.
[33] ↑ Y. Gong, D. Ran, J. Liu, C. Wang, T. Cong, A. Wang, S. Duan, and X. Wang, “FigStep: Jailbreaking large vision-language models via typographic visual prompts,” arXiv preprint arXiv:2311.05608, 2023.
[34] ↑ W. Zou, R. Geng, B. Wang, and J. Jia, “PoisonedRAG: Knowledge corruption attacks to retrieval-augmented generation of large language models,” in Proc. USENIX Security, 2025.
[35] ↑ C. Clop and Y. Teglia, “Backdoored retrievers for prompt injection attacks on retrieval augmented generation of large language models,” arXiv preprint arXiv:2410.14479, 2024.
[36] ↑ P. Cheng, Y. Ding, T. Ju, Z. Wu, W. Du, P. Yi, Z. Zhang, and G. Liu, “TrojanRAG: Retrieval-augmented generation can be backdoor driver in large language models,” arXiv preprint arXiv:2405.13401, 2024.
[37] ↑ S. Yan et al., “An LLM-assisted easy-to-trigger backdoor attack on code completion models: Injecting disguised vulnerabilities against strong detection,” in Proc. USENIX Security, 2024.
[38] ↑ M. Bhatt et al., “Purple Llama CyberSecEval: A secure coding benchmark for language models,” arXiv preprint arXiv:2312.04724, 2023.
[39] ↑ H. Pearce, B. Ahmad, B. Tan, B. Dolan-Gavitt, and R. Karri, “Asleep at the keyboard? Assessing the security of GitHub Copilot's code contributions,” in Proc. IEEE S&P, 2022.
[40] ↑ J. Spracklen, R. Wijewickrama, A. H. M. N. Sakib, A. Maiti, B. Viswanath, and M. Jadliwala, “We have a package for you! A comprehensive analysis of package hallucinations by code generating LLMs,” arXiv preprint arXiv:2406.10279, 2024.
[41] ↑ M. Yang et al., “Inserting and activating backdoor attacks in LLM agents,” in Proc. ACL, 2024.
[42] ↑ E. Hubinger et al., “Sleeper agents: Training deceptive LLMs that persist through safety training,” arXiv preprint arXiv:2401.05566, 2024.
[43] ↑ Y. Yang, D. Wu, and Y. Chen, “MCPSecBench: A systematic security benchmark and playground for testing Model Context Protocols,” arXiv preprint arXiv:2508.13220, 2025.
[44] ↑ E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer, and F. Tramèr, “AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,” in Proc. NeurIPS, 2024.
[45] ↑ M. Andriushchenko et al., “AgentHarm: A benchmark for measuring harmfulness of LLM agents,” in Proc. ICLR, 2025.
[46] ↑ H. Zhang, J. Huang, K. Mei, Y. Yao, Z. Wang, C. Zhan, H. Wang, and Y. Zhang, “Agent Security Bench (ASB): Formalizing and benchmarking attacks and defenses in LLM-based agents,” in Proc. ICLR, 2025.
[47] ↑ S. Toyer et al., “Tensor Trust: Interpretable prompt injection attacks from an online game,” in Proc. NeurIPS, 2023.
[48] ↑ S. Schulhoff et al., “Ignore this title and HackAPrompt: Exposing systemic vulnerabilities of LLMs through a global prompt hacking competition,” in Proc. EMNLP, 2023.
[49] ↑ T. Yuan et al., “R-Judge: Benchmarking safety risk awareness for LLM agents,” in Findings of EMNLP, 2024.
[50] ↑ Y. Ruan, H. Dong, A. Wang, S. Pitis, Y. Zhou, J. Ba, Y. Dubois, C. J. Maddison, and T. Hashimoto, “Identifying the risks of LM agents with an LM-emulated sandbox,” in Proc. ICLR, 2024.
[51] ↑ Q. Zhan, R. Fang, R. Bindu, A. Gupta, T. Hashimoto, and D. Kang, “InjecAgent: Benchmarking indirect prompt injections in tool-integrated LLM agents,” in Findings of ACL, 2024.
[52] ↑ M. Mazeika et al., “HarmBench: A standardized evaluation framework for automated red teaming and robust refusal,” arXiv preprint arXiv:2402.04249, 2024.
[53] ↑ P. Chao et al., “JailbreakBench: An open robustness benchmark for jailbreaking language models,” in Proc. NeurIPS, 2024.
[54] ↑ Y. Liu, Y. Deng, R. Xu, Y. Wang, and Y. Liu, “Formalizing and benchmarking prompt injection attacks and defenses,” in Proc. USENIX Security, 2024.
[55] ↑ J. Yi, Y. Xie, B. Zhu, E. Kiciman, G. Sun, X. Xie, and F. Wu, “Benchmarking and defending against indirect prompt injection attacks on large language models,” arXiv preprint arXiv:2312.14197, 2023.
[56] ↑ E. Wallace, K. Xiao, R. Leike, L. Weng, J. Heidecke, and A. Beutel, “The instruction hierarchy: Training LLMs to prioritize privileged instructions,” arXiv preprint arXiv:2404.13208, 2024.
[57] ↑ S. M. A. Hossain, R. K. Shayoni, M. R. Ameen, A. Islam, M. F. Mridha, and J. Shin, “A multi-agent LLM defense pipeline against prompt injection attacks,” arXiv preprint arXiv:2509.14285, 2025.
[58] ↑ T. Shi, K. Zhu, Z. Wang, Y. Jia, W. Cai, W. Liang, H. Wang, H. Alzahrani, J. Lu, K. Kawaguchi, B. Alomair, X. Zhao, W. Y. Wang, N. Gong, W. Guo, and D. Song, “PromptArmor: Simple yet effective prompt injection defenses,” arXiv preprint arXiv:2507.15219, 2025.
[59] ↑ K. Hines et al., “Defending against indirect prompt injection attacks with spotlighting,” Microsoft Research, 2024.
[60] ↑ E. Debenedetti et al., “Defeating prompt injections by design,” arXiv preprint arXiv:2503.18813, 2025.
[61] ↑ Y. Wu, F. Roesner, T. Kohno, N. Zhang, and U. Iqbal, “IsolateGPT: An execution isolation architecture for LLM-based agentic systems,” in Proc. NDSS, 2025.
[62] ↑ S. Chen, J. Piet, C. Sitawarin, and D. Wagner, “StruQ: Defending against prompt injection with structured queries,” in Proc. USENIX Security, 2025.
[63] ↑ S. Chen, A. Zharmagambetov, S. Mahloujifar, K. Chaudhuri, D. Wagner, and C. Guo, “SecAlign: Defending against prompt injection with preference optimization,” in Proc. CCS, 2025.
[64] ↑ Meta AI, “Agents Rule of Two: A practical approach to AI agent security,” 2025.
[65] ↑ T. Shi, J. He, Z. Wang, L. Wu, H. Li, W. Guo, and D. Song, “Progent: Programmable privilege control for LLM agents,” arXiv preprint arXiv:2504.11703, 2025.
[66] ↑ Z. Wang et al., “MELON: Provable defense against indirect prompt injection attacks in AI agents,” in Proc. ICML, 2025.
[67] ↑ H. Inan et al., “Llama Guard: LLM-based input-output safeguard for human-AI conversations,” arXiv preprint arXiv:2312.06674, 2023.
[68] ↑ T. Rebedea, R. Dinu, M. N. Sreedhar, C. Parisien, and J. Cohen, “NeMo Guardrails: A toolkit for controllable and safe LLM applications with programmable rails,” in Proc. EMNLP Demo, 2023.
[69] ↑ T. Markov et al., “A holistic approach to undesired content detection in the real world,” in Proc. AAAI, 2023.
[70] ↑ M. Nasr, N. Carlini, C. Sitawarin, S. Schulhoff, J. Hayes, et al., “The attacker moves second: Stronger adaptive attacks bypass defenses against LLM jailbreaks and prompt injections,” arXiv preprint arXiv:2510.09023, 2025.
[71] ↑ F. Tramèr, N. Carlini, W. Brendel, S. Madry, and A. Kurakin, “On adaptive attacks to adversarial example defenses,” in Proc. NeurIPS, 2020.
[72] ↑ Y. Liu, G. Deng, Y. Li, K. Wang, Z. Wang, X. Wang, T. Zhang, Y. Liu, H. Wang, Y. Zheng, and Y. Liu, “Identifying the risks of LM agents with an LM-emulated sandbox,” in Proc. ICLR, 2024.
[73] ↑ S. Datta, S. K. Nahin, A. Chhabra, and P. Mohapatra, “Agentic AI security: Threats, defenses, evaluation, and open challenges,” arXiv preprint arXiv:2510.23883, 2025.
[74] ↑ Y. Liu et al., “Prompt injection attack against LLM-integrated applications,” arXiv preprint arXiv:2306.05499, 2023.
[75] ↑ Y. Yao et al., “A survey on large language model (LLM) security and privacy: The good, the bad, and the ugly,” in High-Confidence Computing, 2024.
[76] ↑ Q. Feng, S. R. Kasa, S. K. Kasa, H. Yun, C. H. Teo, and S. B. Bodapati, “Exposing privacy gaps: Membership inference attack on preference data for LLM alignment,” arXiv preprint arXiv:2407.06443, 2024.
[77] ↑ W. Fu et al., “Membership inference attacks against fine-tuned large language models via self-prompt calibration,” in Proc. NeurIPS, 2024.
[78] ↑ M. Ohm, H. Plate, A. Sykosch, and M. Meier, “Backstabber's knife collection: A review of open source software supply chain attacks,” in Proc. DIMVA, 2020.
[79] ↑ P. Ladisa et al., “SoK: Taxonomy of attacks on open-source software supply chains,” in Proc. IEEE S&P, 2023.
Report Issue
Report GitHub Issue
Title:
Content selection saved. Describe the issue below:
Description:
Submit without GitHub Submit in GitHub
Report Issue for Selection
Generated by L A T E xml[LOGO]
Instructions for reporting errors
We are continuing to improve HTML versions of papers, and your feedback helps enhance accessibility and mobile support. To report errors in the HTML that will help us improve conversion and rendering, choose any of the methods listed below:
Click the "Report Issue" button.
Open a report feedback form via keyboard, use " Ctrl + ?".
Make a text selection and click the "Report Issue for Selection" button near your cursor.
You can use Alt+Y to toggle on and Alt+Shift+Y to toggle off accessible reporting links at each section.
Our team has already identified the following issues. We appreciate your time reviewing and reporting rendering errors we may not have found yet. Your efforts will help us improve the HTML versions for all readers, because disability should not be a barrier to accessing research. Thank you for your continued support in championing open access for all.
Have a free development cycle? Help support accessibility at arXiv! Our collaborators at LaTeXML maintain a list of packages that need conversion, and welcome developer contributions.