import logging
from datetime import datetime, timedelta
from celery import Celery
from app import app, db
from models import ScheduledTweet, User, TweetAnalytics, TrendingHashtag
from services.twitter_service import TwitterService
from services.analytics_service import AnalyticsService

# Create Celery instance
celery_app = Celery('twitter_campaign_manager')
celery_app.config_from_object('celery_app')

twitter_service = TwitterService()
analytics_service = AnalyticsService()

@celery_app.task(bind=True, max_retries=3)
def schedule_tweet_task(self, scheduled_tweet_id):
    """Background task to post a scheduled tweet"""
    try:
        with app.app_context():
            # Get the scheduled tweet
            scheduled_tweet = ScheduledTweet.query.get(scheduled_tweet_id)
            if not scheduled_tweet:
                logging.error(f"Scheduled tweet {scheduled_tweet_id} not found")
                return
            
            # Check if already posted or cancelled
            if scheduled_tweet.status != 'scheduled':
                logging.info(f"Tweet {scheduled_tweet_id} status is {scheduled_tweet.status}, skipping")
                return
            
            # Get user's Twitter credentials
            user = User.query.get(scheduled_tweet.user_id)
            if not user or not user.has_twitter_auth():
                scheduled_tweet.status = 'failed'
                scheduled_tweet.error_message = 'Twitter authentication required'
                db.session.commit()
                logging.error(f"User {scheduled_tweet.user_id} missing Twitter auth")
                return
            
            # Validate credentials before posting
            if not twitter_service.validate_credentials(
                user.twitter_access_token, 
                user.twitter_access_token_secret
            ):
                scheduled_tweet.status = 'failed'
                scheduled_tweet.error_message = 'Invalid Twitter credentials'
                db.session.commit()
                logging.error(f"Invalid Twitter credentials for user {user.id}")
                return
            
            # Post the tweet
            try:
                tweet_id = twitter_service.post_tweet(
                    scheduled_tweet.content,
                    user.twitter_access_token,
                    user.twitter_access_token_secret
                )
                
                # Update the scheduled tweet record
                scheduled_tweet.status = 'posted'
                scheduled_tweet.tweet_id = tweet_id
                scheduled_tweet.posted_at = datetime.utcnow()
                scheduled_tweet.error_message = None
                
                db.session.commit()
                
                # Schedule analytics collection
                collect_tweet_analytics.apply_async(
                    args=[tweet_id, user.id, scheduled_tweet.campaign_id],
                    countdown=300  # Wait 5 minutes before collecting initial analytics
                )
                
                logging.info(f"Successfully posted tweet {scheduled_tweet_id} as {tweet_id}")
                
            except Exception as e:
                # Handle posting error
                scheduled_tweet.status = 'failed'
                scheduled_tweet.error_message = str(e)
                db.session.commit()
                
                logging.error(f"Failed to post tweet {scheduled_tweet_id}: {e}")
                raise self.retry(countdown=60 * (2 ** self.request.retries))
    
    except Exception as e:
        logging.error(f"Tweet posting task error: {e}")
        # Don't retry on unexpected errors
        return

@celery_app.task(bind=True, max_retries=2)
def collect_tweet_analytics(self, tweet_id, user_id, campaign_id=None):
    """Background task to collect tweet analytics"""
    try:
        with app.app_context():
            user = User.query.get(user_id)
            if not user or not user.has_twitter_auth():
                logging.error(f"User {user_id} missing Twitter auth for analytics")
                return
            
            # Get tweet analytics from Twitter
            analytics_data = twitter_service.get_tweet_analytics(
                tweet_id,
                user.twitter_access_token,
                user.twitter_access_token_secret
            )
            
            if analytics_data:
                # Update analytics in database
                analytics_service.update_tweet_analytics(
                    tweet_id, 
                    analytics_data, 
                    user_id, 
                    campaign_id
                )
                
                logging.info(f"Updated analytics for tweet {tweet_id}")
            else:
                logging.warning(f"No analytics data received for tweet {tweet_id}")
    
    except Exception as e:
        logging.error(f"Analytics collection error: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)  # Retry after 5 minutes

@celery_app.task
def refresh_trending_hashtags():
    """Periodic task to refresh trending hashtags"""
    try:
        with app.app_context():
            # This will update the database with fresh trending data
            trending_hashtags = twitter_service.get_trending_hashtags()
            logging.info(f"Refreshed {len(trending_hashtags)} trending hashtags")
    
    except Exception as e:
        logging.error(f"Trending hashtags refresh error: {e}")

@celery_app.task
def cleanup_old_data():
    """Periodic task to clean up old data"""
    try:
        with app.app_context():
            # Clean up old scheduled tweets (completed > 30 days ago)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_tweets = ScheduledTweet.query.filter(
                ScheduledTweet.posted_at < cutoff_date,
                ScheduledTweet.status.in_(['posted', 'failed'])
            ).all()
            
            for tweet in old_tweets:
                db.session.delete(tweet)
            
            # Clean up old trending hashtags (> 24 hours old)
            yesterday = datetime.utcnow() - timedelta(hours=24)
            old_trends = TrendingHashtag.query.filter(
                TrendingHashtag.updated_at < yesterday
            ).all()
            
            for trend in old_trends:
                db.session.delete(trend)
            
            db.session.commit()
            logging.info(f"Cleaned up {len(old_tweets)} old tweets and {len(old_trends)} old trends")
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Data cleanup error: {e}")

@celery_app.task
def batch_analytics_update():
    """Periodic task to update analytics for recent tweets"""
    try:
        with app.app_context():
            # Get tweets posted in the last 24 hours that need analytics update
            yesterday = datetime.utcnow() - timedelta(hours=24)
            
            recent_tweets = db.session.query(ScheduledTweet, User).join(
                User, ScheduledTweet.user_id == User.id
            ).filter(
                ScheduledTweet.status == 'posted',
                ScheduledTweet.posted_at >= yesterday,
                User.twitter_access_token.isnot(None)
            ).all()
            
            updated_count = 0
            for tweet, user in recent_tweets:
                try:
                    analytics_data = twitter_service.get_tweet_analytics(
                        tweet.tweet_id,
                        user.twitter_access_token,
                        user.twitter_access_token_secret
                    )
                    
                    if analytics_data:
                        analytics_service.update_tweet_analytics(
                            tweet.tweet_id,
                            analytics_data,
                            user.id,
                            tweet.campaign_id
                        )
                        updated_count += 1
                
                except Exception as e:
                    logging.error(f"Failed to update analytics for tweet {tweet.tweet_id}: {e}")
                    continue
            
            logging.info(f"Updated analytics for {updated_count} tweets")
    
    except Exception as e:
        logging.error(f"Batch analytics update error: {e}")

# Periodic task schedule
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'refresh-trending-hashtags': {
        'task': 'tasks.refresh_trending_hashtags',
        'schedule': crontab(minute=0),  # Every hour
    },
    'batch-analytics-update': {
        'task': 'tasks.batch_analytics_update',
        'schedule': crontab(minute=0, hour='*/3'),  # Every 3 hours
    },
    'cleanup-old-data': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
}

celery_app.conf.timezone = 'UTC'
