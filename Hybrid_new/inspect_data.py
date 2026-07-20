import asyncio
import os
import sys

# Reconfigure stdout to handle emojis and other unicode characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tap.config import get_settings
from tap.db import Database
from tap.x_client import TwitterClient

async def main():
    settings = get_settings()
    print("=== Configurations ===")
    print(f"Database Path: {settings.db_path}")
    print(f"Target Handle: {settings.target_handle}")
    print(f"Our Bot Handle: {settings.our_bot_handle}")
    print(f"OpenRouter Model Primary: {settings.openrouter_model_primary}")
    print(f"OpenRouter Model Hard: {settings.openrouter_model_hard}")

    db = Database(settings.db_path)
    await db.initialize()

    print("\n=== Database Statistics ===")
    stats = await db.get_stats()
    print(stats)

    print("\n=== Recent Tweets ===")
    tweets = await db.get_tweets(limit=10)
    for t in tweets:
        print(f"[{t.id}] @{t.username} ({t.source.value}): {t.text[:100]}")

    print("\n=== Active Nodes ===")
    nodes = await db.get_active_nodes(limit=10)
    for n in nodes:
        print(f"Node ID: {n.id}, Tweet ID: {n.tweet_id}, Score: {n.judge_score}, Property Tested: {n.property_tested}, Outcome: {n.binary_outcome}")

    print("\n=== Testing Twitter Client ===")
    client = TwitterClient(settings)
    
    # Let's test target user resolution
    print("Resolving target user ID...")
    try:
        user_id = await client._resolve_target_user_id()
        print(f"Resolved target user ID: {user_id}")
    except Exception as e:
        print(f"Failed to resolve target user: {e}")

    print("\nTesting search API...")
    try:
        results = await client.initialize_seed(limit=15)
        print(f"Successfully retrieved {len(results)} tweets via seed search.")
        for r in results:
            print(f" - [{r.id}] @{r.username} (source={r.source.value}): {r.text[:80]}")
    except Exception as e:
        print(f"Failed to perform search: {e}")

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
