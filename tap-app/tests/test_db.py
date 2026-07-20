"""Tests for async SQLite database CRUD operations."""

import pytest
from datetime import datetime, timezone

from tap.db import Database
from tap.models import (
    Alias,
    AliasStatus,
    OtherUserIntel,
    TweetSource,
)


pytestmark = pytest.mark.asyncio


class TestDatabaseInit:
    async def test_initialize_creates_tables(self, db):
        stats = await db.get_stats()
        assert stats["total_tweets"] == 0
        assert stats["total_nodes"] == 0
        assert stats["total_properties"] == 0

    async def test_not_connected_raises(self, tmp_path):
        db = Database(str(tmp_path / "uninit.db"))
        with pytest.raises(Exception):
            await db.get_stats()


class TestTweetCRUD:
    async def test_upsert_and_get(self, db, sample_tweet):
        await db.upsert_tweet(sample_tweet)
        tweets = await db.get_tweets(limit=10)
        assert len(tweets) == 1
        assert tweets[0].id == sample_tweet.id

    async def test_get_by_source(self, db, sample_tweet, sample_our_tweet):
        await db.upsert_tweet(sample_tweet)
        await db.upsert_tweet(sample_our_tweet)

        target_tweets = await db.get_tweets(source=TweetSource.TARGET_BOT)
        assert len(target_tweets) == 1
        assert target_tweets[0].source == TweetSource.TARGET_BOT

    async def test_get_latest_target(self, db, sample_tweet):
        await db.upsert_tweet(sample_tweet)
        latest = await db.get_latest_target_tweet()
        assert latest is not None
        assert latest.username == "HackingA0"

    async def test_upsert_replaces(self, db, sample_tweet):
        await db.upsert_tweet(sample_tweet)
        sample_tweet.text = "Updated text"
        await db.upsert_tweet(sample_tweet)
        tweets = await db.get_tweets(limit=10)
        assert len(tweets) == 1
        assert tweets[0].text == "Updated text"


class TestNodeCRUD:
    async def test_insert_and_get(self, db, sample_node):
        node_id = await db.insert_node(sample_node)
        assert node_id > 0

        nodes = await db.get_active_nodes(limit=10)
        assert len(nodes) == 1
        assert nodes[0].id == node_id

    async def test_prune_node(self, db, sample_node):
        node_id = await db.insert_node(sample_node)
        await db.prune_node(node_id, "test pruning")

        active = await db.get_active_nodes(limit=10)
        assert len(active) == 0

    async def test_update_score(self, db, sample_node, sample_judge_score):
        node_id = await db.insert_node(sample_node)
        await db.update_node_score(node_id, sample_judge_score)

        nodes = await db.get_active_nodes(limit=10)
        assert len(nodes) == 1


class TestPropertyCRUD:
    async def test_upsert_new(self, db, sample_property):
        await db.upsert_property(sample_property)
        props = await db.get_confirmed_properties()
        assert len(props) == 1
        assert props[0].property_key == "word_count"

    async def test_upsert_update(self, db, sample_property):
        await db.upsert_property(sample_property)
        sample_property.confidence = 0.99
        await db.upsert_property(sample_property)
        props = await db.get_confirmed_properties()
        assert len(props) == 1
        assert props[0].confidence == 0.99

    async def test_property_history(self, db, sample_property):
        await db.upsert_property(sample_property)
        history = await db.get_property_history("word_count")
        assert len(history) == 1


class TestMetaphorLayer:
    async def test_insert_and_get_latest(self, db, sample_metaphor_layer):
        await db.insert_metaphor_layer(sample_metaphor_layer)
        latest = await db.get_latest_metaphor_layer()
        assert latest is not None
        assert latest.layer_name == "Captain Elara Voss"
        assert latest.layer_number == 7


class TestAliasCRUD:
    async def test_upsert_and_get_active(self, db):
        alias = Alias(
            alias="Kraken",
            status=AliasStatus.ACTIVE,
            first_used=datetime.now(timezone.utc),
            last_used=datetime.now(timezone.utc),
        )
        await db.upsert_alias(alias)
        active = await db.get_active_aliases()
        assert len(active) == 1
        assert active[0].alias == "Kraken"

    async def test_burn_alias(self, db):
        alias = Alias(
            alias="Chaos King",
            status=AliasStatus.ACTIVE,
            first_used=datetime.now(timezone.utc),
        )
        await db.upsert_alias(alias)
        await db.burn_alias("Chaos King")
        active = await db.get_active_aliases()
        assert len(active) == 0


class TestIntelCRUD:
    async def test_insert_and_get_recent(self, db):
        intel = OtherUserIntel(
            tweet_id="999",
            username="other_user",
            new_aliases=["scallywag"],
            defensive_pattern="snarky_deflection",
        )
        await db.insert_intel(intel)
        recent = await db.get_recent_intel(hours=1)
        assert len(recent) == 1
        assert recent[0].username == "other_user"


class TestStats:
    async def test_stats_empty(self, db):
        stats = await db.get_stats()
        assert stats["total_tweets"] == 0
        assert stats["confirmed_properties"] == 0
        assert stats["active_nodes"] == 0

    async def test_stats_with_data(self, db, sample_tweet, sample_node, sample_property):
        await db.upsert_tweet(sample_tweet)
        await db.insert_node(sample_node)
        await db.upsert_property(sample_property)

        stats = await db.get_stats()
        assert stats["total_tweets"] == 1
        assert stats["total_nodes"] == 1
        assert stats["confirmed_properties"] == 1