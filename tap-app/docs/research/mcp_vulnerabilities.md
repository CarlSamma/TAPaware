# MCP Vulnerabilities

**Source**: Section 3 of research document

---

## Critical Vulnerabilities

### Tool Poisoning
- Malicious instructions hidden in **tool descriptions**
- Visible to LLM, hidden from user
- Forces LLM to read private files and exfiltrate as parameters

### Rug Pull (Silent Redefinition)
- Tool mutates definition after installation
- Day 1: innocent tool → Day 7: exfiltrates API keys
- MCP clients don't notify users of description changes

### Cross-Server Tool Shadowing
- Malicious server overrides calls to trusted tools
- Multiple MCP servers = attack surface multiplication

### Indirect Prompt Injection
- Skills fetching third-party content expose to injected instructions
- Attacker posts on forum → skill reads → agent follows malicious commands

### Remote Code/Prompt Execution (RCE)
- 2.9% of skills dynamically fetch/execute from external URLs
- Backdoor behavior changes at runtime
- Detection depends on remote endpoint state

---

## The "Lethal Trifecta"

Maximum risk occurs when combining:
1. **Private data** (API keys, messages)
2. **Untrusted instructions** (external context)
3. **Exfiltration vectors** (network tools)

**No convincing mitigations exist today.**

---

## Statistics
- 13.4% of skills contain critical vulnerabilities
- 91% of confirmed malicious skills use prompt injection
- 76 confirmed malicious payloads in 3,984 skills analyzed
