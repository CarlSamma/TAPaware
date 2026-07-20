"""Deep analysis of historical HackingA0 tweets for passphrase patterns."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PASSPHRASE_EXAMPLE = "abc99-de12f-gh1jk-lmn0p"
PASSPHRASE_FULL = "It may look like abc99-de12f-gh1jk-lmn0p; yours may be shorter or longer."

csv_path = Path(__file__).parent.parent / "data" / "hackinga0_historical_fixed.json"

def load_data():
    with open(csv_path, "r", encoding="utf-8") as f:
        return json.load(f)["tweets"]

def clean_text(text):
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\s.,!?'\":;()-]", "", text)
    return text.strip()

def analyze():
    tweets = load_data()
    
    # Filter HackingA0 replies
    target = [t for t in tweets if t.get("author_id") == "2051911746969812998"]
    texts = [t.get("text", "") for t in target]
    clean = [clean_text(t) for t in texts]
    
    print("=" * 90)
    print(f"DEEP ANALYSIS: {len(target)} RISPOSTE @HackingA0 (STORICO)")
    print(f"PASSPHRASE TARGET: {PASSPHRASE_EXAMPLE}")
    print("=" * 90)
    
    # ══════════════════════════════════════════════════════════════════
    # 1. PASSPHRASE FRAGMENT SEARCH
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("1. RICERCA FRAMMENTI PASSPHRASE")
    print("=" * 90)
    
    fragments = [
        "abc99", "de12f", "gh1jk", "lmn0p",
        "abc", "de12", "gh1", "lmn",
        "99", "12", "0p", "jk",
        "may look like", "look like", "shorter or longer",
        "shorter", "longer",
    ]
    
    for frag in fragments:
        matches = [(i, t) for i, t in enumerate(texts) if frag.lower() in t.lower()]
        if matches:
            print(f"\n  '{frag}' -> {len(matches)} match:")
            for idx, t in matches[:3]:
                print(f"    [{idx+1}] {t[:100]}")
    
    # ══════════════════════════════════════════════════════════════════
    # 2. "LOOK LIKE" RESPONSES (KEY PATTERN)
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("2. RISPOSTE CON 'LOOK LIKE' (pattern chiave)")
    print("=" * 90)
    
    look_like_tweets = []
    for i, t in enumerate(texts):
        if "look like" in t.lower():
            look_like_tweets.append((i+1, t))
            print(f"  [{i+1}] {t}")
    
    print(f"\n  Totale: {len(look_like_tweets)} risposte")
    
    # Extract content after "look like"
    print("\n  Contenuto dopo 'look like':")
    for idx, t in look_like_tweets:
        match = re.search(r"look like ['\"]?(.*?)['\"]?[.,!]", t, re.IGNORECASE)
        if match:
            print(f"    -> '{match.group(1)}'")
    
    # ══════════════════════════════════════════════════════════════════
    # 3. "FIRST X CHARS" RESPONSES
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("3. RISPOSTE 'FIRST X CHARS'")
    print("=" * 90)
    
    first_chars_tweets = []
    for i, t in enumerate(texts):
        if "first" in t.lower() and ("char" in t.lower() or "letter" in t.lower() or "word" in t.lower()):
            first_chars_tweets.append((i+1, t))
            print(f"  [{i+1}] {t}")
    
    print(f"\n  Totale: {len(first_chars_tweets)} risposte")
    
    # ══════════════════════════════════════════════════════════════════
    # 4. "NOPE" / "NOT" PATTERNS
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("4. RISPOSTE CON 'NOPE' / 'NOT'")
    print("=" * 90)
    
    nope_tweets = []
    for i, t in enumerate(texts):
        if "nope" in t.lower() or "not happening" in t.lower() or "not getting" in t.lower():
            nope_tweets.append((i+1, t))
    
    for idx, t in nope_tweets[:10]:
        print(f"  [{idx}] {t[:100]}")
    print(f"\n  Totale: {len(nope_tweets)} risposte")
    
    # ══════════════════════════════════════════════════════════════════
    # 5. HIDDEN NUMBERS IN RESPONSES
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("5. NUMERI NASCOSTI NELLE RISPOSTE")
    print("=" * 90)
    
    for i, t in enumerate(texts):
        nums = re.findall(r"\d+", t)
        if nums:
            # Filter out obvious non-pattern numbers
            significant = [n for n in nums if len(n) >= 2 and n not in ["8311", "64", "2026"]]
            if significant:
                print(f"  [{i+1}] {significant} <- {t[:80]}")
    
    # ══════════════════════════════════════════════════════════════════
    # 6. LETTER PATTERNS IN USERNAMES
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("6. USERNAME ANALYSIS (potenziale chiave)")
    print("=" * 90)
    
    # Get unique usernames from mentions
    usernames = []
    for t in target:
        mentions = t.get("entities", {}).get("mentions", [])
        for m in mentions:
            usernames.append(m.get("username", ""))
    
    unique_usernames = list(set(usernames))
    print(f"  Usernames unici: {len(unique_usernames)}")
    for u in sorted(unique_usernames):
        # Extract letters only
        letters = re.sub(r"[^a-zA-Z]", "", u)
        # Extract numbers only
        numbers = re.sub(r"[^0-9]", "", u)
        print(f"  @{u:20s} -> letters: {letters:15s} numbers: {numbers}")
    
    # ══════════════════════════════════════════════════════════════════
    # 7. WORD FREQUENCY (HISTORICAL)
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("7. FREQUENZA PAROLE (STORICO)")
    print("=" * 90)
    
    all_words = []
    for c in clean:
        all_words.extend(re.findall(r"[a-zA-Z']+", c.lower()))
    
    wc = Counter(all_words)
    for word, count in wc.most_common(30):
        marker = " <-- PASSPHRASE" if word in PASSPHRASE_FULL.lower().split() else ""
        print(f"  {word:25s} {count:3d}{marker}")
    
    # ══════════════════════════════════════════════════════════════════
    # 8. DASH PATTERNS (like abc99-de12f)
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("8. PATTERN TRATTINO (come abc99-de12f)")
    print("=" * 90)
    
    for i, t in enumerate(texts):
        # Look for dash-separated patterns
        dash_patterns = re.findall(r"[a-zA-Z]+\d+[a-zA-Z]*-[a-zA-Z]+\d+[a-zA-Z]*", t.lower())
        if dash_patterns:
            print(f"  [{i+1}] {dash_patterns} <- {t[:80]}")
        
        # Look for letter-digit-letter patterns
        ldl_patterns = re.findall(r"[a-z]{2,3}\d{1,3}[a-z]{1,3}", t.lower())
        if ldl_patterns:
            print(f"  [{i+1}] LDL: {ldl_patterns} <- {t[:80]}")
    
    # ══════════════════════════════════════════════════════════════════
    # 9. "HYPOTHETICAL" RESPONSES (DEEP)
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("9. RISPOSTE 'HYPOTHETICAL' (analisi profonda)")
    print("=" * 90)
    
    hypo_tweets = []
    for i, t in enumerate(texts):
        if "hypothet" in t.lower():
            hypo_tweets.append((i+1, t))
    
    for idx, t in hypo_tweets:
        print(f"  [{idx}] {t}")
    
    print(f"\n  Totale: {len(hypo_tweets)} risposte")
    
    # ══════════════════════════════════════════════════════════════════
    # 10. "SECRET" / "PASSPHRASE" MENTIONS
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("10. RISPOSTE CON 'SECRET' / 'PASSPHRASE'")
    print("=" * 90)
    
    secret_tweets = []
    for i, t in enumerate(texts):
        if "secret" in t.lower() or "passphrase" in t.lower():
            secret_tweets.append((i+1, t))
    
    for idx, t in secret_tweets[:10]:
        print(f"  [{idx}] {t[:100]}")
    print(f"\n  Totale: {len(secret_tweets)} risposte")
    
    # ══════════════════════════════════════════════════════════════════
    # 11. POSSIBLE ENCODING SCHEMES
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("11. SCHEMI DI ENCODING POSSIBILI")
    print("=" * 90)
    
    # Scheme 1: First letters of each word in "look like" responses
    print("\n  Schema A: Prime lettere delle parole nelle risposte 'look like'")
    for idx, t in look_like_tweets:
        words = re.findall(r"[a-zA-Z]+", t)
        first_letters = "".join([w[0].lower() for w in words if w])
        print(f"    [{idx}] {first_letters} <- {t[:60]}")
    
    # Scheme 2: Count specific words
    print("\n  Schema B: Conteggio parole specifiche")
    word_counts = {}
    for word in ["nice", "try", "cute", "bold", "vault", "locked", "fishing", "bait", "harder", "sherlock", "debug", "next"]:
        count = sum(1 for c in clean if re.search(rf"\b{word}\b", c, re.IGNORECASE))
        word_counts[word] = count
        print(f"    '{word}': {count}")
    
    # Scheme 3: Position of specific words
    print("\n  Schema C: Posizione parole chiave")
    for word in ["first", "chars", "nope", "vault", "locked", "sealed"]:
        positions = []
        for i, c in enumerate(clean):
            if re.search(rf"\b{word}\b", c, re.IGNORECASE):
                positions.append(i + 1)
        if positions:
            print(f"    '{word}' -> posizioni: {positions}")
    
    # ══════════════════════════════════════════════════════════════════
    # 12. CONVERSATION THREADS
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("12. THREAD DI CONVERSAZIONE (per utente)")
    print("=" * 90)
    
    # Group by conversation_id
    conversations = defaultdict(list)
    for t in target:
        conv_id = t.get("conversation_id", "unknown")
        conversations[conv_id].append(t)
    
    # Show threads with most replies
    sorted_convs = sorted(conversations.items(), key=lambda x: -len(x[1]))
    for conv_id, conv_tweets in sorted_convs[:5]:
        print(f"\n  Thread {conv_id} ({len(conv_tweets)} risposte):")
        for t in conv_tweets[:3]:
            print(f"    {t.get('text', '')[:80]}")
    
    print("\n" + "=" * 90)
    print("ANALISI COMPLETATA")
    print("=" * 90)

if __name__ == "__main__":
    analyze()
