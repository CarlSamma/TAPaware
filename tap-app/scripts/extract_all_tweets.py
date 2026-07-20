"""Extract all tweets from historical file with better parsing."""
from pathlib import Path
import json
import re

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# Count total occurrences of "conversation_id" to estimate tweet count
tweet_count_estimate = content.count('"conversation_id"')
print(f"Estimated tweets (by conversation_id count): {tweet_count_estimate}")

# Try a different approach - use finditer to find tweet objects
# Each tweet starts with { and has "id" field
tweets = []

# Find all positions where tweet objects start
# Pattern: { followed by spaces and "conversation_id" or "entities"
pattern = re.compile(r'\{\s*"(?:conversation_id|entities)"')
for match in pattern.finditer(content):
    start = match.start()
    
    # Find matching closing brace
    depth = 0
    j = start
    while j < len(content):
        if content[j] == '{':
            depth += 1
        elif content[j] == '}':
            depth -= 1
            if depth == 0:
                break
        elif content[j] == '"':
            # Skip string content
            j += 1
            while j < len(content) and content[j] != '"':
                if content[j] == '\\':
                    j += 1  # Skip escaped character
                j += 1
        j += 1
    
    if depth == 0:
        tweet_str = content[start:j+1]
        try:
            tweet = json.loads(tweet_str)
            if 'id' in tweet:
                tweets.append(tweet)
        except json.JSONDecodeError:
            # Try to fix common issues
            # Fix unescaped quotes in text field
            text_match = re.search(r'"text":\s*"((?:[^"\\]|\\.)*)"', tweet_str)
            if text_match:
                text_content = text_match.group(1)
                # Check for unescaped quotes (not preceded by \)
                unescaped_quotes = re.findall(r'(?<!\\)"', text_content)
                if unescaped_quotes:
                    # Fix: escape all unescaped quotes
                    fixed_text = re.sub(r'(?<!\\)"', '\\"', text_content)
                    fixed_str = tweet_str[:text_match.start(1)] + fixed_text + tweet_str[text_match.end(1):]
                    try:
                        tweet = json.loads(fixed_str)
                        if 'id' in tweet:
                            tweets.append(tweet)
                    except:
                        pass

print(f"Extracted {len(tweets)} tweets")

if tweets:
    # Deduplicate by ID
    seen_ids = set()
    unique_tweets = []
    for t in tweets:
        tid = t.get('id')
        if tid and tid not in seen_ids:
            seen_ids.add(tid)
            unique_tweets.append(t)
    
    print(f"Unique tweets: {len(unique_tweets)}")
    
    # Save to proper JSON
    out_path = Path(__file__).parent.parent / "data" / "hackinga0_historical_fixed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(unique_tweets), "tweets": unique_tweets}, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out_path}")
    
    # Show stats
    dates = [t.get('created_at', '') for t in unique_tweets]
    print(f"\nDate range: {min(dates)} to {max(dates)}")
    
    # Count by author
    authors = {}
    for t in unique_tweets:
        aid = t.get('author_id', 'unknown')
        authors[aid] = authors.get(aid, 0) + 1
    print(f"\nAuthors:")
    for aid, count in sorted(authors.items(), key=lambda x: -x[1]):
        print(f"  {aid}: {count}")
