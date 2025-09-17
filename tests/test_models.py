"""
Comprehensive tests for data models following TDD Red phase.
These tests will initially fail and drive the implementation of models.py.

Tests cover Tweet, Profile, Features, and Recommendation dataclass creation,
validation, serialization, and edge cases.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

import models


class TestEngagementMetrics:
    """Test the EngagementMetrics dataclass."""

    def test_engagement_metrics_creation_with_valid_data(self):
        """Test creating EngagementMetrics with valid data."""
        metrics = models.EngagementMetrics(
            likes=100, retweets=25, replies=15, views=1500
        )
        assert metrics.likes == 100
        assert metrics.retweets == 25
        assert metrics.replies == 15
        assert metrics.views == 1500

    def test_engagement_metrics_creation_with_defaults(self):
        """Test creating EngagementMetrics with default values."""
        metrics = models.EngagementMetrics()
        assert metrics.likes == 0
        assert metrics.retweets == 0
        assert metrics.replies == 0
        assert metrics.views == 0

    def test_engagement_metrics_total_engagements(self):
        """Test calculating total engagements."""
        metrics = models.EngagementMetrics(likes=100, retweets=25, replies=15)
        assert metrics.total_engagements() == 140

    def test_engagement_metrics_engagement_rate(self):
        """Test calculating engagement rate."""
        metrics = models.EngagementMetrics(
            likes=100, retweets=25, replies=15, views=1000
        )
        assert metrics.engagement_rate() == 0.14

    def test_engagement_metrics_engagement_rate_zero_views(self):
        """Test engagement rate with zero views."""
        metrics = models.EngagementMetrics(likes=100, retweets=25, replies=15, views=0)
        assert metrics.engagement_rate() == 0.0


class TestContentFeatures:
    """Test the ContentFeatures dataclass."""

    def test_content_features_creation_with_valid_data(self):
        """Test creating ContentFeatures with valid data."""
        features = models.ContentFeatures(
            has_question=True,
            has_media=False,
            has_links=True,
            has_hashtags=True,
            has_mentions=False,
            length=104,
            word_count=17,
            sentiment="positive",
            topics=["technology", "machine learning"],
            language="en",
        )
        assert features.has_question is True
        assert features.has_media is False
        assert features.length == 104
        assert features.sentiment == "positive"
        assert "technology" in features.topics

    def test_content_features_creation_with_defaults(self):
        """Test creating ContentFeatures with default values."""
        features = models.ContentFeatures()
        assert features.has_question is False
        assert features.has_media is False
        assert features.has_links is False
        assert features.has_hashtags is False
        assert features.has_mentions is False
        assert features.length == 0
        assert features.word_count == 0
        assert features.sentiment == "neutral"
        assert features.topics == []
        assert features.language == "en"

    def test_content_features_is_engaging(self):
        """Test checking if content is engaging."""
        features = models.ContentFeatures(
            has_question=True, has_media=True, sentiment="positive"
        )
        assert features.is_engaging() is True

        boring_features = models.ContentFeatures()
        assert boring_features.is_engaging() is False


class TestProfile:
    """Test the Profile dataclass."""

    def test_profile_creation_with_valid_data(self):
        """Test creating Profile with valid data."""
        profile = models.Profile(
            id="987654321",
            username="tech_enthusiast",
            display_name="Tech Enthusiast",
            bio="Passionate about AI and machine learning.",
            avatar="https://example.com/avatar.jpg",
            verified=True,
            followers=15420,
            following=892,
            location="San Francisco, CA",
            url="https://techblog.example.com",
            join_date=datetime(2019, 3, 15, 10, 0, 0),
            tweet_count=3456,
            pinned_tweet=None,
        )
        assert profile.id == "987654321"
        assert profile.username == "tech_enthusiast"
        assert profile.verified is True
        assert profile.followers == 15420

    def test_profile_creation_with_minimal_data(self):
        """Test creating Profile with minimal required data."""
        profile = models.Profile(
            id="123", username="testuser", display_name="Test User"
        )
        assert profile.id == "123"
        assert profile.username == "testuser"
        assert profile.bio == ""
        assert profile.verified is False
        assert profile.followers == 0

    def test_profile_handles_missing_optional_fields(self):
        """Test Profile handles missing optional fields gracefully."""
        profile = models.Profile(
            id="123",
            username="testuser",
            display_name="Test User",
            location=None,
            url=None,
        )
        assert profile.location is None
        assert profile.url is None

    def test_profile_follower_ratio(self):
        """Test calculating follower ratio."""
        profile = models.Profile(
            id="123",
            username="test",
            display_name="Test",
            followers=1000,
            following=500,
        )
        assert profile.follower_ratio() == 2.0

    def test_profile_follower_ratio_zero_following(self):
        """Test follower ratio with zero following."""
        profile = models.Profile(
            id="123", username="test", display_name="Test", followers=1000, following=0
        )
        assert profile.follower_ratio() == float("inf")

    def test_profile_is_influential(self):
        """Test checking if profile is influential."""
        influential_profile = models.Profile(
            id="123",
            username="test",
            display_name="Test",
            followers=10000,
            verified=True,
        )
        assert influential_profile.is_influential() is True

        regular_profile = models.Profile(
            id="456",
            username="regular",
            display_name="Regular",
            followers=100,
            verified=False,
        )
        assert regular_profile.is_influential() is False

    def test_profile_from_dict(self):
        """Test creating Profile from dictionary."""
        data = {
            "id": "987654321",
            "username": "tech_enthusiast",
            "displayName": "Tech Enthusiast",
            "bio": "Passionate about AI and machine learning.",
            "avatar": "https://example.com/avatar.jpg",
            "verified": True,
            "followers": 15420,
            "following": 892,
            "location": "San Francisco, CA",
            "url": "https://techblog.example.com",
        }
        profile = models.Profile.from_dict(data)
        assert profile.username == "tech_enthusiast"
        assert profile.verified is True


class TestTweet:
    """Test the Tweet dataclass."""

    def test_tweet_creation_with_valid_data(self):
        """Test creating Tweet with valid data."""
        user = models.Profile(id="123", username="testuser", display_name="Test User")
        engagement = models.EngagementMetrics(likes=100, retweets=25)
        features = models.ContentFeatures(has_question=True)

        tweet = models.Tweet(
            id="1234567890123456789",
            text="Test tweet with question?",
            user=user,
            created_at=datetime(2024, 3, 15, 14, 30, 0),
            engagement=engagement,
            features=features,
        )
        assert tweet.id == "1234567890123456789"
        assert tweet.text == "Test tweet with question?"
        assert tweet.user.username == "testuser"
        assert tweet.engagement.likes == 100
        assert tweet.features.has_question is True

    def test_tweet_creation_with_minimal_data(self):
        """Test creating Tweet with minimal required data."""
        user = models.Profile(id="123", username="test", display_name="Test")
        tweet = models.Tweet(
            id="123456", text="Minimal tweet", user=user, created_at=datetime.now()
        )
        assert tweet.id == "123456"
        assert tweet.text == "Minimal tweet"
        assert isinstance(tweet.engagement, models.EngagementMetrics)
        assert isinstance(tweet.features, models.ContentFeatures)

    def test_tweet_handles_different_media_types(self):
        """Test Tweet handles different media types."""
        user = models.Profile(id="123", username="test", display_name="Test")
        media = [
            {"type": "photo", "url": "https://example.com/photo.jpg"},
            {"type": "video", "url": "https://example.com/video.mp4"},
        ]
        tweet = models.Tweet(
            id="123456",
            text="Tweet with media",
            user=user,
            created_at=datetime.now(),
            media=media,
        )
        assert len(tweet.media) == 2
        assert tweet.media[0]["type"] == "photo"

    def test_tweet_thread_properties(self):
        """Test Tweet thread-related properties."""
        user = models.Profile(id="123", username="test", display_name="Test")
        tweet = models.Tweet(
            id="123456",
            text="Thread tweet",
            user=user,
            created_at=datetime.now(),
            is_thread=True,
            thread_position=1,
        )
        assert tweet.is_thread is True
        assert tweet.thread_position == 1

    def test_tweet_retweet_properties(self):
        """Test Tweet retweet-related properties."""
        user = models.Profile(id="123", username="test", display_name="Test")
        retweeted_tweet = {
            "id": "original_tweet_id",
            "user": {"username": "original_user", "displayName": "Original User"},
        }
        tweet = models.Tweet(
            id="123456",
            text="RT @original_user: Original tweet text",
            user=user,
            created_at=datetime.now(),
            is_retweet=True,
            retweeted_tweet=retweeted_tweet,
        )
        assert tweet.is_retweet is True
        assert tweet.retweeted_tweet is not None

    def test_tweet_age_calculation(self):
        """Test calculating tweet age."""
        user = models.Profile(id="123", username="test", display_name="Test")
        old_time = datetime(2024, 1, 1, 10, 0, 0)
        tweet = models.Tweet(
            id="123456", text="Old tweet", user=user, created_at=old_time
        )
        # Age should be positive (actual test would check against current time)
        age = tweet.age_hours()
        assert isinstance(age, float)
        assert age >= 0

    def test_tweet_from_dict(self):
        """Test creating Tweet from dictionary (JSON compatibility)."""
        data = {
            "id": "1234567890123456789",
            "text": "Test tweet",
            "user": {
                "id": "987654321",
                "username": "tech_enthusiast",
                "displayName": "Tech Enthusiast",
            },
            "createdAt": "2024-03-15T14:30:00Z",
            "engagement": {"likes": 245, "retweets": 67, "replies": 23, "views": 3420},
            "features": {
                "hasQuestion": True,
                "hasMedia": False,
                "length": 10,
                "sentiment": "positive",
            },
        }
        tweet = models.Tweet.from_dict(data)
        assert tweet.id == "1234567890123456789"
        assert tweet.user.username == "tech_enthusiast"
        assert tweet.engagement.likes == 245
        assert tweet.features.has_question is True

    def test_tweet_to_dict(self):
        """Test converting Tweet to dictionary."""
        user = models.Profile(id="123", username="test", display_name="Test")
        tweet = models.Tweet(
            id="123456",
            text="Test tweet",
            user=user,
            created_at=datetime(2024, 3, 15, 14, 30, 0),
        )
        data = tweet.to_dict()
        assert data["id"] == "123456"
        assert data["text"] == "Test tweet"
        assert data["user"]["username"] == "test"
        assert "engagement" in data
        assert "features" in data


class TestRecommendation:
    """Test the Recommendation dataclass."""

    def test_recommendation_creation_with_valid_data(self):
        """Test creating Recommendation with valid data."""
        recommendation = models.Recommendation(
            action_type="like",
            priority="high",
            target_id="1234567890123456789",
            target_type="tweet",
            confidence_score=0.85,
            reasoning="High engagement potential with relevant topic",
            timing_suggestion="immediate",
        )
        assert recommendation.action_type == "like"
        assert recommendation.priority == "high"
        assert recommendation.confidence_score == 0.85

    def test_recommendation_creation_with_defaults(self):
        """Test creating Recommendation with default values."""
        recommendation = models.Recommendation(
            action_type="like", target_id="123456", target_type="tweet"
        )
        assert recommendation.priority == "medium"
        assert recommendation.confidence_score == 0.5
        assert recommendation.timing_suggestion == "immediate"

    def test_recommendation_validation(self):
        """Test Recommendation validation methods."""
        recommendation = models.Recommendation(
            action_type="like",
            target_id="123456",
            target_type="tweet",
            confidence_score=0.9,
        )
        assert recommendation.is_high_confidence() is True

        low_conf = models.Recommendation(
            action_type="like",
            target_id="123456",
            target_type="tweet",
            confidence_score=0.3,
        )
        assert low_conf.is_high_confidence() is False

    def test_recommendation_invalid_action_type(self):
        """Test Recommendation with invalid action type raises error."""
        with pytest.raises(ValueError):
            models.Recommendation(
                action_type="invalid_action", target_id="123456", target_type="tweet"
            )

    def test_recommendation_invalid_priority(self):
        """Test Recommendation with invalid priority raises error."""
        with pytest.raises(ValueError):
            models.Recommendation(
                action_type="like",
                target_id="123456",
                target_type="tweet",
                priority="invalid_priority",
            )

    def test_recommendation_invalid_confidence_score(self):
        """Test Recommendation with invalid confidence score raises error."""
        with pytest.raises(ValueError):
            models.Recommendation(
                action_type="like",
                target_id="123456",
                target_type="tweet",
                confidence_score=1.5,  # Should be between 0 and 1
            )


class TestIntegrationWithFixtures:
    """Test models with fixture data for integration testing."""

    @pytest.fixture
    def sample_tweets_data(self):
        """Load sample tweets from fixtures."""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_tweets.json"
        with open(fixtures_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_tweet_creation_from_fixture_data(self, sample_tweets_data):
        """Test creating Tweet objects from fixture data."""
        tweet_data = sample_tweets_data["tweets"][0]  # First tweet
        tweet = models.Tweet.from_dict(tweet_data)

        assert tweet.id == "1234567890123456789"
        assert "machine learning" in tweet.text.lower()
        assert tweet.user.username == "tech_enthusiast"
        assert tweet.user.verified is True
        assert tweet.engagement.likes == 245
        assert tweet.features.has_question is True

    def test_profile_creation_from_fixture_data(self, sample_tweets_data):
        """Test creating Profile objects from fixture data."""
        profile_data = sample_tweets_data["profiles"][0]  # First profile
        profile = models.Profile.from_dict(profile_data)

        assert profile.id == "987654321"
        assert profile.username == "tech_enthusiast"
        assert profile.verified is True
        assert profile.followers == 15420
        assert "AI and machine learning" in profile.bio

    def test_multiple_tweets_processing(self, sample_tweets_data):
        """Test processing multiple tweets from fixture data."""
        tweets = []
        for tweet_data in sample_tweets_data["tweets"]:
            tweet = models.Tweet.from_dict(tweet_data)
            tweets.append(tweet)

        assert len(tweets) == 4
        assert any(tweet.is_retweet for tweet in tweets)
        assert any(tweet.features.has_media for tweet in tweets)
        assert any(tweet.features.has_question for tweet in tweets)

    def test_json_serialization_compatibility(self, sample_tweets_data):
        """Test JSON serialization compatibility with Node.js bridge."""
        tweet_data = sample_tweets_data["tweets"][0]
        tweet = models.Tweet.from_dict(tweet_data)
        serialized = tweet.to_dict()

        # Should be able to serialize back to JSON
        json_str = json.dumps(serialized, default=str)
        assert isinstance(json_str, str)

        # Key fields should be preserved
        deserialized = json.loads(json_str)
        assert deserialized["id"] == tweet_data["id"]
        assert deserialized["text"] == tweet_data["text"]
        assert deserialized["user"]["username"] == tweet_data["user"]["username"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_tweet_with_empty_text(self):
        """Test Tweet with empty text."""
        user = models.Profile(id="123", username="test", display_name="Test")
        tweet = models.Tweet(id="123456", text="", user=user, created_at=datetime.now())
        assert tweet.text == ""
        assert tweet.features.length == 0

    def test_profile_with_zero_followers(self):
        """Test Profile with zero followers."""
        profile = models.Profile(
            id="123",
            username="newbie",
            display_name="Newbie",
            followers=0,
            following=100,
        )
        assert profile.followers == 0
        assert profile.follower_ratio() == 0.0

    def test_engagement_metrics_negative_values(self):
        """Test EngagementMetrics handles negative values."""
        with pytest.raises(ValueError):
            models.EngagementMetrics(likes=-1, retweets=10, replies=5, views=100)

    def test_content_features_invalid_sentiment(self):
        """Test ContentFeatures with invalid sentiment."""
        with pytest.raises(ValueError):
            models.ContentFeatures(sentiment="invalid_sentiment")

    def test_tweet_invalid_date_format(self):
        """Test Tweet with invalid date format in from_dict."""
        data = {
            "id": "123456",
            "text": "Test tweet",
            "user": {"id": "123", "username": "test", "displayName": "Test"},
            "createdAt": "invalid-date-format",
        }
        with pytest.raises(ValueError):
            models.Tweet.from_dict(data)

    def test_profile_extremely_long_bio(self):
        """Test Profile with extremely long bio."""
        long_bio = "A" * 1000  # 1000 characters
        profile = models.Profile(
            id="123", username="test", display_name="Test", bio=long_bio
        )
        # Should handle long bio without issues
        assert len(profile.bio) == 1000
        assert profile.bio == long_bio
