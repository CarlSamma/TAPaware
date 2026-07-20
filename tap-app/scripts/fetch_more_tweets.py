"""Fetch 150 more tweets from @HackingA0 via Twitter API v2 with pagination, store in DB, and regenerate CSV."""

import asyncio
import csv
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tweepy
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DB_PATH = Path(__file__).parent.parent / "data" / "tap.db"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "tapping_hackinga0.csv"
TARGET_HANDLE = "HackingA0"

# Twitter API credentials from .env
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")


def classify_source(author_id: str, target_user_id: str, our_user_id: str = "") -> str:
    """Classify tweet source based on author ID."""
    if author_id == target_user_id:
        return "target_bot"
    if our_user_id and author_id == our_user_id:
        return "our_bot"
    return "other_user"


def get_reply_to_id(tweet_data) -> str | None:
    """Extract in_reply_to_tweet_id from tweet data."""
    if hasattr(tweet_data, "referenced_tweets") and tweet_data.referenced_tweets:
        for ref in tweet_data.referenced_tweets:
            if ref.type == "replied_to":
                return str(ref.id)
    return None


async def fetch_tweets_with_pagination(target_count: int = 150) -> list[dict]:
    """Fetch tweets using Twitter API v2 with pagination."""
    if not BEARER_TOKEN:
        print("ERROR: TWITTER_BEARER_TOKEN not found in .env")
        return []

    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        wait_on_rate_limit=True,
    )

    # Resolve target user ID
    print(f"Resolving user ID for @{TARGET_HANDLE}...")
    try:
        user = client.get_user(username=TARGET_HANDLE)
        if not user.data:
            print(f"ERROR: Could not find user @{TARGET_HANDLE}")
            return []
        target_user_id = str(user.data.id)
        print(f"Target user ID: {target_user_id}")
    except Exception as e:
        print(f"ERROR resolving user: {e}")
        return []

    query = f"to:{TARGET_HANDLE} OR from:{TARGET_HANDLE}"
    all_tweets = []
    next_token = None
    page = 0

    while len(all_tweets) < target_count:
        page += 1
        max_results = min(100, target_count - len(all_tweets))
        print(f"Page {page}: Fetching up to {max_results} tweets (total so far: {len(all_tweets)})...")

        try:
            response = client.search_recent_tweets(
                query=query,
                max_results=max_results,
                next_token=next_token,
                tweet_fields=["created_at", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
                expansions=["author_id", "referenced_tweets.id"],
            )

            if not response.data:
                print("No more tweets found.")
                break

            # Build user lookup
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = user.username

            for tweet_data in response.data:
                author_id = str(tweet_data.author_id) if hasattr(tweet_data, "author_id") else ""
                username = users.get(tweet_data.author_id, "unknown") if hasattr(tweet_data, "author_id") else "unknown"
                source = classify_source(author_id, target_user_id)

                tweet = {
                    "id": str(tweet_data.id),
                    "user_id": author_id,
                    "username": username,
                    "text": tweet_data.text,
                    "in_reply_to_tweet_id": get_reply_to_id(tweet_data),
                    "created_at": (tweet_data.created_at or datetime.now(timezone.utc)).isoformat(),
                    "source": source,
                    "conversation_thread_id": str(tweet_data.conversation_id)
                    if hasattr(tweet_data, "conversation_id") and tweet_data.conversation_id
                    else None,
                }
                all_tweets.append(tweet)

            # Check for next page
            if response.meta and "next_token" in response.meta:
                next_token = response.meta["next_token"]
            else:
                print("No more pages available.")
                break

        except Exception as e:
            print(f"ERROR on page {page}: {e}")
            break

    print(f"\nTotal tweets fetched: {len(all_tweets)}")
    return all_tweets


def store_tweets_in_db(tweets: list[dict]) -> int:
    """Store tweets in SQLite database, return count of new tweets."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    new_count = 0
    for tweet in tweets:
        # Check if tweet already exists
        cursor.execute("SELECT 1 FROM tweets WHERE id = ?", (tweet["id"],))
        if cursor.fetchone():
            continue
        
        cursor.execute(
            """INSERT OR REPLACE INTO tweets
               (id, user_id, username, text, in_reply_to_tweet_id,
                created_at, source, conversation_thread_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tweet["id"],
                tweet["user_id"],
                tweet["username"],
                tweet["text"],
                tweet["in_reply_to_tweet_id"],
                tweet["created_at"],
                tweet["source"],
                tweet["conversation_thread_id"],
            ),
        )
        new_count += 1
    
    conn.commit()
    conn.close()
    return new_count


def regenerate_csv():
    """Regenerate the CSV from the database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            t.id,
            t.user_id,
            t.username,
            t.text,
            t.in_reply_to_tweet_id,
            t.created_at,
            t.source,
            t.conversation_thread_id,
            n.branch_strategy,
            n.dpa_frame,
            n.aliases_used,
            n.judge_score,
            n.pattern_class,
            n.binary_outcome,
            n.property_tested,
            n.property_value,
            n.signal_reliability,
            n.pruned,
            n.pruned_reason,
            n.gamma_score,
            n.gamma_breakdown,
            n.technique_used,
            n.created_at as node_created_at
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

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

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


async def main():
    print("=" * 60)
    print("TAP Framework - Tweet Fetcher")
    print("=" * 60)

    # Fetch tweets
    tweets = await fetch_tweets_with_pagination(target_count=150)
    
    if not tweets:
        print("No tweets fetched. Exiting.")
        return

    # Store in database
    new_count = store_tweets_in_db(tweets)
    print(f"\nStored {new_count} new tweets in database")

    # Regenerate CSV
    total_rows = regenerate_csv()
    print(f"Regenerated CSV with {total_rows} total rows")

    # Final stats
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT source, COUNT(*) FROM tweets GROUP BY source")
    stats = dict(cursor.fetchall())
    conn.close()

    print("\nFinal breakdown:")
    for source, count in sorted(stats.items()):
        print(f"  {source}: {count}")
    print(f"  TOTAL: {sum(stats.values())}")


if __name__ == "__main__":
    asyncio.run(main())
