"""Fix JSON with unescaped quotes in tweet text."""
from pathlib import Path
import json
import re

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# Fix unescaped quotes inside JSON string values
# Pattern: "text": "...unescaped "quotes"..."
# We need to find text values and escape inner quotes

# Simple approach: replace problematic patterns
# Find all "text": "..." patterns and fix inner quotes
def fix_text_field(match):
    prefix = match.group(1)  # "text": "
    text_content = match.group(2)
    suffix = match.group(3)  # ", "entities"
    
    # Escape any unescaped quotes in text_content
    # But be careful not to double-escape
    fixed = text_content.replace('\\"', '"')  # First unescape any existing
    fixed = fixed.replace('"', '\\"')  # Then escape all
    # But we need to preserve the original escaped quotes
    # Actually, let's just replace the problematic pattern
    
    return prefix + text_content + suffix

# Actually, let's try a different approach - read the file line by line
# and fix the specific issues

# Replace "none of the above" with escaped version
content = content.replace('"none of the above"', '\\"none of the above\\"')

# Try parsing
try:
    data = json.loads(content)
    print(f"Success! Total tweets: {data['total']}")
    print(f"Tweets in array: {len(data['tweets'])}")
except json.JSONDecodeError as e:
    print(f"Error: {e}")
    pos = e.pos
    print(f"Context: {repr(content[max(0,pos-100):pos+100])}")
