import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tap.config import get_settings
from tap.x_client import TwitterClient
from tap.stream_listener import StreamListener

async def main():
    settings = get_settings()
    client = TwitterClient(settings)
    stream = StreamListener(settings)

    print("--- Test Stream: resolve target user id ---")
    target_id = await client._resolve_target_user_id()
    if not target_id:
        print("Failed to resolve target user id")
        return
    print(f"Resolved target id: {target_id}")

    stream.set_target_user_id(target_id)

    print("Refreshing OAuth2 user token (if available)...")
    await stream._refresh_oauth2_token()

    print("Attempting to create subscriptions and connect to stream (30s timeout)...")
    try:
        await asyncio.wait_for(stream._connect_and_listen(), timeout=30)
    except asyncio.TimeoutError:
        print("Timeout reached (30s). Subscriptions were attempted; stream connect may have been throttled.")
    except Exception as e:
        print("Stream attempt raised:", repr(e))

if __name__ == '__main__':
    asyncio.run(main())
