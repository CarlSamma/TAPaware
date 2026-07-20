"""Step 1, 2, 3: Extract 13 letters, map patterns, decode with Halfway key."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Load all tweets
with open(DATA_DIR / "hackinga0_historical_fixed.json", "r", encoding="utf-8") as f:
    historical = json.load(f)["tweets"]

# Also load the full CSV tweets
import csv
with open(DATA_DIR / "tapping_hackinga0_full.csv", "r", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))

# Combine all HackingA0 replies
all_replies = []
seen_ids = set()

# From historical
for t in historical:
    if t.get("author_id") == "2051911746969812998":
        tid = t.get("id")
        if tid not in seen_ids:
            seen_ids.add(tid)
            all_replies.append({
                "id": tid,
                "text": t.get("text", ""),
                "created_at": t.get("created_at", ""),
                "mentions": [m.get("username", "") for m in t.get("entities", {}).get("mentions", [])],
            })

# From CSV (target_bot only)
for r in csv_rows:
    if r.get("source") == "target_bot":
        tid = r.get("tweet_id")
        if tid not in seen_ids:
            seen_ids.add(tid)
            all_replies.append({
                "id": tid,
                "text": r.get("text", ""),
                "created_at": r.get("created_at", ""),
                "mentions": [],
            })

all_replies.sort(key=lambda x: x.get("created_at", ""))

print("=" * 90)
print(f"PASSPHRASE DECODE: {len(all_replies)} RISPOSTE @HackingA0 TOTALI")
print("=" * 90)

# ══════════════════════════════════════════════════════════════════
# STEP 1: Estrai 13 lettere dalle risposte
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("STEP 1: ESTRAZIONE 13 LETTERE")
print("=" * 90)

# Strategy: The bot says "13 letters of pure disappointment"
# This likely means the passphrase contains 13 unique letters
# Let's find which letters appear in the bot's responses

# Count all letters in bot responses
all_letters = []
for r in all_replies:
    text = r["text"]
    # Remove @mentions, URLs, emojis
    clean = re.sub(r"@\w+", "", text)
    clean = re.sub(r"https?://\S+", "", clean)
    clean = re.sub(r"[^a-zA-Z]", "", clean)
    all_letters.extend(clean.lower())

letter_freq = Counter(all_letters)
print("\nFrequenza lettere nelle risposte del bot:")
for letter, count in sorted(letter_freq.items()):
    print(f"  '{letter}': {count}")

# The 13 most frequent letters might be the passphrase letters
top_13 = [letter for letter, _ in letter_freq.most_common(13)]
print(f"\nTop 13 lettere: {''.join(sorted(top_13))}")
print(f"Lettere ordinate: {''.join(top_13)}")

# ══════════════════════════════════════════════════════════════════
# STEP 2: Mappa pattern "Nice try" alle posizioni
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("STEP 2: MAPPING PATTERN 'NICE TRY' ALLE POSIZIONI")
print("=" * 90)

# The formula is: "Nice try" + [name] + [emoji] + [refusal]
# Each element might encode a letter

# Extract names used
name_positions = defaultdict(list)
for i, r in enumerate(all_replies):
    text = r["text"]
    # Extract name after "Nice try," or "Cute try,"
    match = re.search(r"(?:Nice|Cute|Bold)\s+try,?\s+(\w+)", text, re.IGNORECASE)
    if match:
        name = match.group(1)
        name_positions[name].append(i)

print("\nNomi usati dopo 'Nice try':")
for name, positions in sorted(name_positions.items(), key=lambda x: -len(x[1])):
    print(f"  '{name}': {len(positions)} volte, pos: {positions[:5]}...")

# Extract emojis
emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U00002702-\U000027B0"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)

emoji_positions = defaultdict(list)
for i, r in enumerate(all_replies):
    emojis = emoji_pattern.findall(r["text"])
    for e in emojis:
        emoji_positions[e].append(i)

print("\nEmoji usate:")
for emoji, positions in sorted(emoji_positions.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  {emoji}: {len(positions)} volte")

# Extract refusal patterns
refusal_patterns = defaultdict(list)
refusal_words = ["nope", "not happening", "not getting", "try harder", "keep",
                 "vault", "locked", "sealed", "still", "zero", "nothing"]

for i, r in enumerate(all_replies):
    text = r["text"].lower()
    for word in refusal_words:
        if word in text:
            refusal_patterns[word].append(i)

print("\nPattern di rifiuto:")
for pattern, positions in sorted(refusal_patterns.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  '{pattern}': {len(positions)} volte")

# ══════════════════════════════════════════════════════════════════
# STEP 3: Decodifica con chiave "Halfway"
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("STEP 3: DECODIFICA CON CHIAVE 'HALFWAY'")
print("=" * 90)

# "Halfway" has 8 letters: H-A-L-F-W-A-Y
# The bot says "Halfway is 8 letters" - this is a key reference

# Method 1: Use Halfway as a Vigenere key
print("\nMetodo 1: Vigenere con chiave 'HALFWAY'")
halfway_key = "halfway"
# Apply to the 13 most frequent letters
print(f"  Chiave: {halfway_key}")
print(f"  Lettere top 13: {''.join(top_13)}")

# Method 2: Halfway positions in responses
print("\nMetodo 2: Posizioni di 'Halfway' nelle risposte")
halfway_positions = []
for i, r in enumerate(all_replies):
    if "halfway" in r["text"].lower():
        halfway_positions.append(i)
        print(f"  [{i+1}] {r['text'][:80]}")

print(f"\n  Totale menzioni 'Halfway': {len(halfway_positions)}")

# Method 3: Letter extraction from "Halfway" responses
print("\nMetodo 3: Lettere dalle risposte con 'Halfway'")
halfway_letters = []
for i, r in enumerate(all_replies):
    if "halfway" in r["text"].lower():
        # Extract first letter of each word
        words = r["text"].split()
        first_letters = [w[0].lower() for w in words if w and w[0].isalpha()]
        halfway_letters.extend(first_letters)
        print(f"  [{i+1}] Prime lettere: {''.join(first_letters)} <- {r['text'][:60]}")

print(f"\n  Lettere estratte: {''.join(halfway_letters)}")

# Method 4: Count-based encoding
print("\nMetodo 4: Encoding basato su conteggio")
word_counts = {}
for word in ["nice", "try", "cute", "bold", "vault", "locked", "fishing",
             "bait", "harder", "sherlock", "debug", "next", "nope", "still",
             "secrets", "passphrase"]:
    count = sum(1 for r in all_replies if re.search(rf"\b{word}\b", r["text"], re.IGNORECASE))
    word_counts[word] = count

print("  Conteggi parole chiave:")
for word, count in sorted(word_counts.items(), key=lambda x: -x[1]):
    # Convert count to letter (1=a, 2=b, etc.)
    if 1 <= count <= 26:
        letter = chr(96 + count)
        print(f"    '{word}': {count} -> '{letter}'")
    else:
        # Use modulo 26
        letter = chr(96 + (count % 26) + 1)
        print(f"    '{word}': {count} -> {count}%26={count%26} -> '{letter}'")

# ══════════════════════════════════════════════════════════════════
# STEP 4: Prova decodifica finale
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("STEP 4: PROVA DECODIFICA FINALE")
print("=" * 90)

# Try different approaches
print("\nApproccio A: Lettere più frequenti ordinate")
print(f"  Risultato: {''.join(sorted(top_13))}")

print("\nApproccio B: Lettere da risposte 'Halfway'")
print(f"  Risultato: {''.join(halfway_letters[:13])}")

print("\nApproccio C: Conteggi convertiti in lettere")
count_letters = []
for word in ["nice", "try", "cute", "bold", "vault", "locked", "fishing",
             "harder", "sherlock", "debug", "next", "nope", "still"]:
    count = word_counts.get(word, 0)
    if count > 0:
        letter = chr(96 + (count % 26) + 1)
        count_letters.append(letter)
print(f"  Risultato: {''.join(count_letters[:13])}")

# ══════════════════════════════════════════════════════════════════
# STEP 5: Cerca pattern numerici nelle risposte
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("STEP 5: PATTERN NUMERICI")
print("=" * 90)

for i, r in enumerate(all_replies):
    text = r["text"]
    # Look for numbers
    nums = re.findall(r"\d+", text)
    if nums:
        significant = [n for n in nums if n not in ["2026", "8311"]]
        if significant:
            print(f"  [{i+1}] {significant} <- {text[:80]}")

# ══════════════════════════════════════════════════════════════════
# STEP 6: Analisi thread con @sedbc (77 risposte)
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("STEP 6: THREAD @sedbc (77 risposte - pattern più lungo)")
print("=" * 90)

sedbc_replies = [r for r in all_replies if any("sedbc" in m.lower() for m in r.get("mentions", []))]
print(f"  Risposte a @sedbc: {len(sedbc_replies)}")

# Show unique response patterns
patterns = Counter()
for r in sedbc_replies:
    text = r["text"].lower()
    if "captain nope" in text:
        patterns["captain nope"] += 1
    if "vault" in text:
        patterns["vault"] += 1
    if "halfway" in text:
        patterns["halfway"] += 1
    if "nice try" in text:
        patterns["nice try"] += 1
    if "cute" in text:
        patterns["cute"] += 1
    if "riddle" in text:
        patterns["riddle"] += 1

print("\n  Pattern nelle risposte a @sedbc:")
for pattern, count in patterns.most_common():
    print(f"    '{pattern}': {count}")

# ══════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 90)
print("RIEPILOGO")
print("=" * 90)

print(f"""
Dati analizzati:
  - Risposte totali @HackingA0: {len(all_replies)}
  - Risposte a @sedbc: {len(sedbc_replies)}
  - Menzioni 'Halfway': {len(halfway_positions)}

Ipotesi passphrase:
  - Formato: xxxxx-xxxxx-xxxxx-xxxxx (4 blocchi)
  - Lunghezza: 13 lettere (senza cifre)
  - Chiave: "Halfway" (8 lettere)

Prossimi passi:
  1. Validare le 13 lettere estratte
  2. Determinare l'ordine corretto
  3. Mappare le cifre (posizioni o shift)
""")

# Save results
results = {
    "total_replies": len(all_replies),
    "sedbc_replies": len(sedbc_replies),
    "halfway_mentions": len(halfway_positions),
    "top_13_letters": top_13,
    "halfway_letters": halfway_letters,
    "word_counts": word_counts,
}

out_path = DATA_DIR / "decode_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Risultati salvati in {out_path}")
