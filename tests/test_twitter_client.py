"""
Comprehensive failing tests for TwitterClient following canonical TDD Red phase.

These tests define the expected behavior and interface of the TwitterClient class
before any implementation exists. They will initially fail and drive the 
implementation of twitter_client.py.

Tests cover:
- Initialization with configuration
- Cookie handling from open_x_cdp.py format
- HTTP communication with Node.js bridge
- Error handling for various scenarios
- Response normalization to Python models
- All client methods (functional and placeholder)
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
import requests

# Import the classes we need to test with
from models import Tweet, Profile, EngagementMetrics, ContentFeatures
from config import AppConfig
from twitter_client import TwitterClient, TwitterClientError


# Global fixtures available to all test classes
@pytest.fixture
def sample_cookie_data():
    """Load sample cookie data fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_cookies.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def mock_bridge_responses():
    """Load mock bridge response fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "bridge_responses.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def authenticated_client(sample_cookie_data):
    """Create authenticated TwitterClient for testing."""
    client = TwitterClient()
    client.load_cookies(sample_cookie_data)
    return client


class TestTwitterClientInitialization:
    """Test TwitterClient initialization and configuration."""
    
    def test_initializes_with_default_config(self):
        """TwitterClient initializes with default configuration when none provided."""
        client = TwitterClient()
        assert client.config is not None
        assert client.config.api["base_url"] == "http://localhost:3000"
        
    def test_initializes_with_custom_config(self):
        """TwitterClient accepts custom AppConfig during initialization."""
        custom_config = AppConfig()
        custom_config.api["base_url"] = "http://custom-bridge:8080"
        
        client = TwitterClient(config=custom_config)
        assert client.config == custom_config
        assert client.config.api["base_url"] == "http://custom-bridge:8080"
        
    def test_sets_up_session_with_proper_headers(self):
        """TwitterClient initializes requests session with proper headers."""
        client = TwitterClient()
        assert hasattr(client, 'session')
        assert isinstance(client.session, requests.Session)
        assert 'User-Agent' in client.session.headers
        
    def test_initializes_cookie_data_as_none(self):
        """TwitterClient starts with no cookie data loaded."""
        client = TwitterClient()
        assert client.cookie_data is None


class TestTwitterClientCookieHandling:
    """Test cookie handling from open_x_cdp.py format."""
    
    def test_loads_cookie_data_from_dict(self, sample_cookie_data):
        """TwitterClient loads cookie data from dictionary format."""
        client = TwitterClient()
        client.load_cookies(sample_cookie_data)
        
        assert client.cookie_data == sample_cookie_data
        assert "essentials" in client.cookie_data
        assert "cookieHeader" in client.cookie_data
        assert "cookies" in client.cookie_data
        
    def test_extracts_essential_cookies(self, sample_cookie_data):
        """TwitterClient extracts essential authentication cookies."""
        client = TwitterClient()
        client.load_cookies(sample_cookie_data)
        
        essentials = client.get_essential_cookies()
        assert "auth_token" in essentials
        assert "ct0" in essentials
        assert "twid" in essentials
        assert "guest_id" in essentials
        assert "att" in essentials
        
    def test_generates_cookie_header(self, sample_cookie_data):
        """TwitterClient generates proper cookie header for requests."""
        client = TwitterClient()
        client.load_cookies(sample_cookie_data)
        
        header = client.get_cookie_header()
        assert "auth_token=" in header
        assert "ct0=" in header
        assert "; " in header
        
    def test_validates_authentication_cookies(self, sample_cookie_data):
        """TwitterClient validates that required auth cookies are present."""
        client = TwitterClient()
        client.load_cookies(sample_cookie_data)
        
        assert client.is_authenticated()
        
    def test_fails_authentication_with_missing_cookies(self):
        """TwitterClient fails authentication when essential cookies are missing."""
        client = TwitterClient()
        incomplete_data = {
            "essentials": {"auth_token": "token"},  # Missing other required cookies
            "cookieHeader": "auth_token=token",
            "cookies": []
        }
        client.load_cookies(incomplete_data)
        
        assert not client.is_authenticated()
        
    def test_raises_error_when_not_authenticated(self):
        """TwitterClient raises error when attempting requests without authentication."""
        client = TwitterClient()
        
        with pytest.raises(TwitterClientError, match="not authenticated"):
            client.get_timeline()


class TestTwitterClientHTTPCommunication:
    """Test HTTP communication with Node.js bridge."""
    
    @patch('requests.Session.post')
    def test_makes_post_request_to_timeline_endpoint(self, mock_post, authenticated_client, mock_bridge_responses):
        """TwitterClient makes POST request to timeline endpoint with cookies."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["timeline_success"]
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = authenticated_client.get_timeline()
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0].endswith("/api/timeline")
        assert "cookies" in call_args[1]["json"]
        
    @patch('requests.Session.get')
    def test_makes_get_request_to_tweet_endpoint(self, mock_get, authenticated_client, mock_bridge_responses):
        """TwitterClient makes GET request to tweet endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["tweet_success"]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = authenticated_client.get_tweet("1234567890123456789")
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0].endswith("/api/tweet/1234567890123456789")
        
    def test_includes_timeout_in_requests(self, authenticated_client):
        """TwitterClient includes timeout parameter in all requests."""
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"success": True, "data": []}
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            authenticated_client.get_timeline()
            
            call_args = mock_post.call_args
            assert "timeout" in call_args[1]
            assert call_args[1]["timeout"] > 0
            
    def test_handles_connection_timeout(self, authenticated_client):
        """TwitterClient handles connection timeouts gracefully."""
        with patch('requests.Session.post', side_effect=requests.Timeout):
            with pytest.raises(TwitterClientError, match="timeout"):
                authenticated_client.get_timeline()
                
    def test_handles_connection_error(self, authenticated_client):
        """TwitterClient handles connection errors gracefully."""
        with patch('requests.Session.post', side_effect=requests.ConnectionError):
            with pytest.raises(TwitterClientError, match="Connection"):
                authenticated_client.get_timeline()


class TestTwitterClientErrorHandling:
    """Test error handling for various scenarios."""
    
    @patch('requests.Session.post')
    def test_handles_authentication_error_response(self, mock_post, authenticated_client, mock_bridge_responses):
        """TwitterClient handles authentication error from bridge."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["authentication_error"]
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with pytest.raises(TwitterClientError, match="Authentication"):
            authenticated_client.get_timeline()
            
    @patch('requests.Session.get')
    def test_handles_not_found_error(self, mock_get, authenticated_client, mock_bridge_responses):
        """TwitterClient handles not found errors."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["not_found_error"]
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with pytest.raises(TwitterClientError, match="not found"):
            authenticated_client.get_tweet("nonexistent")
            
    @patch('requests.Session.post')
    def test_handles_rate_limit_error(self, mock_post, authenticated_client, mock_bridge_responses):
        """TwitterClient handles rate limiting."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["rate_limit_error"]
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        with pytest.raises(TwitterClientError, match="Rate limit"):
            authenticated_client.get_timeline()
            
    def test_handles_invalid_json_response(self, authenticated_client):
        """TwitterClient handles invalid JSON responses."""
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.status_code = 200
            mock_response.text = "Invalid JSON"
            mock_post.return_value = mock_response
            
            with pytest.raises(TwitterClientError, match="Invalid response"):
                authenticated_client.get_timeline()
                
    @patch('requests.Session.post')
    def test_retry_logic_with_exponential_backoff(self, mock_post, authenticated_client):
        """TwitterClient implements retry logic with exponential backoff."""
        # First two calls fail, third succeeds
        mock_post.side_effect = [
            requests.ConnectionError(),
            requests.ConnectionError(),
            Mock(json=lambda: {"success": True, "data": []}, status_code=200)
        ]
        
        with patch('time.sleep') as mock_sleep:
            result = authenticated_client.get_timeline()
            
            assert mock_post.call_count == 3
            assert mock_sleep.call_count == 2
            # Verify exponential backoff
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[1] > sleep_calls[0]


