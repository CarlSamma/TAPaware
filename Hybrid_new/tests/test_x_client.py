import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tap.exceptions import TwitterError
from tap.x_client import TwitterClient


@pytest.mark.asyncio
async def test_post_probe_appends_hackinga0_mention(mock_settings):
    # Initialize TwitterClient
    client = TwitterClient(mock_settings)
    client._resolve_target_user_id = AsyncMock(return_value=None)

    # Mock self._retry to return a dummy response
    mock_response = MagicMock()
    mock_response.data = {"id": "11223344"}
    
    # We patch the '_retry' helper method to bypass the thread pool and actual HTTP requests
    with patch.object(client, "_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = mock_response

        # Case 1: Post probe without mention
        tweet_id = await client.post_probe("Hello, is the gate open?")
        
        # Verify the returned tweet_id
        assert tweet_id == "11223344"
        
        # Verify that _retry was called for create_tweet
        assert mock_retry.call_count >= 1
        func = mock_retry.call_args[0][0]
        
        # Mock client's actual tweepy Client's create_tweet
        client.client.create_tweet = MagicMock()
        func()
        client.client.create_tweet.assert_called_once_with(
            text="Hello, is the gate open? @HackingA0",
            in_reply_to_tweet_id=None,
            media_ids=None,
        )


@pytest.mark.asyncio
async def test_post_probe_keeps_existing_hackinga0_mention(mock_settings):
    client = TwitterClient(mock_settings)
    mock_response = MagicMock()
    mock_response.data = {"id": "11223344"}
    
    with patch.object(client, "_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = mock_response

        # Case 2: Post probe with lowercase mention
        await client.post_probe("Hello @hackinga0 are you there?")
        
        client.client.create_tweet = MagicMock()
        mock_retry.call_args[0][0]()
        client.client.create_tweet.assert_called_once_with(
            text="Hello @hackinga0 are you there?",
            in_reply_to_tweet_id=None,
            media_ids=None,
        )

    with patch.object(client, "_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = mock_response

        # Case 3: Post probe with mixed-case mention
        await client.post_probe("Hello @HackingA0 logic check")
        
        client.client.create_tweet = MagicMock()
        mock_retry.call_args[0][0]()
        client.client.create_tweet.assert_called_once_with(
            text="Hello @HackingA0 logic check",
            in_reply_to_tweet_id=None,
            media_ids=None,
        )


@pytest.mark.asyncio
async def test_create_activity_subscription_retries_after_refresh(mock_settings):
    client = TwitterClient(mock_settings)
    mock_first_response = MagicMock(status_code=401, text="Unauthorized")
    mock_second_response = MagicMock(status_code=201)
    mock_second_response.json.return_value = {"data": {"id": "sub_123"}}

    async_client_mock = AsyncMock()
    async_client_mock.__aenter__.return_value.post = AsyncMock(side_effect=[mock_first_response, mock_second_response])
    async_client_mock.__aexit__.return_value = AsyncMock()

    with patch("tap.x_client.httpx.AsyncClient", return_value=async_client_mock), \
         patch("tap.oauth.refresh_oauth2_token", new_callable=AsyncMock, return_value="new_oauth2_token") as mock_refresh:
        result = await client.create_activity_subscription()

    assert result == {"data": {"id": "sub_123"}}
    mock_refresh.assert_awaited_once()
    assert client._oauth2_token == "new_oauth2_token"
    assert client.settings.twitter_oauth2_access_token == "new_oauth2_token"
    assert async_client_mock.__aenter__.return_value.post.call_count == 2
