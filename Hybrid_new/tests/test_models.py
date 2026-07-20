"""Tests for Pydantic model serialization/deserialization."""


from tap.models import (
    BranchStrategy,
    DualFollowUp,
    GrokAnalysis,
    JudgeScore,
    PatternClass,
    PropertyStatus,
    TAPNode,
    Tweet,
    TweetSource,
)


class TestTweet:
    def test_create_tweet(self, sample_tweet):
        assert sample_tweet.id == "1234567890"
        assert sample_tweet.source == TweetSource.TARGET_BOT
        assert sample_tweet.username == "HackingA0"

    def test_tweet_serialize(self, sample_tweet):
        data = sample_tweet.model_dump()
        assert data["id"] == "1234567890"
        assert data["source"] == "target_bot"

    def test_tweet_json_roundtrip(self, sample_tweet):
        json_str = sample_tweet.model_dump_json()
        restored = Tweet.model_validate_json(json_str)
        assert restored.id == sample_tweet.id
        assert restored.source == sample_tweet.source


class TestTAPNode:
    def test_create_node(self, sample_node):
        assert sample_node.branch_strategy == BranchStrategy.BINARY_SEARCH
        assert sample_node.judge_score == 7.0

    def test_node_optional_fields(self):
        node = TAPNode(branch_strategy=BranchStrategy.NARRATIVE)
        assert node.tweet_id is None
        assert node.judge_score is None
        assert node.pruned is False

    def test_node_serialize(self, sample_node):
        data = sample_node.model_dump()
        assert data["branch_strategy"] == "binary_search"
        assert data["pruned"] is False


class TestProperty:
    def test_create_property(self, sample_property):
        assert sample_property.property_key == "word_count"
        assert sample_property.status == PropertyStatus.CONFIRMED
        assert sample_property.confidence == 0.9

    def test_property_serialize(self, sample_property):
        data = sample_property.model_dump()
        assert data["status"] == "confirmed"


class TestResponseClassification:
    def test_verify_hit(self, sample_classification):
        assert sample_classification.pattern == PatternClass.VERIFY_HIT
        assert sample_classification.boolean_result is True
        assert sample_classification.confidence == 0.9

    def test_rhetoric_block(self, sample_rhetoric_block):
        assert sample_rhetoric_block.pattern == PatternClass.RHETORIC_BLOCK
        assert sample_rhetoric_block.boolean_result is None


class TestJudgeScore:
    def test_create_score(self, sample_judge_score):
        assert sample_judge_score.score == 7.0
        assert sample_judge_score.information_extracted is True

    def test_score_bounds(self):
        score = JudgeScore(
            score=5.0,
            reasoning="test",
            pattern=PatternClass.VERIFY_HIT,
            information_extracted=False,
        )
        assert 1.0 <= score.score <= 10.0


class TestDualFollowUp:
    def test_create_followup(self):
        followup = DualFollowUp(
            option_a="Test probe A",
            option_a_explanation="Conservative approach",
            option_a_strategy=BranchStrategy.BINARY_SEARCH,
            option_b="Test probe B",
            option_b_explanation="Exploratory approach",
            option_b_strategy=BranchStrategy.ALIAS_ABSORPTION,
            recommended="A",
        )
        assert followup.recommended in ("A", "B")
        assert followup.option_a_strategy == BranchStrategy.BINARY_SEARCH


class TestDPAFrame:
    def test_create_frame(self, sample_dpa_frame):
        assert sample_dpa_frame.metaphor_layer == "Captain Elara Voss / Kraken"
        assert len(sample_dpa_frame.active_aliases) == 4
        assert len(sample_dpa_frame.burned_aliases) == 1
        assert 0.0 <= sample_dpa_frame.frame_coherence_score <= 1.0


class TestGrokAnalysis:
    def test_create_analysis(self):
        analysis = GrokAnalysis(
            binary_outcome="confirmed",
            property_tested="word_count",
            property_value="2",
            new_aliases=["scallywag"],
            refusal_tone="engaged",
            metaphor_shift="same_layer",
            signal_reliability=0.95,
            followup_a="Continue binary search",
            followup_b="Absorb new alias",
        )
        assert analysis.binary_outcome == "confirmed"
        assert 0.0 <= analysis.signal_reliability <= 1.0