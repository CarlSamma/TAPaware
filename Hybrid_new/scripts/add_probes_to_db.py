"""Add new probes and replies to database and regenerate CSV."""

import os
import sys
import json
import csv
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import tweepy

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "tap.db"
PROBES_FILE = DATA_DIR / "all_probes_and_replies.json"
OUTPUT_CSV = DATA_DIR / "tapping_hackinga0_full.csv"

# Twitter client
client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    wait_on_rate_limit=True,
)

OUR_USER_ID = "880902458"  # @sedbc
TARGET_USER_ID = "2051911746969812998"  # @HackingA0

def load_probes():
    with open(PROBES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_existing_ids():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tweets")
    ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return ids

def fetch_tweet(tweet_id):
    """Fetch a tweet by ID."""
    try:
        tweet = client.get_tweet(
            tweet_id,
            tweet_fields=["created_at", "author_id", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
            expansions=["author_id"],
        )
        if tweet.data:
            return tweet.data
    except Exception as e:
        print(f"  Error fetching {tweet_id}: {e}")
    return None

def insert_tweet(tweet_data, source, username):
    """Insert a tweet into the database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR REPLACE INTO tweets
               (id, user_id, username, text, in_reply_to_tweet_id,
                created_at, source, conversation_thread_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(tweet_data.id),
                str(tweet_data.author_id),
                username,
                tweet_data.text,
                None,  # Will be set if it's a reply
                tweet_data.created_at.isoformat() if tweet_data.created_at else None,
                source,
                str(tweet_data.conversation_id) if hasattr(tweet_data, "conversation_id") else None,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"  Error inserting: {e}")
        return False
    finally:
        conn.close()

def regenerate_csv():
    """Regenerate the CSV from the database."""
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

    return len(rows)

def main():
    print("=" * 60)
    print("ADDING NEW PROBES TO DATABASE")
    print("=" * 60)

    # Load probes
    probes_data = load_probes()
    probes = probes_data["probes_and_replies"]
    print(f"Loaded {len(probes)} probes from file")

    # Get existing IDs
    existing_ids = get_existing_ids()
    print(f"Existing tweets in DB: {len(existing_ids)}")

    # Collect new tweet IDs to fetch
    new_tweet_ids = set()
    for p in probes:
        tid = str(p.get("tweet_id", ""))
        if tid and tid not in existing_ids:
            new_tweet_ids.add(tid)
        # Also add reply IDs
        rid = p.get("reply_id")
        if rid and str(rid) not in existing_ids:
            new_tweet_ids.add(str(rid))

    print(f"New tweets to fetch: {len(new_tweet_ids)}")

    # Fetch and insert tweets
    added = 0
    for tid in new_tweet_ids:
        print(f"\nFetching {tid}...")
        tweet = fetch_tweet(tid)
        if tweet:
            # Determine source
            author_id = str(tweet.author_id)
            if author_id == TARGET_USER_ID:
                source = "target_bot"
                username = "hackingA0"
            elif author_id == OUR_USER_ID:
                source = "our_bot"
                username = "sedbc"
            else:
                source = "other_user"
                username = "unknown"

            if insert_tweet(tweet, source, username):
                added += 1
                print(f"  Added: {source} - {tweet.text[:60]}...")

    print(f"\nAdded {added} new tweets")

    # Regenerate CSV
    total = regenerate_csv()
    print(f"CSV regenerated: {total} rows")

    # Final stats
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT source, COUNT(*) FROM tweets GROUP BY source")
    stats = dict(cursor.fetchall())
    conn.close()

    print("\nFinal DB stats:")
    for source, count in sorted(stats.items()):
        print(f"  {source}: {count}")
    print(f"  TOTAL: {sum(stats.values())}")

if __name__ == "__main__":
    main()
