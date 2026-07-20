"""Extract tweets table data and generate CSV with posts, replies, and SSOT info."""

import csv
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "tap.db"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "tapping_hackinga0.csv"


def extract_data():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all tweets with node data (LEFT JOIN for probe metadata)
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

    # Get properties (SSOT confirmed/denied)
    cursor.execute("SELECT * FROM properties ORDER BY confirmed_at ASC")
    properties = cursor.fetchall()

    # Get candidate graph nodes
    cursor.execute("SELECT * FROM candidate_graph_nodes ORDER BY recorded_at ASC")
    candidate_graph = cursor.fetchall()

    # Get probe memory
    cursor.execute("SELECT * FROM probe_memory ORDER BY recorded_at DESC")
    probe_memory = cursor.fetchall()

    conn.close()

    if not rows:
        print("No tweets found in database.")
        return

    # Write main CSV
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

    print(f"Extracted {len(rows)} tweets to {OUTPUT_CSV}")

    # Summary by source
    sources = {}
    for row in rows:
        src = row["source"]
        sources[src] = sources.get(src, 0) + 1

    print("\nBreakdown by source:")
    for src, count in sorted(sources.items()):
        print(f"  {src}: {count}")

    # Stats
    with_reply = sum(1 for r in rows if r["in_reply_to_tweet_id"])
    print(f"\nWith reply link: {with_reply}")
    print(f"Properties (SSOT): {len(properties)}")
    print(f"Candidate graph nodes: {len(candidate_graph)}")
    print(f"Probe memory entries: {len(probe_memory)}")


if __name__ == "__main__":
    extract_data()
