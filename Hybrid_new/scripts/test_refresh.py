
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tap.config import get_settings
from tap.x_client import TwitterClient
from tap.stream_listener import StreamListener

async def test_refresh():
    settings = get_settings()
    client = TwitterClient(settings)
    stream = StreamListener(settings)
    
    print("--- Testing OAuth 2.0 Token Refresh ---")
    print(f"Current Access Token (prefix): {settings.twitter_oauth2_access_token[:20]}...")
    
    new_token = await stream._refresh_oauth2_token()
    
    if new_token:
        print(f"[SUCCESS] Token refreshed! New Access Token: {new_token[:20]}...")
        print("Note: In a real run, this token is stored in memory and should be updated in .env manually if needed.")
        
        # Now try to use it
        client._oauth2_token = new_token
        try:
            subs = await client.list_activity_subscriptions()
            print(f"[SUCCESS] Verified with list_activity_subscriptions. Found {len(subs)} subs.")
        except Exception as e:
            print(f"[FAIL] Even with new token, API call failed: {e}")
    else:
        print("[FAIL] Refresh failed. Check if refresh_token is valid and matching client_id.")

if __name__ == "__main__":
    asyncio.run(test_refresh())
