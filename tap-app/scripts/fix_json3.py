"""Fix all unescaped quotes in JSON text fields."""
from pathlib import Path
import json
import re

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# Find all "text": "..." patterns and fix inner quotes
# Pattern: "text": "...content..."
# We need to handle nested quotes properly

# Strategy: Find "text": " and then extract until the next ", "entities"
# or similar delimiter

def fix_text_fields(content):
    result = []
    i = 0
    while i < len(content):
        # Look for "text": "
        text_start = content.find('"text": "', i)
        if text_start == -1:
            result.append(content[i:])
            break
        
        # Add everything before this text field
        result.append(content[i:text_start])
        
        # Find the start of the text value
        text_value_start = text_start + len('"text": "')
        
        # Find the end of the text value - look for ", "entities" or similar
        # We need to be careful about escaped quotes
        j = text_value_start
        while j < len(content):
            if content[j] == '\\':
                j += 2  # Skip escaped character
                continue
            if content[j] == '"':
                # Check if this is the end of the text value
                # Look for ", "entities" or similar pattern after
                rest = content[j+1:j+20]
                if '", "entities"' in rest or '", "edit_history' in rest:
                    break
            j += 1
        
        # Extract the text content
        text_content = content[text_value_start:j]
        
        # Fix unescaped quotes in text content
        # Replace any " that's not already escaped
        fixed_text = re.sub(r'(?<!\\)"', '\\"', text_content)
        
        # Add the fixed text
        result.append('"text": "')
        result.append(fixed_text)
        result.append('"')
        
        i = j + 1
    
    return ''.join(result)

print("Fixing text fields...")
fixed_content = fix_text_fields(content)

try:
    data = json.loads(fixed_content)
    print(f"Success! Total tweets: {data['total']}")
    print(f"Tweets in array: {len(data['tweets'])}")
    
    # Save fixed JSON
    import json
    out_path = Path(__file__).parent.parent / "data" / "hackinga0_historical_fixed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved fixed JSON to {out_path}")
    
except json.JSONDecodeError as e:
    print(f"Error: {e}")
    pos = e.pos
    print(f"Context: {repr(fixed_content[max(0,pos-100):pos+100])}")
