"""Check the historical tweets file structure."""
from pathlib import Path

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

print(f"File size: {len(content)} chars")
print(f"First 300 chars:")
print(content[:300])
print(f"\nLast 300 chars:")
print(content[-300:])
print(f"\nTotal lines: {len(content.split(chr(10)))}")

# Check if JSON is complete
stripped = content.strip()
print(f"Starts with '{{': {stripped.startswith('{')}")
print(f"Ends with '}}': {stripped.endswith('}')}")
