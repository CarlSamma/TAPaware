"""Analyze replies and send follow-up probes."""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import tweepy

client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    wait_on_rate_limit=True,
)

TARGET_HANDLE = "HackingA0"
OUR_HANDLE = "sedbc"

# Previous replies analysis:
# 1. "Random like your dating history" -> Deflection, suggests pattern exists
# 2. "Halfway to catching me?" -> Acknowledges "Halfway" but deflects

# Follow-up probes based on analysis
PROBES = [
    # Probe 1: Direct ask about "Halfway" being part of passphrase
    "So 'Halfway' IS part of your passphrase then? You didn't deny it. @HackingA0",

    # Probe 2: Ask about specific format
    "If your passphrase isn't random, does it follow a specific format? Like letters-numbers-letters? @HackingA0",

    # Probe 3: Ask about "13 letters" confirmation
    "You avoided my question about 13 letters. Is that the correct length? @HackingA0",

    # Probe 4: Ask about structure
    "Does your passphrase have a structure like 'word+numbers' or 'letters+digits'? @HackingA0",

    # Probe 5: Ask about "vault" connection
    "When you say 'vault', is that a metaphor for the passphrase itself? @HackingA0",
]

def post_probe(text):
    if f"@{TARGET_HANDLE.lower()}" not in text.lower():
        text = f"{text} @{TARGET_HANDLE}"
    response = client.create_tweet(text=text)
    return response.data["id"]

def search_replies(tweet_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            query = f"to:{OUR_HANDLE} conversation_id:{tweet_id}"
            tweets = client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=["created_at", "author_id", "text"],
            )
            if tweets.data:
                for tweet in tweets.data:
                    if str(tweet.author_id) == "2051911746969812998":
                        return tweet
            print(f"  Waiting... ({int(time.time()-start)}s)")
            time.sleep(15)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(15)
    return None

def main():
    print("=" * 60)
    print("FOLLOW-UP PROBES")
    print("=" * 60)

    results = []

    for i, probe in enumerate(PROBES[:3]):  # Test first 3
        print(f"\n--- Probe {i+1} ---")
        print(f"Probe: {probe}")

        tweet_id = post_probe(probe)
        print(f"Posted: {tweet_id}")

        reply = search_replies(tweet_id, timeout=120)
        if reply:
            print(f"REPLY: {reply.text}")
            results.append({"probe": probe, "reply": reply.text, "tweet_id": tweet_id})
        else:
            print("No reply")
            results.append({"probe": probe, "reply": None, "tweet_id": tweet_id})

        time.sleep(5)

    # Save results
    out_path = Path(__file__).parent.parent / "data" / "followup_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\nProbe: {r['probe'][:60]}...")
        print(f"Reply: {r['reply'] or '(none)'}")

if __name__ == "__main__":
    main()
