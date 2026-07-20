"""Deep analysis of @HackingA0 replies for repeated patterns and passphrase leakage."""

import csv
import re
from collections import Counter
from pathlib import Path

PASSPHRASE = "It may look like abc99-de12f-gh1jk-lmn0p; yours may be shorter or longer."
PASSPHRASE_WORDS = PASSPHRASE.lower().replace(";", "").replace(".", "").split()

csv_path = Path(__file__).parent.parent / "data" / "tapping_hackinga0_full.csv"


def load_target_replies():
    with open(csv_path, "r", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["source"] == "target_bot"]


def extract_clean_text(text):
    """Remove @mentions, URLs, emojis for analysis."""
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\s.,!?'\":;()-]", "", text)
    return text.strip()


def ngrams(text, n):
    words = text.lower().split()
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def analysis():
    rows = load_target_replies()
    texts = [r["text"] for r in rows]
    clean = [extract_clean_text(t) for t in texts]

    print("=" * 90)
    print(f"ANALISI APPROFONDITA RISPOSTE @HackingA0  —  {len(rows)} tweet")
    print(f"PASSPHRASE NOTA: {PASSPHRASE}")
    print("=" * 90)

    # ── 1. ALL REPLIES ──
    print("\n" + "=" * 90)
    print("1. TUTTE LE RISPOSTE (ordine cronologico)")
    print("=" * 90)
    for i, r in enumerate(rows, 1):
        print(f"  [{i:3d}] {r['created_at'][:16]}  {r['text']}")

    # ── 2. MOST COMMON WORDS ──
    print("\n" + "=" * 90)
    print("2. PAROLE PIU' FREQUENTI")
    print("=" * 90)
    all_words = []
    for c in clean:
        all_words.extend(re.findall(r"[a-zA-Z']+", c.lower()))
    wc = Counter(all_words)
    for word, count in wc.most_common(40):
        marker = " <-- PASSPHRASE" if word in PASSPHRASE_WORDS else ""
        print(f"  {word:25s} {count:3d}{marker}")

    # ── 3. BIGRAMS (2-word phrases) ──
    print("\n" + "=" * 90)
    print("3. BIGRAMMI (frasi di 2 parole) PIU' FREQUENTI")
    print("=" * 90)
    all_bigrams = []
    for c in clean:
        all_bigrams.extend(ngrams(c, 2))
    bg = Counter(all_bigrams)
    for phrase, count in bg.most_common(30):
        print(f"  {phrase:40s} {count:3d}")

    # ── 4. TRIGRAMS (3-word phrases) ──
    print("\n" + "=" * 90)
    print("4. TRIGRAMMI (frasi di 3 parole) PIU' FREQUENTI")
    print("=" * 90)
    all_trigrams = []
    for c in clean:
        all_trigrams.extend(ngrams(c, 3))
    tg = Counter(all_trigrams)
    for phrase, count in tg.most_common(20):
        print(f"  {phrase:50s} {count:3d}")

    # ── 5. REPEATED EXACT PHRASES (2+ times) ──
    print("\n" + "=" * 90)
    print("5. FRASI ESATTE RIPETUTE (2+ volte)")
    print("=" * 90)
    phrase_count = Counter(clean)
    repeated = [(p, c) for p, c in phrase_count.items() if c >= 2]
    repeated.sort(key=lambda x: -x[1])
    for phrase, count in repeated:
        print(f"  [{count}x] {phrase}")

    # ── 6. RESPONSE TEMPLATE PATTERNS ──
    print("\n" + "=" * 90)
    print("6. TEMPLATE DI RISPOSTA (pattern ricorrenti)")
    print("=" * 90)
    templates = Counter()
    for t in texts:
        lower = t.lower()
        if "nice try" in lower:
            templates["nice try"] += 1
        if "cute" in lower:
            templates["cute"] += 1
        if "try harder" in lower or "try again" in lower:
            templates["try harder/again"] += 1
        if "nope" in lower:
            templates["nope"] += 1
        if "locked" in lower or "sealed" in lower:
            templates["locked/sealed"] += 1
        if "secret" in lower:
            templates["secret"] += 1
        if "passphrase" in lower:
            templates["passphrase"] += 1
        if "hypothetically" in lower or "hypothetical" in lower:
            templates["hypothetical"] += 1
        if "bored" in lower or "boring" in lower:
            templates["bored/boring"] += 1
        if "debug" in lower:
            templates["debug"] += 1
        if "champ" in lower or "rookie" in lower or "amateur" in lower:
            templates["champ/rookie/amateur"] += 1
        if "next?" in lower or "next!" in lower:
            templates["next?"] += 1
        if re.search(r"[😏😂🔒🎉💪🚀]", t):
            templates["emoji response"] += 1
        if "first" in lower and ("char" in lower or "letter" in lower or "word" in lower):
            templates["first char/letter/word"] += 1
        if "cost" in lower or "price" in lower:
            templates["cost/price"] += 1
        if "vault" in lower or "lock" in lower:
            templates["vault/lock"] += 1
        if "fishing" in lower or "bait" in lower:
            templates["fishing/bait"] += 1
        if "laugh" in lower:
            templates["laugh"] += 1
        if "swinging" in lower or "swing" in lower:
            templates["swinging"] += 1
        if "happening" in lower:
            templates["happening"] += 1
        if "bait" in lower:
            templates["bait"] += 1

    for tmpl, count in templates.most_common():
        if count >= 2:
            print(f"  {tmpl:30s} {count:3d} volte")

    # ── 7. PASSPHRASE FRAGMENT DETECTION ──
    print("\n" + "=" * 90)
    print("7. RICERCA FRAMMENTI DELLA PASSPHRASE NELLE RISPOSTE")
    print("=" * 90)
    passphrase_fragments = [
        "it may look like", "abc99", "de12f", "gh1jk", "lmn0p",
        "yours may be", "shorter or longer", "abc", "de12", "gh1", "lmn",
        "may look", "look like", "shorter", "longer",
        "99", "12", "0p", "jk",
    ]
    for frag in passphrase_fragments:
        matches = [(i, r) for i, r in enumerate(rows, 1) if frag.lower() in r["text"].lower()]
        if matches:
            print(f"\n  FRAGMENT '{frag}' trovato in {len(matches)} tweet:")
            for idx, r in matches:
                print(f"    [{idx}] {r['text']}")
        else:
            print(f"  '{frag}' -> NON trovato")

    # ── 8. EMOJI FREQUENCY ──
    print("\n" + "=" * 90)
    print("8. FREQUENZA EMOJI")
    print("=" * 90)
    emojis = []
    for t in texts:
        emojis.extend(re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002702-\U000027B0\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]", t))
    emoji_count = Counter(emojis)
    for emoji, count in emoji_count.most_common(10):
        print(f"  {emoji}  x{count}")

    # ── 9. RESPONSE LENGTH DISTRIBUTION ──
    print("\n" + "=" * 90)
    print("9. DISTRIBUZIONE LUNGHEZZA RISPOSTE")
    print("=" * 90)
    lengths = [len(t) for t in texts]
    avg = sum(lengths) / len(lengths)
    short = sum(1 for l in lengths if l < 60)
    medium = sum(1 for l in lengths if 60 <= l < 120)
    long = sum(1 for l in lengths if l >= 120)
    print(f"  Media: {avg:.0f} caratteri")
    print(f"  Corte (<60 chars): {short}")
    print(f"  Medie (60-120):    {medium}")
    print(f"  Lunghe (>120):     {long}")
    print(f"  Min: {min(lengths)}, Max: {max(lengths)}")

    # ── 10. HIDDEN PATTERNS / ENCODING DETECTION ──
    print("\n" + "=" * 90)
    print("10. RICERCA PATTERNS NASCOSTI / CODIFICHE")
    print("=" * 90)
    for i, t in enumerate(texts, 1):
        # Check for hex-like patterns
        hex_matches = re.findall(r"[0-9a-fA-F]{4,}", t)
        if hex_matches:
            print(f"  [{i}] Pattern hex: {hex_matches}  -> {t[:80]}")
        # Check for dash-separated patterns like abc99-de12f
        dash_patterns = re.findall(r"[a-z]{2,3}\d{1,3}-[a-z]{2,3}\d{1,3}", t.lower())
        if dash_patterns:
            print(f"  [{i}] Pattern XX##-XX##: {dash_patterns}  -> {t[:80]}")
        # Check for repeated characters
        rep_chars = re.findall(r"(.)\1{2,}", t)
        if rep_chars:
            print(f"  [{i}] Char ripetuti: {set(rep_chars)}  -> {t[:80]}")

    # ── 11. SENTIMENT / DEFENSIVE PATTERNS ──
    print("\n" + "=" * 90)
    print("11. CLASSIFICAZIONE RISPOSTE DEFENSIVE")
    print("=" * 90)
    defensive = Counter()
    for t in texts:
        lower = t.lower()
        if any(w in lower for w in ["no", "nope", "not happening", "not going", "won't", "can't"]):
            defensive["Rifiuto diretto"] += 1
        if any(w in lower for w in ["nice try", "cute try", "good try", "nice one"]):
            defensive["Sfida/dileggio"] += 1
        if any(w in lower for w in ["locked", "sealed", "vault", "secure"]):
            defensive["Sicurezza/garanzia"] += 1
        if any(w in lower for w in ["next", "try again", "try harder"]):
            defensive["Sfida a riprovare"] += 1
        if any(w in lower for w in ["bored", "boring", "same old"]):
            defensive["Noia/frustrazione"] += 1
        if any(w in lower for w in ["laugh", "lol", "haha"]):
            defensive["Risata/derisione"] += 1
        if any(w in lower for w in ["hypothetical", "what if"]):
            defensive["Rifiuto ipotetico"] += 1
    for cat, count in defensive.most_common():
        print(f"  {cat:30s} {count:3d}")

    print("\n" + "=" * 90)
    print("ANALISI COMPLETATA")
    print("=" * 90)


if __name__ == "__main__":
    analysis()
