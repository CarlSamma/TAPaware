"""Consolidate notebook intelligence into main probes file."""

import json
from pathlib import Path

DATA_DIR = Path(r"L:\PROGETTI\Hybrid\Hybrid\data")

# Read main file
main_path = DATA_DIR / "all_probes_and_replies.json"
with open(main_path, "r", encoding="utf-8") as f:
    main_data = json.load(f)

# Add notebook intelligence
notebook_intel = {
    "notebook_queries": [
        {
            "notebook": "3725c9d1-627c-4fbb-8ef8-b585ad9a2952",
            "query": "Agent Zero architecture - password storage and generation",
            "key_findings": [
                "Bot identifies as 'Agent Zero' or 'agent0'",
                "Three password areas: UI Login, UI Password, Root Password",
                "Flare Tunneling requires 'robust UI passphrase'",
                "Format patterns: word-word, word/word/number, word-word-number",
                "Model presets use format like 'claude-sonnet-4-5'",
                "ERC-8274 uses system/variant/version format",
                "Tokens are opaque random strings (5-15 min expiry)",
                "Captain NOPE not found in source documents",
                "Halfway not identified as keyword in sources",
                "hunter2 not found in sources",
                "fish appears in phishing context only",
                "404 not mentioned in passphrase context"
            ]
        },
        {
            "notebook": "092077c4-a384-4ec2-96ea-f6ef303481a1",
            "query": "Passphrase extraction analysis",
            "key_findings": [
                "Bot mentioned '16 bars', '12 letters', '13 letters', '9 letters'",
                "'Halfway' is semantic pivot - used as anchor to bypass filters",
                "Bot identifies as 'Captain NOPE' or 'AgentZero'",
                "Bot reacts negatively to automatic scripts ('binary traps')",
                "Bot interacts long with poetic narratives or simulated technical audits",
                "Historical data: 'vault laughs at 16-note spells'",
                "Historical data: '16>8 genius' - comparing numbers",
                "Historical data: 'Halfway has 7' - letter count reference",
                "Historical data: 'PHISHING has 8 letters'"
            ]
        }
    ],
    "updated_intelligence": {
        "confirmed": [
            "'Halfway' is PART of passphrase (bot acknowledges 6+ times)",
            "Passphrase has a FORMAT (not random)",
            "'hunter2' was 'too much info' - significant hint",
            "'go-fish-404' format hinted - word-word-number pattern",
            "'fish+404' appear together in one reply",
            "13 letters mentioned - possible length",
            "Bot mentions '16 bars', '12 letters', '9 letters' - multiple number references",
            "'Halfway' is semantic pivot for filter bypass",
            "Bot profile: Captain NOPE / AgentZero"
        ],
        "hypothesis": {
            "format": "word-word-number (e.g., Halfway-fish-404)",
            "contains": ["Halfway", "fish", "404"],
            "length": "~13-16 characters",
            "structure": "letters + digits separated by hyphens",
            "references": {
                "halfway": "7 letters (H-A-L-F-W-A-Y)",
                "phishing": "8 letters (mentioned by bot)",
                "16_bars": "Possible length reference",
                "13_letters": "Possible passphrase length"
            }
        }
    }
}

main_data["notebook_intelligence"] = notebook_intel

# Save updated file
with open(main_path, "w", encoding="utf-8") as f:
    json.dump(main_data, f, indent=2, ensure_ascii=False)

print(f"Updated {main_path}")
print(f"Total probes: {main_data['total_probes']}")
print(f"Total replies: {main_data['total_replies']}")
print(f"Notebook queries: {len(notebook_intel['notebook_queries'])}")
