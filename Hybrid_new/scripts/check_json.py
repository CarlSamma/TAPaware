"""Check JSON validity around position 54915."""
from pathlib import Path

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# Check around position 54915
pos = 54915
print(f"Characters around position {pos}:")
print(repr(content[pos-50:pos+50]))

# Try to fix common JSON issues
# Remove any trailing commas before ] or }
import re
fixed = re.sub(r',\s*([}\]])', r'\1', content)

# Try parsing
import json
try:
    data = json.loads(fixed)
    print(f"\nFixed JSON parsed successfully!")
    print(f"Total tweets: {data['total']}")
    print(f"Tweets in array: {len(data['tweets'])}")
except json.JSONDecodeError as e:
    print(f"\nStill invalid: {e}")
    # Try to find the issue
    lines = fixed.split('\n')
    print(f"Number of lines: {len(lines)}")
