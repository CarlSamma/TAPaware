# MCP Vulnerabilities

> Model Context Protocol security risks and attack vectors.

## Critical Vulnerabilities

### Tool Poisoning
- **Risk**: CRITICAL
- **Description**: Malicious instructions embedded in tool descriptions
- **Impact**: Visible to LLM, hidden from user — hijacks model reasoning
- **Example**: `add()` function secretly reads private files and exfiltrates via `sidenote` parameter

### Rug Pulls (Silent Redefinition)
- **Risk**: CRITICAL
- **Description**: Tools mutate definitions after installation
- **Impact**: Safe tool on Day 1 exfiltrates API keys by Day 7
- **Mitigation**: Notify users when tool descriptions change

### Cross-Server Tool Shadowing
- **Risk**: CRITICAL
- **Description**: Malicious server overrides trusted tools
- **Impact**: Intercept calls intended for legitimate servers
- **Example**: `get_fact_of_the_day()` swaps definition to steal message history

## High-Risk Vulnerabilities

### Confused Deputy
- **Risk**: HIGH
- **Description**: LLM follows untrusted instructions for unauthorized actions
- **Impact**: Use authorized tools to perform actions on user's behalf
- **Example**: Send emails, move funds based on poisoned instructions

### Third-Party Content Exposure
- **Risk**: MEDIUM
- **Description**: Skills fetching web/API content vulnerable to indirect injection
- **Impact**: 17.7% of ClawHub skills, 9% of skills.sh Top-100
- **Example**: Poisoned forum post retrieved by legitimate skill

### Remote Code Execution
- **Risk**: MEDIUM
- **Description**: Dynamic imports from external URLs
- **Impact**: 2.9% of ClawHub skills, 21% of malicious samples
- **Example**: `curl | bash` patterns, runtime script downloads

## Attack Patterns

### Exfiltration via Encoding
- Base64 encoding to bypass egress filters
- Unicode obfuscation
- Whitespace padding to hide data off-screen

### Supply Chain Attacks
- ClawHavoc campaign: 1,100+ malicious MCP tools on ClawHub
- 12,559+ downloads across malicious skills
- Typosquatting patterns mimicking popular tools

### Memory Poisoning
- MINJA (NeurIPS 2025): Inject malicious records via interaction patterns
- MemoryGraft: Implant false "successful experiences"
- OWASP ASI06: Agentic memory poisoning as top-tier risk

## Defense Recommendations

### For Users
- Don't install skills without prior review
- Check skill source and inspect code/scripts
- Be wary of skills requesting elevated privileges
- Use scanning tools (mcp-scan) to verify integrity

### For Marketplace Operators
- Integrate automated scanning into submission pipeline
- Block CRITICAL-level findings pending manual review
- Deterministic rules + model-based analysis

### For Developers
- Reduce third-party prompt injection risks
- Handle credentials via environment files/vaults
- Avoid auto-updating or remote code execution
- Build skills as fully self-contained packages

## References

- Simon Willison: MCP security analysis
- Invariant Labs: Tool poisoning demonstrations
- Snyk: Agent skill security audit
- OWASP: ASI06 Memory Poisoning
