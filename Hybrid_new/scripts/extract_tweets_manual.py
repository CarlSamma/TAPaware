"""Parse historical tweets with a more robust approach."""
from pathlib import Path
import json
import re

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# Strategy: Extract each tweet manually using regex
# Pattern for a tweet object
tweet_pattern = r'\{[^{}]*"id"\s*:\s*"[^"]*"[^{}]*\}'

# Actually, let's try a different approach - split by tweet boundaries
# Each tweet starts with { "conversation_id" and ends with }

# Find all tweet-like objects
tweets = []
i = 0
while i < len(content):
    # Find next tweet start
    start = content.find('{ "conversation_id":', i)
    if start == -1:
        break
    
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
        j += 1
    
    if depth == 0:
        tweet_str = content[start:j+1]
        try:
            tweet = json.loads(tweet_str)
            tweets.append(tweet)
        except json.JSONDecodeError:
            # Try to fix common issues
            # Fix unescaped quotes in text
            fixed = tweet_str
            # Find "text": "..." and fix inner quotes
            text_match = re.search(r'"text":\s*"((?:[^"\\]|\\.)*)"', fixed)
            if text_match:
                text_content = text_match.group(1)
                # Check for unescaped quotes
                if '"' in text_content.replace('\\"', ''):
                    # Fix unescaped quotes
                    fixed_text = re.sub(r'(?<!\\)"', '\\"', text_content)
                    fixed = fixed[:text_match.start(1)] + fixed_text + fixed[text_match.end(1):]
                    try:
                        tweet = json.loads(fixed)
                        tweets.append(tweet)
                    except:
                        pass
        
        i = j + 1
    else:
        i = len(content)

print(f"Extracted {len(tweets)} tweets")

if tweets:
    # Save to proper JSON
    out_path = Path(__file__).parent.parent / "data" / "hackinga0_historical_fixed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(tweets), "tweets": tweets}, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out_path}")
    
    # Show first 3 tweets
    for i, t in enumerate(tweets[:3]):
        print(f"\n[{i+1}] ID: {t.get('id')}")
        print(f"    Created: {t.get('created_at')}")
        print(f"    Text: {t.get('text', '')[:100]}")
