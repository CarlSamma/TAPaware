import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tap.x_client import TwitterClient

@pytest.mark.asyncio
async def test_sync_compliance(mock_settings):
    client = TwitterClient(mock_settings)
    
    # Mock response for get_tweets
    mock_response = MagicMock()
    mock_response.data = [MagicMock(id=123), MagicMock(id=456)]
    
    with patch.object(client, "_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = mock_response
        
        # 123 and 456 exist, 789 is missing (deleted)
        deleted_ids = await client.sync_compliance(["123", "456", "789"])
        
        assert deleted_ids == ["789"]
        assert mock_retry.call_count == 1

@pytest.mark.asyncio
async def test_get_quota_status(mock_settings):
    client = TwitterClient(mock_settings)
    
    # Simulate some usage
    client._update_quota(reads=100, writes=10)
    
    status = await client.get_quota_status()
    assert status["reads"] == 100
    assert status["writes"] == 10
    assert status["estimated_overage_usd"] == 0.0
    
    # Simulate overage
    client._update_quota(reads=2_000_100)
    status = await client.get_quota_status()
    assert status["reads"] == 2_000_200 # previous 100 + 2000100
    assert status["estimated_overage_usd"] > 0.0

@pytest.mark.asyncio
async def test_post_probe_with_media(mock_settings):
    client = TwitterClient(mock_settings)
    mock_response = MagicMock()
    mock_response.data = {"id": "11223344"}
    
    with patch.object(client, "_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = mock_response

        await client.post_probe("Hello", media_ids=["media123"])
        
        client.client.create_tweet = MagicMock()
        mock_retry.call_args[0][0]()
        client.client.create_tweet.assert_called_once_with(
            text="Hello @HackingA0",
            in_reply_to_tweet_id=None,
            media_ids=["media123"]
        )
