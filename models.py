"""
Minimal data models using Python dataclasses to make failing tests pass.

This module implements Tweet, Profile, Features, and Recommendation dataclasses
following TDD Green phase - implementing only what's needed to pass tests.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import json
from dateutil import parser as date_parser


@dataclass
class EngagementMetrics:
    """Engagement metrics for tweets and content."""
    
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    
    def __post_init__(self):
        """Validate engagement metrics."""
        if any(value < 0 for value in [self.likes, self.retweets, self.replies, self.views]):
            raise ValueError("Engagement metrics cannot be negative")
    
    def total_engagements(self) -> int:
        """Calculate total engagements excluding views."""
        return self.likes + self.retweets + self.replies
    
    def engagement_rate(self) -> float:
        """Calculate engagement rate based on views."""
        if self.views == 0:
            return 0.0
        return self.total_engagements() / self.views


@dataclass
class ContentFeatures:
    """Content analysis features for tweets."""
    
    has_question: bool = False
    has_media: bool = False
    has_links: bool = False
    has_hashtags: bool = False
    has_mentions: bool = False
    length: int = 0
    word_count: int = 0
    sentiment: str = "neutral"
    topics: List[str] = field(default_factory=list)
    language: str = "en"
    
    def __post_init__(self):
        """Validate content features."""
        valid_sentiments = ["positive", "negative", "neutral"]
        if self.sentiment not in valid_sentiments:
            raise ValueError(f"Invalid sentiment: {self.sentiment}. Must be one of {valid_sentiments}")
    
    def is_engaging(self) -> bool:
        """Check if content is considered engaging."""
        return (self.has_question or 
                self.has_media or 
                self.sentiment == "positive" or
                len(self.topics) > 0)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentFeatures':
        """Create ContentFeatures from dictionary (camelCase compatibility)."""
        return cls(
            has_question=data.get("hasQuestion", data.get("has_question", False)),
            has_media=data.get("hasMedia", data.get("has_media", False)),
            has_links=data.get("hasLinks", data.get("has_links", False)),
            has_hashtags=data.get("hasHashtags", data.get("has_hashtags", False)),
            has_mentions=data.get("hasMentions", data.get("has_mentions", False)),
            length=data.get("length", 0),
            word_count=data.get("wordCount", data.get("word_count", 0)),
            sentiment=data.get("sentiment", "neutral"),
            topics=data.get("topics", []),
            language=data.get("language", "en")
        )


@dataclass
class Profile:
    """User profile information."""
    
    id: str
    username: str
    display_name: str
    bio: str = ""
    avatar: Optional[str] = None
    verified: bool = False
    followers: int = 0
    following: int = 0
    location: Optional[str] = None
    url: Optional[str] = None
    join_date: Optional[datetime] = None
    tweet_count: int = 0
    pinned_tweet: Optional[str] = None
    
    def follower_ratio(self) -> float:
        """Calculate follower to following ratio."""
        if self.following == 0:
            return float('inf') if self.followers > 0 else 0.0
        return self.followers / self.following
    
    def is_influential(self) -> bool:
        """Check if profile is considered influential."""
        ratio = self.follower_ratio()
        return (self.verified or 
                self.followers >= 5000 or 
                (ratio != float('inf') and ratio >= 5.0))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create Profile from dictionary (camelCase compatibility)."""
        # Handle join_date parsing if present
        join_date = None
        if "joinDate" in data or "join_date" in data:
            date_str = data.get("joinDate", data.get("join_date"))
            if date_str and isinstance(date_str, str):
                try:
                    join_date = date_parser.parse(date_str)
                except (ValueError, TypeError):
                    join_date = None
        
        return cls(
            id=data.get("id", ""),
            username=data.get("username", ""),
            display_name=data.get("displayName", data.get("display_name", "")),
            bio=data.get("bio", ""),
            avatar=data.get("avatar"),
            verified=data.get("verified", False),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            location=data.get("location"),
            url=data.get("url"),
            join_date=join_date,
            tweet_count=data.get("tweetCount", data.get("tweet_count", 0)),
            pinned_tweet=data.get("pinnedTweet", data.get("pinned_tweet"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Profile to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "displayName": self.display_name,
            "bio": self.bio,
            "avatar": self.avatar,
            "verified": self.verified,
            "followers": self.followers,
            "following": self.following,
            "location": self.location,
            "url": self.url,
            "joinDate": self.join_date.isoformat() if self.join_date else None,
            "tweetCount": self.tweet_count,
            "pinnedTweet": self.pinned_tweet
        }


@dataclass
class Tweet:
    """Tweet data model."""
    
    id: str
    text: str
    user: Profile
    created_at: datetime
    engagement: Optional[EngagementMetrics] = None
    features: Optional[ContentFeatures] = None
    urls: List[Dict[str, str]] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    media: List[Dict[str, Any]] = field(default_factory=list)
    is_retweet: bool = False
    is_reply: bool = False
    is_thread: bool = False
    thread_position: Optional[int] = None
    quoted_tweet: Optional[Dict[str, Any]] = None
    retweeted_tweet: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default objects if not provided."""
        if self.engagement is None:
            self.engagement = EngagementMetrics()
        if self.features is None:
            self.features = ContentFeatures(
                length=len(self.text),
                word_count=len(self.text.split())
            )
    
    def age_hours(self) -> float:
        """Calculate age of tweet in hours."""
        now = datetime.now()
        # Handle timezone-aware datetime
        if self.created_at.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=self.created_at.tzinfo)
        elif self.created_at.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        delta = now - self.created_at
        return delta.total_seconds() / 3600
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tweet':
        """Create Tweet from dictionary (JSON compatibility)."""
        # Parse created_at
        created_at_str = data.get("createdAt", data.get("created_at"))
        if isinstance(created_at_str, str):
            try:
                created_at = date_parser.parse(created_at_str)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid date format: {created_at_str}")
        elif isinstance(created_at_str, datetime):
            created_at = created_at_str
        else:
            raise ValueError("createdAt field is required and must be a valid datetime")
        
        # Create user profile
        user_data = data.get("user", {})
        user = Profile.from_dict(user_data)
        
        # Create engagement metrics
        engagement_data = data.get("engagement", {})
        engagement = EngagementMetrics(
            likes=engagement_data.get("likes", 0),
            retweets=engagement_data.get("retweets", 0),
            replies=engagement_data.get("replies", 0),
            views=engagement_data.get("views", 0)
        )
        
        # Create content features
        features_data = data.get("features", {})
        features = ContentFeatures.from_dict(features_data)
        
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            user=user,
            created_at=created_at,
            engagement=engagement,
            features=features,
            urls=data.get("urls", []),
            hashtags=data.get("hashtags", []),
            mentions=data.get("mentions", []),
            media=data.get("media", []),
            is_retweet=data.get("isRetweet", data.get("is_retweet", False)),
            is_reply=data.get("isReply", data.get("is_reply", False)),
            is_thread=data.get("isThread", data.get("is_thread", False)),
            thread_position=data.get("threadPosition", data.get("thread_position")),
            quoted_tweet=data.get("quotedTweet", data.get("quoted_tweet")),
            retweeted_tweet=data.get("retweetedTweet", data.get("retweeted_tweet"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Tweet to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "user": self.user.to_dict(),
            "createdAt": self.created_at.isoformat(),
            "engagement": {
                "likes": self.engagement.likes,
                "retweets": self.engagement.retweets,
                "replies": self.engagement.replies,
                "views": self.engagement.views
            },
            "features": {
                "hasQuestion": self.features.has_question,
                "hasMedia": self.features.has_media,
                "hasLinks": self.features.has_links,
                "hasHashtags": self.features.has_hashtags,
                "hasMentions": self.features.has_mentions,
                "length": self.features.length,
                "wordCount": self.features.word_count,
                "sentiment": self.features.sentiment,
                "topics": self.features.topics,
                "language": self.features.language
            },
            "urls": self.urls,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "media": self.media,
            "isRetweet": self.is_retweet,
            "isReply": self.is_reply,
            "isThread": self.is_thread,
            "threadPosition": self.thread_position,
            "quotedTweet": self.quoted_tweet,
            "retweetedTweet": self.retweeted_tweet
        }


@dataclass
class Recommendation:
    """Recommendation for actions to take."""
    
    action_type: str
    target_id: str
    target_type: str
    priority: str = "medium"
    confidence_score: float = 0.5
    reasoning: str = ""
    timing_suggestion: str = "immediate"
    
    def __post_init__(self):
        """Validate recommendation fields."""
        valid_actions = ["like", "retweet", "reply", "follow", "unfollow", "mute", "block"]
        if self.action_type not in valid_actions:
            raise ValueError(f"Invalid action_type: {self.action_type}. Must be one of {valid_actions}")
        
        valid_priorities = ["high", "medium", "low"]
        if self.priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {self.priority}. Must be one of {valid_priorities}")
        
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"Invalid confidence_score: {self.confidence_score}. Must be between 0.0 and 1.0")
    
    def is_high_confidence(self) -> bool:
        """Check if recommendation has high confidence."""
        return self.confidence_score >= 0.8
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recommendation':
        """Create Recommendation from dictionary."""
        return cls(
            action_type=data.get("action_type", data.get("actionType", "")),
            target_id=data.get("target_id", data.get("targetId", "")),
            target_type=data.get("target_type", data.get("targetType", "")),
            priority=data.get("priority", "medium"),
            confidence_score=data.get("confidence_score", data.get("confidenceScore", 0.5)),
            reasoning=data.get("reasoning", ""),
            timing_suggestion=data.get("timing_suggestion", data.get("timingSuggestion", "immediate"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Recommendation to dictionary."""
        return {
            "actionType": self.action_type,
            "targetId": self.target_id,
            "targetType": self.target_type,
            "priority": self.priority,
            "confidenceScore": self.confidence_score,
            "reasoning": self.reasoning,
            "timingSuggestion": self.timing_suggestion
        }