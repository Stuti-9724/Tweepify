import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import func
from app import db
from models import TweetAnalytics, ScheduledTweet, Campaign

class AnalyticsService:
    def get_user_analytics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive analytics for a user within a date range"""
        try:
            # Get tweet performance metrics
            tweet_metrics = db.session.query(
                func.sum(TweetAnalytics.likes).label('total_likes'),
                func.sum(TweetAnalytics.retweets).label('total_retweets'),
                func.sum(TweetAnalytics.replies).label('total_replies'),
                func.sum(TweetAnalytics.impressions).label('total_impressions'),
                func.avg(TweetAnalytics.engagement_rate).label('avg_engagement_rate'),
                func.count(TweetAnalytics.id).label('total_analyzed_tweets')
            ).filter(
                TweetAnalytics.user_id == user_id,
                TweetAnalytics.last_updated >= start_date,
                TweetAnalytics.last_updated <= end_date
            ).first()
            
            # Get posting activity
            posting_activity = db.session.query(
                func.count(ScheduledTweet.id).label('total_tweets'),
                func.sum(func.case([(ScheduledTweet.status == 'posted', 1)], else_=0)).label('posted_tweets'),
                func.sum(func.case([(ScheduledTweet.status == 'failed', 1)], else_=0)).label('failed_tweets'),
                func.sum(func.case([(ScheduledTweet.status == 'scheduled', 1)], else_=0)).label('scheduled_tweets')
            ).filter(
                ScheduledTweet.user_id == user_id,
                ScheduledTweet.created_at >= start_date,
                ScheduledTweet.created_at <= end_date
            ).first()
            
            # Calculate engagement metrics
            total_interactions = (tweet_metrics.total_likes or 0) + \
                               (tweet_metrics.total_retweets or 0) + \
                               (tweet_metrics.total_replies or 0)
            
            total_impressions = tweet_metrics.total_impressions or 0
            overall_engagement_rate = (total_interactions / total_impressions * 100) if total_impressions > 0 else 0
            
            # Get daily activity for charts
            daily_activity = self._get_daily_activity(user_id, start_date, end_date)
            
            return {
                'total_likes': tweet_metrics.total_likes or 0,
                'total_retweets': tweet_metrics.total_retweets or 0,
                'total_replies': tweet_metrics.total_replies or 0,
                'total_impressions': total_impressions,
                'overall_engagement_rate': round(overall_engagement_rate, 2),
                'avg_engagement_rate': round(tweet_metrics.avg_engagement_rate or 0, 2),
                'total_tweets': posting_activity.total_tweets or 0,
                'posted_tweets': posting_activity.posted_tweets or 0,
                'failed_tweets': posting_activity.failed_tweets or 0,
                'scheduled_tweets': posting_activity.scheduled_tweets or 0,
                'success_rate': round((posting_activity.posted_tweets or 0) / max(posting_activity.total_tweets or 1, 1) * 100, 2),
                'daily_activity': daily_activity
            }
            
        except Exception as e:
            logging.error(f"User analytics error: {e}")
            return self._get_empty_analytics()
    
    def get_campaign_analytics(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get analytics for all user campaigns"""
        try:
            campaigns = Campaign.query.filter_by(user_id=user_id).all()
            campaign_analytics = []
            
            for campaign in campaigns:
                # Get campaign tweet metrics
                metrics = db.session.query(
                    func.sum(TweetAnalytics.likes).label('likes'),
                    func.sum(TweetAnalytics.retweets).label('retweets'),
                    func.sum(TweetAnalytics.replies).label('replies'),
                    func.sum(TweetAnalytics.impressions).label('impressions'),
                    func.avg(TweetAnalytics.engagement_rate).label('avg_engagement'),
                    func.count(TweetAnalytics.id).label('tweet_count')
                ).filter(
                    TweetAnalytics.campaign_id == campaign.id,
                    TweetAnalytics.last_updated >= start_date,
                    TweetAnalytics.last_updated <= end_date
                ).first()
                
                # Get posting stats
                posting_stats = db.session.query(
                    func.count(ScheduledTweet.id).label('total_scheduled'),
                    func.sum(func.case([(ScheduledTweet.status == 'posted', 1)], else_=0)).label('posted')
                ).filter(
                    ScheduledTweet.campaign_id == campaign.id,
                    ScheduledTweet.created_at >= start_date,
                    ScheduledTweet.created_at <= end_date
                ).first()
                
                campaign_analytics.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'is_active': campaign.is_active,
                    'likes': metrics.likes or 0,
                    'retweets': metrics.retweets or 0,
                    'replies': metrics.replies or 0,
                    'impressions': metrics.impressions or 0,
                    'avg_engagement': round(metrics.avg_engagement or 0, 2),
                    'tweet_count': metrics.tweet_count or 0,
                    'total_scheduled': posting_stats.total_scheduled or 0,
                    'posted': posting_stats.posted or 0,
                    'success_rate': round((posting_stats.posted or 0) / max(posting_stats.total_scheduled or 1, 1) * 100, 2)
                })
            
            return campaign_analytics
            
        except Exception as e:
            logging.error(f"Campaign analytics error: {e}")
            return []
    
    def _get_daily_activity(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily posting activity for charts"""
        try:
            daily_data = db.session.query(
                func.date(ScheduledTweet.posted_at).label('date'),
                func.count(ScheduledTweet.id).label('posts'),
                func.sum(TweetAnalytics.likes).label('likes'),
                func.sum(TweetAnalytics.retweets).label('retweets')
            ).outerjoin(
                TweetAnalytics, ScheduledTweet.tweet_id == TweetAnalytics.tweet_id
            ).filter(
                ScheduledTweet.user_id == user_id,
                ScheduledTweet.status == 'posted',
                ScheduledTweet.posted_at >= start_date,
                ScheduledTweet.posted_at <= end_date
            ).group_by(
                func.date(ScheduledTweet.posted_at)
            ).order_by(
                func.date(ScheduledTweet.posted_at)
            ).all()
            
            return [
                {
                    'date': item.date.strftime('%Y-%m-%d') if item.date else '',
                    'posts': item.posts or 0,
                    'likes': item.likes or 0,
                    'retweets': item.retweets or 0
                }
                for item in daily_data
            ]
            
        except Exception as e:
            logging.error(f"Daily activity error: {e}")
            return []
    
    def update_tweet_analytics(self, tweet_id: str, analytics_data: Dict[str, Any], user_id: int, campaign_id: int = None):
        """Update or create tweet analytics record"""
        try:
            # Check if analytics record exists
            existing_analytics = TweetAnalytics.query.filter_by(
                tweet_id=tweet_id,
                user_id=user_id
            ).first()
            
            # Calculate engagement rate
            total_engagement = analytics_data.get('likes', 0) + \
                             analytics_data.get('retweets', 0) + \
                             analytics_data.get('replies', 0)
            impressions = analytics_data.get('impressions', 0)
            engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0
            
            if existing_analytics:
                # Update existing record
                existing_analytics.likes = analytics_data.get('likes', 0)
                existing_analytics.retweets = analytics_data.get('retweets', 0)
                existing_analytics.replies = analytics_data.get('replies', 0)
                existing_analytics.impressions = impressions
                existing_analytics.engagement_rate = engagement_rate
                existing_analytics.last_updated = datetime.utcnow()
            else:
                # Create new record
                new_analytics = TweetAnalytics(
                    tweet_id=tweet_id,
                    likes=analytics_data.get('likes', 0),
                    retweets=analytics_data.get('retweets', 0),
                    replies=analytics_data.get('replies', 0),
                    impressions=impressions,
                    engagement_rate=engagement_rate,
                    user_id=user_id,
                    campaign_id=campaign_id
                )
                db.session.add(new_analytics)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Analytics update error: {e}")
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'total_likes': 0,
            'total_retweets': 0,
            'total_replies': 0,
            'total_impressions': 0,
            'overall_engagement_rate': 0,
            'avg_engagement_rate': 0,
            'total_tweets': 0,
            'posted_tweets': 0,
            'failed_tweets': 0,
            'scheduled_tweets': 0,
            'success_rate': 0,
            'daily_activity': []
        }
    
    def get_top_performing_tweets(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing tweets by engagement"""
        try:
            top_tweets = db.session.query(
                TweetAnalytics, ScheduledTweet.content
            ).join(
                ScheduledTweet, TweetAnalytics.tweet_id == ScheduledTweet.tweet_id
            ).filter(
                TweetAnalytics.user_id == user_id
            ).order_by(
                TweetAnalytics.engagement_rate.desc()
            ).limit(limit).all()
            
            return [
                {
                    'content': tweet.content[:100] + '...' if len(tweet.content) > 100 else tweet.content,
                    'likes': analytics.likes,
                    'retweets': analytics.retweets,
                    'replies': analytics.replies,
                    'engagement_rate': round(analytics.engagement_rate, 2),
                    'impressions': analytics.impressions
                }
                for analytics, tweet in top_tweets
            ]
            
        except Exception as e:
            logging.error(f"Top tweets error: {e}")
            return []
