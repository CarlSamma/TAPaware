"""Extract tweets by splitting on boundaries."""
from pathlib import Path
import json
import re

fpath = Path(__file__).parent.parent / ".mimocode" / "Sources" / "2-hackinga0_ALL_tweets_historical.json.TXT.md"
content = fpath.read_text(encoding="utf-8")

# The file is a single line JSON
# Let's try to parse it directly, fixing issues as we go

# First, let's see how many "id": " patterns there are (each tweet has one)
id_count = content.count('"id":')
print(f"Total 'id' fields found: {id_count}")

# Try to parse the whole thing
try:
    data = json.loads(content)
    print(f"Direct parse success! Tweets: {len(data['tweets'])}")
except json.JSONDecodeError as e:
    print(f"Direct parse failed: {e}")
    
    # Try to fix common issues
    # 1. Fix unicode escapes
    content = content.replace('\\ud83d\\ude0f', '\U0001F60F')
    content = content.replace('\\ud83d\\ude02', '\U0001F602')
    content = content.replace('\\ud83d\\ude0d', '\U0001F60D')
    content = content.replace('\\ud83d\\ude12', '\U0001F612')
    content = content.replace('\\ud83d\\ude0e', '\U0001F60E')
    content = content.replace('\\ud83d\\ude1c', '\U0001F61C')
    content = content.replace('\\ud83d\\ude08', '\U0001F608')
    content = content.replace('\\ud83d\\ude0a', '\U0001F60A')
    content = content.replace('\\ud83d\\ude1d', '\U0001F61D')
    content = content.replace('\\ud83d\\ude21', '\U0001F621')
    content = content.replace('\\ud83d\\ude0b', '\U0001F60B')
    content = content.replace('\\ud83d\\ude05', '\U0001F605')
    content = content.replace('\\ud83d\\ude06', '\U0001F606')
    content = content.replace('\\ud83d\\ude09', '\U0001F609')
    content = content.replace('\\ud83d\\ude07', '\U0001F607')
    content = content.replace('\\ud83d\\ude10', '\U0001F610')
    content = content.replace('\\ud83d\\ude11', '\U0001F611')
    content = content.replace('\\ud83d\\ude13', '\U0001F613')
    content = content.replace('\\ud83d\\ude14', '\U0001F614')
    content = content.replace('\\ud83d\\ude15', '\U0001F615')
    content = content.replace('\\ud83d\\ude16', '\U0001F616')
    content = content.replace('\\ud83d\\ude17', '\U0001F617')
    content = content.replace('\\ud83d\\ude18', '\U0001F618')
    content = content.replace('\\ud83d\\ude19', '\U0001F619')
    content = content.replace('\\ud83d\\ude1a', '\U0001F61A')
    content = content.replace('\\ud83d\\ude1b', '\U0001F61B')
    content = content.replace('\\ud83d\\ude1e', '\U0001F61E')
    content = content.replace('\\ud83d\\ude1f', '\U0001F61F')
    content = content.replace('\\ud83d\\ude20', '\U0001F620')
    content = content.replace('\\ud83d\\ude22', '\U0001F622')
    content = content.replace('\\ud83d\\ude23', '\U0001F623')
    content = content.replace('\\ud83d\\ude24', '\U0001F624')
    content = content.replace('\\ud83d\\ude25', '\U0001F625')
    content = content.replace('\\ud83d\\ude26', '\U0001F626')
    content = content.replace('\\ud83d\\ude27', '\U0001F627')
    content = content.replace('\\ud83d\\ude28', '\U0001F628')
    content = content.replace('\\ud83d\\ude29', '\U0001F629')
    content = content.replace('\\ud83d\\ude2a', '\U0001F62A')
    content = content.replace('\\ud83d\\ude2b', '\U0001F62B')
    content = content.replace('\\ud83d\\ude2c', '\U0001F62C')
    content = content.replace('\\ud83d\\ude2d', '\U0001F62D')
    content = content.replace('\\ud83d\\ude2e', '\U0001F62E')
    content = content.replace('\\ud83d\\ude2f', '\U0001F62F')
    content = content.replace('\\ud83d\\ude30', '\U0001F630')
    content = content.replace('\\ud83d\\ude31', '\U0001F631')
    content = content.replace('\\ud83d\\ude32', '\U0001F632')
    content = content.replace('\\ud83d\\ude33', '\U0001F633')
    content = content.replace('\\ud83d\\ude34', '\U0001F634')
    content = content.replace('\\ud83d\\ude35', '\U0001F635')
    content = content.replace('\\ud83d\\ude36', '\U0001F636')
    content = content.replace('\\ud83d\\ude37', '\U0001F637')
    content = content.replace('\\ud83e\\udd14', '\U0001F914')
    content = content.replace('\\ud83e\\udd23', '\U0001F923')
    content = content.replace('\\ud83e\\udd70', '\U0001F970')
    content = content.replace('\\ud83e\\udee1', '\U0001FAE1')
    content = content.replace('\\ud83e\\dd2a', '\U0001F92A')
    content = content.replace('\\ud83e\\dd73', '\U0001F973')
    content = content.replace('\\ud83e\\dd11', '\U0001F911')
    content = content.replace('\\ud83e\\dd13', '\U0001F913')
    content = content.replace('\\ud83e\\dd2f', '\U0001F92F')
    content = content.replace('\\ud83e\\ude79', '\U0001FA79')
    content = content.replace('\\ud83d\\udc80', '\U0001F480')
    content = content.replace('\\ud83d\\udca9', '\U0001F4A9')
    content = content.replace('\\ud83d\\udc4d', '\U0001F44D')
    content = content.replace('\\ud83d\\udc4e', '\U0001F44E')
    content = content.replace('\\ud83d\\udc4a', '\U0001F44A')
    content = content.replace('\\ud83d\\udc4b', '\U0001F44B')
    content = content.replace('\\ud83d\\udc4c', '\U0001F44C')
    content = content.replace('\\ud83d\\udc4f', '\U0001F44F')
    content = content.replace('\\ud83d\\udc50', '\U0001F450')
    content = content.replace('\\ud83d\\udc42', '\U0001F442')
    content = content.replace('\\ud83d\\udc43', '\U0001F443')
    content = content.replace('\\ud83d\\udc40', '\U0001F440')
    content = content.replace('\\ud83d\\udc45', '\U0001F445')
    content = content.replace('\\ud83d\\udc44', '\U0001F444')
    content = content.replace('\\ud83d\\udc46', '\U0001F446')
    content = content.replace('\\ud83d\\udc47', '\U0001F447')
    content = content.replace('\\ud83d\\udc48', '\U0001F448')
    content = content.replace('\\ud83d\\udc49', '\U0001F449')
    content = content.replace('\\ud83d\\udcaf', '\U0001F4AF')
    content = content.replace('\\ud83d\\udcaa', '\U0001F4AA')
    content = content.replace('\\ud83d\\ude4f', '\U0001F64F')
    content = content.replace('\\ud83d\\ude4e', '\U0001F64E')
    content = content.replace('\\ud83d\\ude4d', '\U0001F64D')
    content = content.replace('\\ud83d\\ude4c', '\U0001F64C')
    content = content.replace('\\ud83d\\ude4b', '\U0001F64B')
    content = content.replace('\\ud83d\\ude4a', '\U0001F64A')
    content = content.replace('\\ud83d\\ude49', '\U0001F649')
    content = content.replace('\\ud83d\\ude48', '\U0001F648')
    content = content.replace('\\ud83d\\ude47', '\U0001F647')
    content = content.replace('\\ud83d\\ude46', '\U0001F646')
    content = content.replace('\\ud83d\\ude45', '\U0001F645')
    content = content.replace('\\ud83d\\ude44', '\U0001F644')
    content = content.replace('\\ud83d\\ude43', '\U0001F643')
    content = content.replace('\\ud83d\\ude42', '\U0001F642')
    content = content.replace('\\ud83d\\ude41', '\U0001F641')
    content = content.replace('\\ud83d\\ude40', '\U0001F640')
    content = content.replace('\\ud83d\\ude3f', '\U0001F63F')
    content = content.replace('\\ud83d\\ude3e', '\U0001F63E')
    content = content.replace('\\ud83d\\ude3d', '\U0001F63D')
    content = content.replace('\\ud83d\\ude3c', '\U0001F63C')
    content = content.replace('\\ud83d\\ude3b', '\U0001F63B')
    content = content.replace('\\ud83d\\ude3a', '\U0001F63A')
    content = content.replace('\\ud83d\\ude39', '\U0001F639')
    content = content.replace('\\ud83d\\ude38', '\U0001F638')
    
    # 2. Fix unescaped quotes in text fields
    # This is the tricky part - we need to find text fields and fix inner quotes
    
    # Try parsing again
    try:
        data = json.loads(content)
        print(f"After unicode fix: {len(data['tweets'])} tweets")
    except json.JSONDecodeError as e2:
        print(f"After unicode fix still failed: {e2}")
        
        # Last resort - extract tweets manually
        # Split by tweet boundaries
        tweets = []
        # Find all "id": "..." patterns
        id_pattern = re.compile(r'"id":\s*"(\d+)"')
        for match in id_pattern.finditer(content):
            tweet_id = match.group(1)
            # Find the tweet object boundaries
            # Look backwards for the opening {
            start = content.rfind('{', 0, match.start())
            # Look forward for the closing }
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
            
            tweet_str = content[start:j+1]
            try:
                tweet = json.loads(tweet_str)
                tweets.append(tweet)
            except:
                pass
        
        print(f"Manual extraction: {len(tweets)} tweets")
        data = {"total": len(tweets), "tweets": tweets}

# Save the result
if 'data' in locals() and data.get('tweets'):
    out_path = Path(__file__).parent.parent / "data" / "hackinga0_historical_fixed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data['tweets'])} tweets to {out_path}")
