"""Parse and analyze the historical tweets JSON file."""

import json
from pathlib import Path

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# Find the JSON part
lines = content.strip().split("\n")
json_line = lines[0] if lines[0].startswith("{") else lines[1]

data = json.loads(json_line)
total = data["total"]
tweets = data["tweets"]

print(f"Total tweets declared: {total}")
print(f"Tweets in array: {len(tweets)}")

# Show first 5 tweets
for i, tweet in enumerate(tweets[:5]):
    print(f"\n[{i+1}] ID: {tweet['id']}")
    print(f"    Created: {tweet['created_at']}")
    print(f"    Text: {tweet['text'][:120]}")
    if "entities" in tweet and "mentions" in tweet["entities"]:
        mentions = [m["username"] for m in tweet["entities"]["mentions"]]
        print(f"    Mentions: {mentions}")

# Date range
dates = [t["created_at"] for t in tweets]
print(f"\nDate range: {min(dates)} to {max(dates)}")

# Unique authors
authors = set()
for t in tweets:
    authors.add(t.get("author_id", "unknown"))
print(f"Unique author IDs: {len(authors)}")

# Check for replies
replies = [t for t in tweets if t.get("in_reply_to_user_id")]
print(f"Tweets with reply target: {len(replies)}")

# Save to CSV for merging
import csv
csv_path = Path(__file__).parent.parent / "data" / "hackinga0_historical.csv"

fieldnames = ["id", "author_id", "in_reply_to_user_id", "created_at", "text", "conversation_id"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for tweet in tweets:
        writer.writerow({
            "id": tweet.get("id", ""),
            "author_id": tweet.get("author_id", ""),
            "in_reply_to_user_id": tweet.get("in_reply_to_user_id", ""),
            "created_at": tweet.get("created_at", ""),
            "text": tweet.get("text", ""),
            "conversation_id": tweet.get("conversation_id", ""),
        })

print(f"\nSaved {len(tweets)} tweets to {csv_path}")
