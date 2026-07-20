
import asyncio
import sys
import os
from dotenv import load_dotenv
from tap.config import Settings
from tap.x_client import TwitterClient
from tap.exceptions import TwitterError

async def verify():
    # Force reload from .env and ignore session environment
    if os.path.exists(".env"):
        # Clear existing env vars to prevent override
        for key in os.environ.keys():
            if key.startswith("TWITTER_"):
                os.environ.pop(key)
        load_dotenv(".env", override=True)
    
    settings = Settings()
    
    print("--- Verifying X API Credentials ---")
    
    # Check if variables are set (without printing them)
    creds_to_check = [
        ("Bearer Token", settings.twitter_bearer_token),
        ("Consumer Key", settings.twitter_consumer_key),
        ("Consumer Secret", settings.twitter_consumer_secret),
        ("Access Token", settings.twitter_access_token),
        ("Access Token Secret", settings.twitter_access_token_secret)
    ]
    
    all_set = True
    for name, value in creds_to_check:
        if not value or value.strip() == "":
            print(f"[FAIL] {name} is NOT set in .env")
            all_set = False
        else:
            print(f"[OK] {name} is set (length: {len(value)})")
            
    if not all_set:
        print("\n[ERROR] One or more required credentials are missing. Verification aborted.")
        return

    client = TwitterClient(settings)
    
    # 1. Verify Read Access (Bearer Token)
    print("\n1. Testing Read Access (Bearer Token)...")
    try:
        # Use _retry to execute synchronous get_user call
        user = await client._retry(lambda: client.client.get_user(username=settings.target_handle))
        if user and user.data:
            print(f"[SUCCESS] Bearer Token is valid. Resolved target @{settings.target_handle} to ID: {user.data.id}")
        else:
            print(f"[FAIL] Bearer Token seems valid but target @{settings.target_handle} was not found.")
    except Exception as e:
        print(f"[FAIL] Bearer Token verification failed: {e}")

    # 2. Verify Write Access (OAuth 1.0a)
    print("\n2. Testing Write Access (OAuth 1.0a)...")
    try:
        # We use get_me() which requires User Context (OAuth 1.0a)
        # Note: get_me() in tweepy v2 returns the user for the authenticated tokens
        me = await client._retry(lambda: client.client.get_me())
        if me.data:
            print(f"[SUCCESS] OAuth 1.0a credentials are valid. Authenticated as @{me.data.username} (ID: {me.data.id})")
        else:
            print("[FAIL] OAuth 1.0a credentials failed to return user data.")
    except Exception as e:
        print(f"[FAIL] OAuth 1.0a verification failed: {e}")
        print("Note: Ensure 'Read and Write' permissions are enabled in the X Developer Portal for these tokens.")

    # 3. Verify OAuth 2.0 User Token (if set)
    if settings.twitter_oauth2_access_token:
        print("\n3. Testing OAuth 2.0 User Token...")
        try:
            # Simple call to list subscriptions as a test
            await client.list_activity_subscriptions()
            print("[SUCCESS] OAuth 2.0 User Token is valid for Activity API calls.")
        except Exception as e:
            print(f"[FAIL] OAuth 2.0 User Token verification failed: {e}")
    else:
        print("\n3. OAuth 2.0 User Token not set (optional).")

if __name__ == "__main__":
    asyncio.run(verify())