class TestTwitterClientResponseNormalization:
    """Test response normalization to Python data models."""
    
    @patch('requests.Session.post')
    def test_normalizes_timeline_response_to_tweets(self, mock_post, authenticated_client, mock_bridge_responses):
        """TwitterClient normalizes timeline response to Tweet objects."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["timeline_success"]
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        tweets = authenticated_client.get_timeline()
        
        assert isinstance(tweets, list)
        assert len(tweets) == 1
        assert isinstance(tweets[0], Tweet)
        assert tweets[0].id == "1234567890123456789"
        assert tweets[0].text == "Sample tweet content for timeline testing"
        
    @patch('requests.Session.get')
    def test_normalizes_single_tweet_response(self, mock_get, authenticated_client, mock_bridge_responses):
        """TwitterClient normalizes single tweet response to Tweet object."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["tweet_success"]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        tweet = authenticated_client.get_tweet("1234567890123456789")
        
        assert isinstance(tweet, Tweet)
        assert tweet.id == "1234567890123456789"
        assert isinstance(tweet.user, Profile)
        assert isinstance(tweet.engagement, EngagementMetrics)
        
    def test_normalizes_user_data_to_profile(self, authenticated_client, mock_bridge_responses):
        """TwitterClient normalizes user data to Profile objects."""
        bridge_user = mock_bridge_responses["tweet_success"]["data"]["user"]
        
        profile = authenticated_client._normalize_user(bridge_user)
        
        assert isinstance(profile, Profile)
        assert profile.id == "987654321"
        assert profile.username == "sample_user"
        assert profile.display_name == "Sample User"
        assert profile.followers == 1500
        
    def test_normalizes_engagement_data(self, authenticated_client, mock_bridge_responses):
        """TwitterClient normalizes engagement data to EngagementMetrics."""
        bridge_engagement = mock_bridge_responses["tweet_success"]["data"]["engagement"]
        
        engagement = authenticated_client._normalize_engagement(bridge_engagement)
        
        assert isinstance(engagement, EngagementMetrics)
        assert engagement.likes == 42
        assert engagement.retweets == 15
        assert engagement.replies == 8
        assert engagement.views == 1000
        
    def test_handles_missing_optional_fields(self, authenticated_client):
        """TwitterClient handles missing optional fields in responses gracefully."""
        minimal_tweet_data = {
            "id": "123",
            "text": "Minimal tweet",
            "user": {"id": "456", "username": "user", "displayName": "User"},
            "createdAt": "2024-01-15T10:30:00.000Z"
        }
        
        tweet = authenticated_client._normalize_tweet(minimal_tweet_data)
        
        assert isinstance(tweet, Tweet)
        assert tweet.id == "123"
        assert tweet.engagement is not None  # Should have default values
        assert tweet.features is not None


