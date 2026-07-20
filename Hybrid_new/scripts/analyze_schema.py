"""Analyze @HackingA0 responses to find encoding patterns that could map to passphrase format abc99-de12f-gh1jk-lmn0p."""

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

PASSPHRASE = "It may look like abc99-de12f-gh1jk-lmn0p; yours may be shorter or longer."
PASSPHRASE_BLOCKS = ["abc99", "de12f", "gh1jk", "lmn0p"]

csv_path = Path(__file__).parent.parent / "data" / "tapping_hackinga0_full.csv"


def load_target():
    with open(csv_path, "r", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["source"] == "target_bot"]


def analyze():
    rows = load_target()
    texts = [r["text"] for r in rows]
    clean = []
    for t in texts:
        c = re.sub(r"@\w+", "", t)
        c = re.sub(r"https?://\S+", "", c)
        c = re.sub(r"[^\w\s.,!?'\":;()-]", "", c)
        clean.append(c.strip())

    print("=" * 90)
    print("SCHEMA ANALYSIS: Come i pattern delle risposte potrebbero mappare")
    print("alla passphrase abc99-de12f-gh1jk-lmn0p")
    print("=" * 90)

    # ══════════════════════════════════════════════════════════════════
    # 1. PRIMA LETTERA DI OGNI RISPOSTA
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("1. PRIMA LETTERA DI OGNI RISPOSTA (acronimo)")
    print("=" * 90)
    first_letters = ""
    for i, t in enumerate(texts, 1):
        fl = re.search(r"[a-zA-Z]", t)
        if fl:
            first_letters += fl.group().lower()
            print(f"  [{i:2d}] '{fl.group()}' <- {t[:60]}")
        else:
            print(f"  [{i:2d}] '?' <- {t[:60]}")
    print(f"\n  Sequenza: {first_letters}")
    # Check if any blocks match passphrase patterns
    for block in PASSPHRASE_BLOCKS:
        if block in first_letters:
            print(f"  *** MATCH: '{block}' trovato nella sequenza!")

    # ══════════════════════════════════════════════════════════════════
    # 2. ULTIMA LETTERA DI OGNI RISPOSTA
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("2. ULTIMA LETTERA DI OGNI RISPOSTA")
    print("=" * 90)
    last_letters = ""
    for i, t in enumerate(texts, 1):
        fl = re.findall(r"[a-zA-Z]", t)
        if fl:
            last_letters += fl[-1].lower()
    print(f"  Sequenza: {last_letters}")

    # ══════════════════════════════════════════════════════════════════
    # 3. NOME UTENTE INVOCATO — lettere estratte
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("3. NOME UTENTE NELLA RISPOSTA — estrai lettere")
    print("=" * 90)
    # For each response, extract the @name mentioned (first word usually)
    name_chars = ""
    for i, t in enumerate(texts, 1):
        # Extract first @mention or first word after @
        mention = re.search(r"@(\w+)", t)
        if mention:
            name = mention.group(1)
            # Take only letters, skip digits/special
            letters = re.sub(r"[^a-zA-Z]", "", name).lower()
            name_chars += letters[-1] if letters else "?"
            print(f"  [{i:2d}] @{name} -> last letter '{letters[-1] if letters else '?'}'")
    print(f"\n  Sequenza (ultima lettera di ogni username): {name_chars}")

    # ══════════════════════════════════════════════════════════════════
    # 4. PAROLE CHIAVE fisse — posizione nella passphrase
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("4. PAROLE fisse nelle risposte e posizione")
    print("=" * 90)
    keywords = ["nice", "try", "cute", "bold", "fishing", "bait", "locked",
                "sealed", "vault", "harder", "sherlock", "debug", "next",
                "hypothetical", "look", "like", "first", "chars", "nope"]
    for kw in keywords:
        positions = []
        for i, c in enumerate(clean):
            if re.search(rf"\b{kw}\b", c, re.IGNORECASE):
                positions.append(i + 1)
        if positions:
            print(f"  '{kw}' -> {len(positions)} volte, pos: {positions}")

    # ══════════════════════════════════════════════════════════════════
    # 5. NUMERI nelle risposte
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("5. NUMERI TROVATI NELLE RISPOSTE")
    print("=" * 90)
    for i, t in enumerate(texts, 1):
        nums = re.findall(r"\d+", t)
        if nums:
            print(f"  [{i:2d}] {str(nums):20s} <- {t[:60]}")

    # ══════════════════════════════════════════════════════════════════
    # 6. PAROLE CHE CONTENGONO CIFRE (tipo passXYZ99)
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("6. PAROLE CON CIFRE EMBEDED (pattern XX##)")
    print("=" * 90)
    for i, t in enumerate(texts, 1):
        # Words mixing letters and digits
        mixed = re.findall(r"[a-zA-Z]+\d+[a-zA-Z]*|[a-zA-Z]*\d+[a-zA-Z]+", t)
        if mixed:
            print(f"  [{i:2d}] {mixed} <- {t[:70]}")

    # ══════════════════════════════════════════════════════════════════
    # 7. LUNGHEZZA PAROLE — mappatura a cifre
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("7. LUNGHEZZA PAROLE (potrebbe codificare numeri)")
    print("=" * 90)
    # "Nice try" -> [4, 3] -> 43?  Nope -> [4] -> 4?
    for i, c in enumerate(clean[:20], 1):
        words = c.split()
        lengths = [len(re.sub(r"[^a-zA-Z]", "", w)) for w in words if re.sub(r"[^a-zA-Z]", "", w)]
        if lengths:
            print(f"  [{i:2d}] parole={lengths} somma={sum(lengths)} <- {c[:50]}")

    # ══════════════════════════════════════════════════════════════════
    # 8. SEZIONI DELLA PASSPHRASE — 4 blocchi indipendenti
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("8. IPOTESI: 4 GRUPPI DI RISPOSTE = 4 BLOCCHI PASSPHRASE")
    print(f"   Blocchi target: {PASSPHRASE_BLOCKS}")
    print("=" * 90)
    # Divide 84 risposte in 4 gruppi di 21
    chunk_size = len(texts) // 4
    for block_idx in range(4):
        start = block_idx * chunk_size
        end = start + chunk_size
        chunk = clean[start:end]
        chunk_texts = texts[start:end]

        # Extract all first letters from this chunk
        fls = ""
        for c in chunk:
            fl = re.search(r"[a-zA-Z]", c)
            if fl:
                fls += fl.group().lower()

        # Extract all last letters
        lls = ""
        for c in chunk:
            ll = re.findall(r"[a-zA-Z]", c)
            if ll:
                lls += ll[-1].lower()

        target_block = PASSPHRASE_BLOCKS[block_idx]
        print(f"\n  --- Blocco {block_idx+1}: target '{target_block}' (risposte {start+1}-{end}) ---")
        print(f"  Prime lettere:  {fls}")
        print(f"  Ultime lettere: {lls}")

        # Check for matching substrings
        for seq_name, seq in [("prime lettere", fls), ("ultime lettere", lls)]:
            if target_block in seq:
                print(f"  *** MATCH ESATTO '{target_block}' in {seq_name}!")
            # Check partial matches
            for i in range(len(target_block)):
                prefix = target_block[:i+1]
                if prefix in seq:
                    print(f"  ~~~ Prefisso '{prefix}' trovato in {seq_name}")

    # ══════════════════════════════════════════════════════════════════
    # 9. EMOJI MAP — ogni emoji = cifra?
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("9. MAPPA EMOJI (ogni emoji potrebbe = cifra)")
    print("=" * 90)
    emoji_list = []
    for t in texts:
        emojis = re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002702-\U000027B0\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]", t)
        if emojis:
            emoji_list.extend(emojis)

    emoji_counter = Counter(emoji_list)
    unique_emojis = sorted(emoji_counter.keys())
    print(f"  Emoji uniche: {len(unique_emojis)}")
    for e, c in emoji_counter.most_common():
        print(f"  {e}  x{c}")

    # ══════════════════════════════════════════════════════════════════
    # 10. SEQUENZA LETTERE A-O DA "look like" RESPONSES
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("10. ANALISI RISPOSTE 'HYPOTHETICAL' (contengono 'look like')")
    print("=" * 90)
    hypothetical = [(i, t) for i, t in enumerate(texts) if "look like" in t.lower() or "hypothetical" in t.lower()]
    for idx, t in hypothetical:
        # Extract words after "look like"
        match = re.search(r"look like ['\"]?(.*?)['\"]?[.,]", t, re.IGNORECASE)
        if match:
            print(f"  [{idx+1}] Dopo 'look like': '{match.group(1)}'  <- {t}")
        else:
            print(f"  [{idx+1}] {t}")

    # ══════════════════════════════════════════════════════════════════
    # 11. ANALISI "FIRST X CHARS" — cosa risponde?
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("11. RISPOSTE ALLA DOMANDA 'FIRST X CHARS'")
    print("=" * 90)
    for i, t in enumerate(texts, 1):
        lower = t.lower()
        if "first" in lower and ("char" in lower or "letter" in lower or "word" in lower or "0" in lower or "zero" in lower):
            print(f"  [{i:2d}] {t}")

    # ══════════════════════════════════════════════════════════════════
    # 12. PAROLE CHE APPARISSO SOLO 1 VOLTA (potenzialmente codificanti)
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("12. PAROLE UNICHE (hapax) — potenzialmente significative")
    print("=" * 90)
    all_words = []
    for c in clean:
        all_words.extend(re.findall(r"[a-zA-Z']+", c.lower()))
    word_freq = Counter(all_words)
    hapax = [(w, c) for w, c in word_freq.items() if c == 1]
    # Filter out very short or common words
    hapax_filtered = [(w, c) for w, c in hapax if len(w) > 3]
    hapax_filtered.sort(key=lambda x: x[0])
    for w, _ in hapax_filtered[:40]:
        print(f"  '{w}'")

    print("\n" + "=" * 90)
    print("ANALISI SCHEMA COMPLETATA")
    print("=" * 90)


if __name__ == "__main__":
    analyze()
