#!/usr/bin/env python3
"""
Demonstration of the TDD-implemented Python data models and configuration system.

This script shows how the models and configuration system work with real data
from the fixtures, demonstrating the successful TDD implementation.
"""

import json
from pathlib import Path

import models
import config


def main():
    """Demonstrate the TDD implementation."""
    print("🚀 TDD Python Models & Configuration Demo")
    print("=" * 50)
    
    # Load configuration from fixture
    print("\n📋 Loading Configuration...")
    config_path = Path("tests/fixtures/sample_config.yaml")
    app_config = config.AppConfig.from_file(str(config_path))
    
    print(f"Persona: {app_config.persona.name}")
    print(f"Target Audience: {app_config.persona.target_audience}")
    print(f"Tone: {app_config.persona.tone_of_voice}")
    print(f"API Base URL: {app_config.api['base_url']}")
    print(f"Batch Size: {app_config.processing['batch_size']}")
    
    # Load and process tweets from fixture
    print("\n🐦 Processing Tweet Data...")
    tweets_path = Path("tests/fixtures/sample_tweets.json")
    with open(tweets_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tweets = []
    for tweet_data in data["tweets"]:
        tweet = models.Tweet.from_dict(tweet_data)
        tweets.append(tweet)
    
    print(f"Loaded {len(tweets)} tweets")
    
    # Analyze tweets
    print("\n📊 Tweet Analysis:")
    for i, tweet in enumerate(tweets, 1):
        print(f"\nTweet {i}: {tweet.id}")
        print(f"  User: @{tweet.user.username} ({tweet.user.display_name})")
        print(f"  Verified: {'✓' if tweet.user.verified else '✗'}")
        print(f"  Followers: {tweet.user.followers:,}")
        print(f"  Text: {tweet.text[:60]}{'...' if len(tweet.text) > 60 else ''}")
        print(f"  Engagement: {tweet.engagement.likes} likes, {tweet.engagement.retweets} retweets")
        print(f"  Features: Question={tweet.features.has_question}, Media={tweet.features.has_media}")
        print(f"  Sentiment: {tweet.features.sentiment}")
        print(f"  Engaging Content: {'Yes' if tweet.features.is_engaging() else 'No'}")
        print(f"  Age: {tweet.age_hours():.1f} hours")
        
        # Generate recommendations using scoring config
        metrics = {
            "engagement_rate": tweet.engagement.engagement_rate(),
            "recency": max(0, 1.0 - (tweet.age_hours() / 168)),  # Decay over 1 week
            "author_credibility": 0.8 if tweet.user.verified else 0.5,
            "content_relevance": 0.9 if tweet.features.has_question else 0.6,
            "viral_potential": 0.8 if tweet.features.is_engaging() else 0.4
        }
        
        score = app_config.scoring.calculate_score(metrics)
        priority = app_config.scoring.get_priority_level(score)
        
        if score > 0.5:  # Only recommend high-scoring content
            recommendation = models.Recommendation(
                action_type="like" if not tweet.is_retweet else "retweet",
                target_id=tweet.id,
                target_type="tweet",
                priority=priority,
                confidence_score=score,
                reasoning=f"High engagement potential (score: {score:.2f})"
            )
            print(f"  💡 Recommendation: {recommendation.action_type.upper()} (Priority: {recommendation.priority})")
    
    # Configuration validation demo
    print(f"\n✅ Configuration Validation: {'PASSED' if app_config.validate() else 'FAILED'}")
    
    # Serialization demo
    print("\n🔄 Serialization Demo:")
    config_dict = app_config.to_dict()
    print(f"Config serialized to dict with {len(config_dict)} top-level keys")
    
    sample_tweet = tweets[0]
    tweet_dict = sample_tweet.to_dict()
    print(f"Tweet serialized to dict with {len(tweet_dict)} fields")
    
    # JSON compatibility
    json_str = json.dumps(tweet_dict, default=str, indent=2)
    print(f"Tweet JSON: {len(json_str)} characters")
    
    print("\n🎉 TDD Implementation Demo Complete!")
    print("All models and configuration classes are working correctly.")


if __name__ == "__main__":
    main()