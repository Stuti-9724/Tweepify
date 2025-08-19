import os
import logging
import tweepy
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app import db
from models import TrendingHashtag

class TwitterService:
    def __init__(self):
        self.consumer_key = os.environ.get("TWITTER_CONSUMER_KEY", "default_key")
        self.consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET", "default_secret")
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "default_bearer")
        
        # Initialize API v2 client for read operations
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        
        # OAuth 1.0a handler for write operations
        self.auth = tweepy.OAuth1UserHandler(
            self.consumer_key,
            self.consumer_secret,
            callback="http://localhost:5000/twitter_callback"
        )
    
    def get_auth_url(self) -> str:
        """Get Twitter OAuth authorization URL"""
        try:
            redirect_url = self.auth.get_authorization_url()
            return redirect_url
        except Exception as e:
            logging.error(f"Twitter auth URL error: {e}")
            raise Exception("Failed to get Twitter authorization URL")
    
    def get_request_token(self) -> str:
        """Get OAuth request token"""
        try:
            return self.auth.request_token['oauth_token']
        except Exception as e:
            logging.error(f"Request token error: {e}")
            return ""
    
    def get_access_token(self, oauth_token: str, oauth_verifier: str) -> Tuple[str, str]:
        """Get access token after OAuth callback"""
        try:
            self.auth.request_token = {
                'oauth_token': oauth_token,
                'oauth_token_secret': oauth_verifier
            }
            access_token, access_token_secret = self.auth.get_access_token(oauth_verifier)
            return access_token, access_token_secret
        except Exception as e:
            logging.error(f"Access token error: {e}")
            raise Exception("Failed to get access token")
    
    def post_tweet(self, content: str, access_token: str, access_token_secret: str) -> str:
        """Post a tweet using user's credentials"""
        try:
            # Create authenticated API instance
            auth = tweepy.OAuth1UserHandler(
                self.consumer_key,
                self.consumer_secret,
                access_token,
                access_token_secret
            )
            
            api = tweepy.API(auth)
            client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            # Post the tweet
            response = client.create_tweet(text=content)
            
            if response.data:
                return response.data['id']
            else:
                raise Exception("No tweet ID returned")
                
        except Exception as e:
            logging.error(f"Tweet posting error: {e}")
            raise Exception(f"Failed to post tweet: {str(e)}")
    
    def get_trending_hashtags(self, location_woeid: int = 1) -> List[str]:
        """Get trending hashtags (cached for performance)"""
        try:
            # Check if we have recent trending data (less than 1 hour old)
            recent_trends = TrendingHashtag.query.filter(
                TrendingHashtag.updated_at > datetime.utcnow() - timedelta(hours=1)
            ).order_by(TrendingHashtag.trend_rank).limit(10).all()
            
            if recent_trends:
                return [trend.hashtag for trend in recent_trends]
            
            # Fetch new trending data
            trends = self.client.get_trending(id=location_woeid)
            
            if trends and trends.data:
                # Clear old trends
                TrendingHashtag.query.delete()
                
                # Save new trends
                trending_hashtags = []
                for i, trend in enumerate(trends.data[:20]):
                    hashtag = trend.get('name', '')
                    if hashtag.startswith('#'):
                        trend_obj = TrendingHashtag(
                            hashtag=hashtag,
                            tweet_volume=trend.get('tweet_volume'),
                            trend_rank=i + 1,
                            location='Global'
                        )
                        db.session.add(trend_obj)
                        trending_hashtags.append(hashtag)
                
                db.session.commit()
                return trending_hashtags[:10]
            
            return []
            
        except Exception as e:
            logging.error(f"Trending hashtags error: {e}")
            # Return cached data if available
            cached_trends = TrendingHashtag.query.order_by(TrendingHashtag.trend_rank).limit(10).all()
            return [trend.hashtag for trend in cached_trends]
    
    def get_tweet_analytics(self, tweet_id: str, access_token: str, access_token_secret: str) -> Dict[str, Any]:
        """Get analytics for a specific tweet"""
        try:
            # Create authenticated client
            client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            # Get tweet data with metrics
            tweet = client.get_tweet(
                id=tweet_id,
                tweet_fields=['public_metrics', 'created_at'],
                user_fields=['username']
            )
            
            if tweet.data:
                metrics = tweet.data.public_metrics
                return {
                    'likes': metrics.get('like_count', 0),
                    'retweets': metrics.get('retweet_count', 0),
                    'replies': metrics.get('reply_count', 0),
                    'impressions': metrics.get('impression_count', 0),
                    'created_at': tweet.data.created_at
                }
            
            return {}
            
        except Exception as e:
            logging.error(f"Tweet analytics error: {e}")
            return {}
    
    def search_tweets(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for tweets with specific query"""
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['public_metrics', 'created_at', 'author_id'],
                user_fields=['username', 'name']
            )
            
            if tweets.data:
                results = []
                for tweet in tweets.data:
                    results.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'author_id': tweet.author_id,
                        'created_at': tweet.created_at,
                        'metrics': tweet.public_metrics
                    })
                return results
            
            return []
            
        except Exception as e:
            logging.error(f"Tweet search error: {e}")
            return []
    
    def validate_credentials(self, access_token: str, access_token_secret: str) -> bool:
        """Validate Twitter credentials"""
        try:
            client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            # Try to get user info to validate credentials
            me = client.get_me()
            return me.data is not None
            
        except Exception as e:
            logging.error(f"Credential validation error: {e}")
            return False
