"""
Python Twitter client that communicates with the Node.js HTTP bridge.

This implementation follows TDD Green phase - minimal code to make failing tests pass.
Handles cookie authentication from open_x_cdp.py format and normalizes responses 
to Python data models from models.py.
"""

import json
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser

from models import Tweet, Profile, EngagementMetrics, ContentFeatures
from config import AppConfig


class TwitterClientError(Exception):
    """Custom exception for TwitterClient errors."""
    pass


class TwitterClient:
    """Twitter client that communicates with Node.js bridge via HTTP requests."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize TwitterClient with configuration."""
        self.config = config or AppConfig()
        if not hasattr(self.config, 'api') or 'base_url' not in self.config.api:
            self.config.api = {"base_url": "http://localhost:3000"}
        
        # Set default configuration values if not provided
        if 'timeout_seconds' not in self.config.api:
            self.config.api['timeout_seconds'] = 30
        if 'max_retries' not in self.config.api:
            self.config.api['max_retries'] = 3
        if 'backoff_base' not in self.config.api:
            self.config.api['backoff_base'] = 2
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TwitterClient/1.0',
            'Content-Type': 'application/json'
        })
        
        self.cookie_data: Optional[Dict[str, Any]] = None
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()
        
    def close(self):
        """Close the requests session."""
        if hasattr(self, 'session'):
            self.session.close()
            delattr(self, 'session')
    
    def load_cookies(self, cookie_data: Dict[str, Any]) -> None:
        """Load cookie data from open_x_cdp.py format."""
        self.cookie_data = cookie_data
        
    def get_essential_cookies(self) -> Dict[str, str]:
        """Extract essential authentication cookies."""
        if not self.cookie_data:
            return {}
        return self.cookie_data.get("essentials", {})
        
    def get_cookie_header(self) -> str:
        """Generate cookie header for requests."""
        if not self.cookie_data:
            return ""
        return self.cookie_data.get("cookieHeader", "")
        
    def is_authenticated(self) -> bool:
        """Determine whether essential cookies satisfy the Node bridge contract.

        The Node bridge middleware (`twitter_bridge/middleware/auth.js`) enforces the
        same cookie set that `open_x_cdp.py` captures from the Chromium debugging
        session:
        - auth_token: primary session authentication token issued by X/Twitter
        - ct0: CSRF token that must accompany state-changing requests
        - twid: binds the authenticated user to the session
        - guest_id: gates access to some API endpoints even for authenticated users
        - att: additional token that X validates alongside the primary session cookies

        We require each of these cookies to be present and non-empty before
        attempting to call the bridge so that outbound requests mirror the
        expectations of the middleware layer.
        """
        if not self.cookie_data:
            return False
        
        essentials = self.get_essential_cookies()
        required_cookies = ["auth_token", "ct0", "twid", "guest_id", "att"]
        
        return all(cookie in essentials and essentials[cookie] for cookie in required_cookies)
        
    def _check_authentication(self) -> None:
        """Raise error if not authenticated."""
        # Check if cookie data was loaded
        if not self.cookie_data:
            raise TwitterClientError("Authentication cookies missing: expected 'cookieHeader' and 'essentials'")
        
        # Check if required fields are present
        if 'cookieHeader' not in self.cookie_data or 'essentials' not in self.cookie_data:
            raise TwitterClientError("Authentication cookies missing: expected 'cookieHeader' and 'essentials'")
        
        # Check if fields are not empty
        cookie_header = self.cookie_data.get('cookieHeader', '')
        essentials = self.cookie_data.get('essentials', {})
        
        if not cookie_header or not essentials:
            raise TwitterClientError("Authentication cookies missing: expected 'cookieHeader' and 'essentials'")
        
        # Use the existing is_authenticated() logic for deeper validation
        if not self.is_authenticated():
            raise TwitterClientError("Authentication cookies invalid or incomplete; see is_authenticated() docstring for required set")
            
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, max_retries: int = None) -> Dict[str, Any]:
        """Make HTTP request to Node.js bridge with retry logic."""
        self._check_authentication()
        
        # Use config values if not overridden
        if max_retries is None:
            max_retries = self.config.api['max_retries']
        timeout_seconds = self.config.api['timeout_seconds']
        backoff_base = self.config.api['backoff_base']
        
        url = f"{self.config.api['base_url']}{endpoint}"
        headers = {'Cookie': self.get_cookie_header()}
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'POST':
                    request_data = data or {}
                    request_data['cookies'] = self.get_essential_cookies()
                    
                    response = self.session.post(
                        url, 
                        json=request_data, 
                        headers=headers,
                        timeout=timeout_seconds
                    )
                else:
                    response = self.session.get(url, headers=headers, timeout=timeout_seconds)
                
                return self._handle_response(response)
                
            except requests.Timeout:
                if attempt == max_retries - 1:
                    raise TwitterClientError("Request timeout - bridge may be unavailable")
                time.sleep(backoff_base ** attempt)  # Exponential backoff
                
            except requests.ConnectionError:
                if attempt == max_retries - 1:
                    raise TwitterClientError("Connection error - unable to reach bridge")
                time.sleep(backoff_base ** attempt)  # Exponential backoff
                
            except TwitterClientError as e:
                # Check if this is a transient HTTP error that should be retried
                error_msg = str(e)
                if any(status in error_msg for status in ["HTTP 502:", "HTTP 503:", "HTTP 504:"]):
                    if attempt == max_retries - 1:
                        raise  # Re-raise the original error on final attempt
                    time.sleep(backoff_base ** attempt)  # Exponential backoff
                else:
                    # Non-transient error, don't retry
                    raise
                
        raise TwitterClientError("Max retries exceeded")
        
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle HTTP response from bridge."""
        # First check if this is an HTTP error status (>= 400)
        if response.status_code >= 400:
            # Try to parse JSON for error details
            try:
                data = response.json()
                error = data.get('error', {})
                error_code = error.get('code', 'UNKNOWN')
                error_message = error.get('message', 'Unknown error')
                
                # Format as HTTP status error with JSON details
                raise TwitterClientError(f"HTTP {response.status_code}: {error_code} - {error_message}")
                
            except json.JSONDecodeError:
                # No valid JSON, use status code and reason phrase
                reason = getattr(response, 'reason', 'Unknown Error')
                raise TwitterClientError(f"HTTP {response.status_code}: {reason}")
        
        # Not an HTTP error status, parse normally
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise TwitterClientError(f"Invalid response format: {response.text}")
            
        # Handle application-level errors from successful HTTP responses
        if not data.get('success', False):
            error = data.get('error', {})
            error_code = error.get('code', 'UNKNOWN')
            error_message = error.get('message', 'Unknown error')
            
            if 'AUTHENTICATION' in error_code:
                raise TwitterClientError(f"Authentication error: {error_message}")
            elif error_code == 'NOT_FOUND':
                raise TwitterClientError(f"Resource not found: {error_message}")
            elif error_code == 'RATE_LIMITED':
                raise TwitterClientError(f"Rate limit exceeded: {error_message}")
            else:
                raise TwitterClientError(f"API error ({error_code}): {error_message}")
                
        return data
        
    def _normalize_tweet(self, tweet_data: Dict[str, Any]) -> Tweet:
        """Normalize bridge tweet data to Tweet model."""
        user_data = tweet_data.get('user', {})
        user = self._normalize_user(user_data)
        
        engagement_data = tweet_data.get('engagement', {})
        engagement = self._normalize_engagement(engagement_data)
        
        # Parse created_at timestamp
        created_at_str = tweet_data.get('createdAt')
        if created_at_str:
            try:
                created_at = date_parser.parse(created_at_str)
            except (ValueError, TypeError):
                created_at = datetime.now()
        else:
            created_at = datetime.now()
            
        # Create basic content features
        text = tweet_data.get('text', '')
        features = ContentFeatures(
            length=len(text),
            word_count=len(text.split()),
            has_question='?' in text,
            has_media=bool(tweet_data.get('media', [])),
            has_hashtags='#' in text,
            has_mentions='@' in text,
            has_links='http' in text.lower()
        )
        
        return Tweet(
            id=tweet_data.get('id', ''),
            text=text,
            user=user,
            created_at=created_at,
            engagement=engagement,
            features=features,
            urls=tweet_data.get('urls', []),
            hashtags=tweet_data.get('hashtags', []),
            mentions=tweet_data.get('mentions', []),
            media=tweet_data.get('media', []),
            is_retweet=tweet_data.get('isRetweet', False),
            is_reply=tweet_data.get('isReply', False),
            is_thread=tweet_data.get('isThread', False),
            thread_position=tweet_data.get('threadPosition'),
            quoted_tweet=tweet_data.get('quotedTweet'),
            retweeted_tweet=tweet_data.get('retweetedTweet')
        )
        
    def _normalize_user(self, user_data: Dict[str, Any]) -> Profile:
        """Normalize bridge user data to Profile model."""
        join_date = None
        if 'joinDate' in user_data:
            try:
                join_date = date_parser.parse(user_data['joinDate'])
            except (ValueError, TypeError):
                pass
                
        return Profile(
            id=user_data.get('id', ''),
            username=user_data.get('username', ''),
            display_name=user_data.get('displayName', ''),
            bio=user_data.get('bio', ''),
            avatar=user_data.get('avatar'),
            verified=user_data.get('verified', False),
            followers=user_data.get('followers', 0),
            following=user_data.get('following', 0),
            location=user_data.get('location'),
            url=user_data.get('url'),
            join_date=join_date,
            tweet_count=user_data.get('tweetCount', 0),
            pinned_tweet=user_data.get('pinnedTweet')
        )
        
    def _normalize_engagement(self, engagement_data: Dict[str, Any]) -> EngagementMetrics:
        """Normalize bridge engagement data to EngagementMetrics model."""
        return EngagementMetrics(
            likes=engagement_data.get('likes', 0),
            retweets=engagement_data.get('retweets', 0),
            replies=engagement_data.get('replies', 0),
            views=engagement_data.get('views', 0)
        )
        
    # Functional methods that work with Node.js bridge
    
    def get_timeline(self, count: int = 20) -> List[Tweet]:
        """Get timeline tweets."""
        data = self._make_request('POST', '/api/timeline', {'count': count})
        tweet_list = data.get('data', [])
        return [self._normalize_tweet(tweet_data) for tweet_data in tweet_list]
        
    def get_latest_tweet(self) -> Tweet:
        """Get the latest tweet from timeline."""
        tweets = self.get_timeline(count=1)
        if not tweets:
            raise TwitterClientError("No tweets found")
        return tweets[0]
        
    def get_tweets_and_replies(self, count: int = 20) -> List[Tweet]:
        """Get tweets and replies."""
        data = self._make_request('POST', '/api/timeline', {
            'count': count, 
            'includeReplies': True
        })
        tweet_list = data.get('data', [])
        return [self._normalize_tweet(tweet_data) for tweet_data in tweet_list]
        
    def get_tweet(self, tweet_id: str) -> Tweet:
        """Get specific tweet by ID."""
        data = self._make_request('GET', f'/api/tweet/{tweet_id}')
        tweet_data = data.get('data', {})
        return self._normalize_tweet(tweet_data)
        
    # Placeholder methods for features not yet implemented
    
    def search_tweets(self, query: str, count: int = 20) -> List[Tweet]:
        """Search for tweets (not yet implemented due to library limitations)."""
        raise TwitterClientError("Search functionality is not yet implemented due to library limitations")
        
    def get_profile(self, username: str) -> Profile:
        """Get user profile (not yet implemented due to library limitations)."""
        raise TwitterClientError("Profile retrieval is not yet implemented due to library limitations")
        
    def get_trends(self, location: str = "worldwide") -> List[Dict[str, Any]]:
        """Get trending topics (not yet implemented due to library limitations)."""
        raise TwitterClientError("Trends functionality is not yet implemented due to library limitations")
        
    def get_mentions(self, count: int = 20) -> List[Tweet]:
        """Get mentions (not yet implemented due to library limitations)."""
        raise TwitterClientError("Mentions functionality is not yet implemented due to library limitations")