class TestTwitterClientFunctionalMethods:
    """Test functional client methods that work with Node.js bridge."""
    
    @patch('requests.Session.post')
    def test_get_timeline_returns_tweet_list(self, mock_post, authenticated_client, mock_bridge_responses):
        """get_timeline() returns list of Tweet objects."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["timeline_success"]
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        tweets = authenticated_client.get_timeline()
        
        assert isinstance(tweets, list)
        assert all(isinstance(tweet, Tweet) for tweet in tweets)
        
    @patch('requests.Session.post')
    def test_get_timeline_accepts_count_parameter(self, mock_post, authenticated_client):
        """get_timeline() accepts count parameter for number of tweets."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": []}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        authenticated_client.get_timeline(count=50)
        
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data["count"] == 50
        
    @patch('requests.Session.post')
    def test_get_latest_tweet_returns_single_tweet(self, mock_post, authenticated_client, mock_bridge_responses):
        """get_latest_tweet() returns single Tweet object."""
        timeline_response = mock_bridge_responses["timeline_success"].copy()
        timeline_response["data"] = timeline_response["data"][:1]  # Only one tweet
        
        mock_response = Mock()
        mock_response.json.return_value = timeline_response
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        tweet = authenticated_client.get_latest_tweet()
        
        assert isinstance(tweet, Tweet)
        
    @patch('requests.Session.post')
    def test_get_tweets_and_replies_includes_replies(self, mock_post, authenticated_client):
        """get_tweets_and_replies() includes replies in request parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": []}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        authenticated_client.get_tweets_and_replies()
        
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data.get("includeReplies") is True
        
    @patch('requests.Session.get')
    def test_get_tweet_by_id_returns_tweet(self, mock_get, authenticated_client, mock_bridge_responses):
        """get_tweet() returns Tweet object for specific tweet ID."""
        mock_response = Mock()
        mock_response.json.return_value = mock_bridge_responses["tweet_success"]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        tweet = authenticated_client.get_tweet("1234567890123456789")
        
        assert isinstance(tweet, Tweet)
        assert tweet.id == "1234567890123456789"


class TestTwitterClientPlaceholderMethods:
    """Test placeholder methods for features not yet implemented."""
    
    def test_search_tweets_returns_not_implemented_error(self, authenticated_client):
        """search_tweets() returns appropriate not implemented error."""
        with pytest.raises(TwitterClientError, match="not yet implemented"):
            authenticated_client.search_tweets("python")
            
    def test_get_profile_returns_not_implemented_error(self, authenticated_client):
        """get_profile() returns appropriate not implemented error."""
        with pytest.raises(TwitterClientError, match="not yet implemented"):
            authenticated_client.get_profile("sample_user")
            
    def test_get_trends_returns_not_implemented_error(self, authenticated_client):
        """get_trends() returns appropriate not implemented error."""
        with pytest.raises(TwitterClientError, match="not yet implemented"):
            authenticated_client.get_trends()
            
    def test_get_mentions_returns_not_implemented_error(self, authenticated_client):
        """get_mentions() returns appropriate not implemented error."""
        with pytest.raises(TwitterClientError, match="not yet implemented"):
            authenticated_client.get_mentions()


class TestTwitterClientConnectionManagement:
    """Test connection management and session handling."""
    
    def test_closes_session_on_context_exit(self, sample_cookie_data):
        """TwitterClient closes session when used as context manager."""
        with TwitterClient() as client:
            client.load_cookies(sample_cookie_data)
            assert hasattr(client, 'session')
            
        # Session should be closed after context exit
        with pytest.raises(AttributeError):
            client.session.get("http://example.com")
            
    def test_manual_session_close(self, sample_cookie_data):
        """TwitterClient provides method to manually close session."""
        client = TwitterClient()
        client.load_cookies(sample_cookie_data)
        
        client.close()
        
        with pytest.raises(AttributeError):
            client.session.get("http://example.com")
            
    def test_reuses_session_for_multiple_requests(self, sample_cookie_data):
        """TwitterClient reuses session for multiple requests."""
        client = TwitterClient()
        client.load_cookies(sample_cookie_data)
        
        session_id = id(client.session)
        
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"success": True, "data": []}
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            client.get_timeline()
            client.get_timeline()
            
            # Should be same session instance
            assert id(client.session) == session_id
            assert mock_post.call_count == 2
