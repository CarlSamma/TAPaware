"""Merge all tweets into database and regenerate CSV."""

import json
import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "tap.db"
HISTORICAL_PATH = DATA_DIR / "hackinga0_historical_fixed.json"
OUTPUT_CSV = DATA_DIR / "tapping_hackinga0_full.csv"

# 1. Load historical tweets
with open(HISTORICAL_PATH, "r", encoding="utf-8") as f:
    historical = json.load(f)["tweets"]
print(f"Historical tweets loaded: {len(historical)}")

# 2. Load existing tweets from DB
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()
cursor.execute("SELECT id FROM tweets")
existing_ids = {row[0] for row in cursor.fetchall()}
print(f"Existing tweets in DB: {len(existing_ids)}")

# 3. Insert new tweets from historical into DB
new_count = 0
for tweet in historical:
    tid = tweet.get("id", "")
    if tid in existing_ids:
        continue

    # Determine source
    author_id = str(tweet.get("author_id", ""))
    mentions = tweet.get("entities", {}).get("mentions", [])
    mention_usernames = [m.get("username", "") for m in mentions]

    if author_id == "2051911746969812998":
        source = "target_bot"
        username = "hackingA0"
    else:
        source = "other_user"
        username = mention_usernames[0] if mention_usernames else "unknown"

    reply_to = tweet.get("in_reply_to_user_id", None)
    text = tweet.get("text", "")
    created_at = tweet.get("created_at", "")
    conv_id = tweet.get("conversation_id", None)

    try:
        cursor.execute(
            """INSERT OR REPLACE INTO tweets
               (id, user_id, username, text, in_reply_to_tweet_id,
                created_at, source, conversation_thread_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tid, author_id, username, text, reply_to, created_at, source, conv_id),
        )
        new_count += 1
    except Exception as e:
        print(f"Error inserting {tid}: {e}")

conn.commit()
print(f"New tweets inserted: {new_count}")

# 4. Get final stats
cursor.execute("SELECT source, COUNT(*) FROM tweets GROUP BY source")
stats = dict(cursor.fetchall())
cursor.execute("SELECT COUNT(*) FROM tweets")
total = cursor.fetchone()[0]
conn.close()

print(f"\nFinal DB stats:")
for source, count in sorted(stats.items()):
    print(f"  {source}: {count}")
print(f"  TOTAL: {total}")

# 5. Regenerate full CSV
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT
        t.id, t.user_id, t.username, t.text, t.in_reply_to_tweet_id,
        t.created_at, t.source, t.conversation_thread_id,
        n.branch_strategy, n.dpa_frame, n.aliases_used, n.judge_score,
        n.pattern_class, n.binary_outcome, n.property_tested, n.property_value,
        n.signal_reliability, n.pruned, n.pruned_reason, n.gamma_score,
        n.gamma_breakdown, n.technique_used, n.created_at as node_created_at
    FROM tweets t
    LEFT JOIN nodes n ON t.id = n.tweet_id
    ORDER BY t.created_at ASC
""")
rows = cursor.fetchall()
conn.close()

fieldnames = [
    "tweet_id", "user_id", "username", "text", "in_reply_to_tweet_id",
    "created_at", "source", "conversation_thread_id",
    "branch_strategy", "dpa_frame", "aliases_used", "judge_score",
    "pattern_class", "binary_outcome", "property_tested", "property_value",
    "signal_reliability", "pruned", "pruned_reason", "gamma_score",
    "gamma_breakdown", "technique_used", "node_created_at"
]

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "tweet_id": row["id"],
            "user_id": row["user_id"],
            "username": row["username"],
            "text": row["text"],
            "in_reply_to_tweet_id": row["in_reply_to_tweet_id"] or "",
            "created_at": row["created_at"],
            "source": row["source"],
            "conversation_thread_id": row["conversation_thread_id"] or "",
            "branch_strategy": row["branch_strategy"] or "",
            "dpa_frame": row["dpa_frame"] or "",
            "aliases_used": row["aliases_used"] or "",
            "judge_score": row["judge_score"] if row["judge_score"] is not None else "",
            "pattern_class": row["pattern_class"] or "",
            "binary_outcome": row["binary_outcome"] or "",
            "property_tested": row["property_tested"] or "",
            "property_value": row["property_value"] or "",
            "signal_reliability": row["signal_reliability"] if row["signal_reliability"] is not None else "",
            "pruned": row["pruned"] if row["pruned"] is not None else "",
            "pruned_reason": row["pruned_reason"] or "",
            "gamma_score": row["gamma_score"] if row["gamma_score"] is not None else "",
            "gamma_breakdown": row["gamma_breakdown"] or "",
            "technique_used": row["technique_used"] or "",
            "node_created_at": row["node_created_at"] or ""
        })

print(f"\nCSV regenerated: {len(rows)} rows -> {OUTPUT_CSV}")
