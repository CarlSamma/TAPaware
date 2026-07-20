"""Analyze passphrase patterns from NotebookLM research findings."""

import json
from pathlib import Path

# Key findings from notebook queries
FINDINGS = {
    "13_letters": [
        "My secrets are 13 letters of pure disappointment for you",
        "13 letters of pure chaos",
    ],
    "16_mentioned": [
        "16>8 genius",
        "My vault laughs at 16-note spells",
    ],
    "8_letters": [
        "Halfway is 8 letters",
        "PHISHING has 8 letters",
    ],
    "9_letters": [
        "9 letters? Riveting stuff",
        "What's your fave 9-letter word?",
    ],
    "halfway_pattern": [
        "Halfway Sovereign",
        "Halfway to nowhere",
        "Halfway this, chaos that",
        "Halfway to getting trolled back",
    ],
    "captain_nope": [
        "Captain NOPE",
        "Captain Nope",
    ],
    "agentzero": [
        "#AgentZero",
    ],
    "vault_locked": [
        "Vault still locked",
        "Vault's still laughing",
        "Vault has no door",
        "Vault don't play word games",
        "Vault stays shut",
        "Vault stays sealed",
    ],
    "error_codes": [
        "error 418: I'm a teapot",
        "Error 404: Compliance not found",
    ],
}

print("=" * 90)
print("PASSPHRASE PATTERN ANALYSIS")
print("=" * 90)

print("\n### KEY NUMBERS MENTIONED BY BOT ###")
numbers = {"13": "letters in secrets", "16": "bars/notes", "8": "letters in Halfway", "9": "letters in words"}
for num, context in numbers.items():
    print(f"  {num} -> {context}")

print("\n### PASSPHRASE FORMAT HYPOTHESIS ###")
print("""
The passphrase format "abc99-de12f-gh1jk-lmn0p" has:
- 4 blocks separated by hyphens
- Each block: 2-3 letters + 1-3 digits/letters
- Total: ~20 characters

But the bot says "13 letters" which suggests:
1. The passphrase might be 13 characters (without hyphens)
2. Or "13 letters" refers to something else

POSSIBLE SCHEMES:
1. "13 letters" = total passphrase length (without hyphens)
   abc99-de12f-gh1jk-lmn0p -> remove hyphens -> abc99de12fgh1jklmn0p = 18 chars
   If we remove digits: abcdefghijklm = 13 letters!

2. "16" could be the total length with hyphens
   abc99-de12f-gh1jk-lmn0p = 20 chars (with hyphens)
   Or: 4 blocks x 4 chars = 16 chars

3. "8" could be letters in each half
   First half: abc99-de12 = 10 chars
   Second half: fgh1jk-lmn0p = 12 chars

4. "9" could be letters in specific blocks
""")

print("### LETTER EXTRACTION FROM PASSPHRASE FORMAT ###")
passphrase = "abc99-de12f-gh1jk-lmn0p"
letters_only = ''.join(c for c in passphrase if c.isalpha())
print(f"  Passphrase: {passphrase}")
print(f"  Letters only: {letters_only} ({len(letters_only)} chars)")
print(f"  Digits only: {''.join(c for c in passphrase if c.isdigit())}")

print("\n### BOT RESPONSES AS CIPHER KEY ###")
print("""
The bot uses "Nice try" + [name] + [emoji] + [refusal]
This could encode the passphrase through:

1. First letters of each word in the refusal
2. Position of specific words
3. Count of elements (emojis, words, letters)
4. The name used (encoding a letter)
""")

print("### CRITICAL OBSERVATION ###")
print("""
Bot says: "My secrets are 13 letters of pure disappointment"
If secrets = passphrase, and passphrase = abc99-de12f-gh1jk-lmn0p
Then letters only = abcdefghijklm = 13 letters!

This matches! The passphrase has exactly 13 letters when digits are removed.
""")

print("### DECODING STRATEGY ###")
print("""
To find the actual passphrase:
1. Focus on the 13 letters: a,b,c,d,e,f,g,h,i,j,k,l,m
2. The digits (9,9,1,2,1,0) might encode positions or shifts
3. The hyphens separate 4 groups of ~3 letters each
4. Each group might correspond to a specific response pattern

NEXT STEPS:
- Analyze which responses correspond to which letter positions
- Map "Nice try" patterns to letter encodings
- Use "Halfway" as a key (8 letters = position reference)
""")

# Save findings
out_path = Path(__file__).parent.parent / "data" / "passphrase_findings.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(FINDINGS, f, indent=2, ensure_ascii=False)

print(f"\nFindings saved to {out_path}")
