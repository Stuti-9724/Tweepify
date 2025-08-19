import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app import db
from models import Campaign, ScheduledTweet, TweetTemplate
from services.ai_service import AIService

class CampaignService:
    def __init__(self):
        self.ai_service = AIService()
    
    def create_campaign_from_template(self, user_id: int, template_data: Dict[str, Any]) -> Campaign:
        """Create a campaign from AI-generated template"""
        try:
            campaign = Campaign(
                name=template_data.get('name', 'New Campaign'),
                description=template_data.get('description', ''),
                keywords=json.dumps(template_data.get('keywords', [])),
                hashtags=json.dumps(template_data.get('hashtags', [])),
                target_audience=template_data.get('target_audience', ''),
                tweet_frequency=template_data.get('tweet_frequency', 3),
                user_id=user_id
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            return campaign
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Campaign creation error: {e}")
            raise Exception("Failed to create campaign")
    
    def generate_campaign_content(self, campaign_id: int, num_tweets: int = 5) -> List[str]:
        """Generate multiple tweet contents for a campaign"""
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                raise Exception("Campaign not found")
            
            # Parse campaign data
            keywords = json.loads(campaign.keywords) if campaign.keywords else []
            hashtags = json.loads(campaign.hashtags) if campaign.hashtags else []
            
            # Generate multiple variations
            generated_tweets = []
            for i in range(num_tweets):
                content = self.ai_service.generate_tweet_content(
                    keywords=', '.join(keywords),
                    hashtags=', '.join(hashtags),
                    target_audience=campaign.target_audience
                )
                
                if content and content not in generated_tweets:
                    generated_tweets.append(content)
            
            return generated_tweets
            
        except Exception as e:
            logging.error(f"Content generation error: {e}")
            return []
    
    def schedule_campaign_tweets(self, campaign_id: int, start_date: datetime, 
                               end_date: datetime, tweets_per_day: int = None) -> int:
        """Schedule tweets for a campaign over a date range"""
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                raise Exception("Campaign not found")
            
            frequency = tweets_per_day or campaign.tweet_frequency
            total_days = (end_date - start_date).days + 1
            total_tweets_needed = total_days * frequency
            
            # Generate content for all tweets
            tweet_contents = self.generate_campaign_content(campaign_id, total_tweets_needed)
            
            if not tweet_contents:
                raise Exception("Failed to generate tweet content")
            
            # Schedule tweets evenly across the date range
            scheduled_count = 0
            current_date = start_date
            content_index = 0
            
            while current_date <= end_date and content_index < len(tweet_contents):
                # Schedule tweets for this day
                for i in range(frequency):
                    if content_index >= len(tweet_contents):
                        break
                    
                    # Calculate posting time (spread throughout the day)
                    hour_offset = (i + 1) * (24 // (frequency + 1))
                    posting_time = current_date.replace(hour=hour_offset, minute=0, second=0)
                    
                    # Create scheduled tweet
                    scheduled_tweet = ScheduledTweet(
                        content=tweet_contents[content_index],
                        scheduled_time=posting_time,
                        user_id=campaign.user_id,
                        campaign_id=campaign_id
                    )
                    
                    db.session.add(scheduled_tweet)
                    scheduled_count += 1
                    content_index += 1
                
                current_date += timedelta(days=1)
            
            db.session.commit()
            return scheduled_count
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Tweet scheduling error: {e}")
            raise Exception("Failed to schedule tweets")
    
    def analyze_campaign_performance(self, campaign_id: int) -> Dict[str, Any]:
        """Analyze campaign performance and provide insights"""
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                raise Exception("Campaign not found")
            
            # Get campaign tweets and their analytics
            campaign_tweets = ScheduledTweet.query.filter_by(campaign_id=campaign_id).all()
            
            # Calculate performance metrics
            total_tweets = len(campaign_tweets)
            posted_tweets = len([t for t in campaign_tweets if t.status == 'posted'])
            failed_tweets = len([t for t in campaign_tweets if t.status == 'failed'])
            
            # Get engagement metrics from analytics
            from services.analytics_service import AnalyticsService
            analytics_service = AnalyticsService()
            
            end_date = datetime.utcnow()
            start_date = campaign.created_at
            
            campaign_analytics = analytics_service.get_campaign_analytics(
                campaign.user_id, start_date, end_date
            )
            
            # Find analytics for this specific campaign
            current_campaign_analytics = next(
                (ca for ca in campaign_analytics if ca['id'] == campaign_id),
                {}
            )
            
            # Generate AI insights
            insights = self._generate_campaign_insights(campaign, current_campaign_analytics)
            
            return {
                'campaign_name': campaign.name,
                'total_tweets': total_tweets,
                'posted_tweets': posted_tweets,
                'failed_tweets': failed_tweets,
                'success_rate': round(posted_tweets / max(total_tweets, 1) * 100, 2),
                'total_engagement': current_campaign_analytics.get('likes', 0) + 
                                 current_campaign_analytics.get('retweets', 0) + 
                                 current_campaign_analytics.get('replies', 0),
                'avg_engagement_rate': current_campaign_analytics.get('avg_engagement', 0),
                'total_impressions': current_campaign_analytics.get('impressions', 0),
                'insights': insights,
                'recommendations': self._get_campaign_recommendations(campaign, current_campaign_analytics)
            }
            
        except Exception as e:
            logging.error(f"Campaign analysis error: {e}")
            return {}
    
    def _generate_campaign_insights(self, campaign: Campaign, analytics: Dict[str, Any]) -> List[str]:
        """Generate AI-powered insights for campaign performance"""
        try:
            # Prepare data for AI analysis
            campaign_data = {
                'name': campaign.name,
                'frequency': campaign.tweet_frequency,
                'keywords': campaign.keywords,
                'hashtags': campaign.hashtags,
                'target_audience': campaign.target_audience,
                'total_tweets': analytics.get('tweet_count', 0),
                'engagement_rate': analytics.get('avg_engagement', 0),
                'impressions': analytics.get('impressions', 0),
                'likes': analytics.get('likes', 0),
                'retweets': analytics.get('retweets', 0)
            }
            
            prompt = f"""Analyze this social media campaign performance and provide 3-5 key insights:

Campaign Data: {json.dumps(campaign_data, indent=2)}

Provide actionable insights about:
- Performance trends
- Engagement patterns
- Content effectiveness
- Audience response
- Areas for improvement

Return insights as a JSON array of strings:
{{"insights": ["insight1", "insight2", "insight3"]}}"""

            response = self.ai_service.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            
            if response.text:
                result = json.loads(response.text)
                return result.get('insights', [])
            
            return []
            
        except Exception as e:
            logging.error(f"Campaign insights error: {e}")
            return []
    
    def _get_campaign_recommendations(self, campaign: Campaign, analytics: Dict[str, Any]) -> List[str]:
        """Get recommendations for campaign optimization"""
        recommendations = []
        
        # Analyze engagement rate
        engagement_rate = analytics.get('avg_engagement', 0)
        if engagement_rate < 2.0:
            recommendations.append("Consider using more engaging content formats and trending hashtags")
        elif engagement_rate > 5.0:
            recommendations.append("Great engagement! Consider increasing posting frequency")
        
        # Analyze posting frequency
        if campaign.tweet_frequency < 2:
            recommendations.append("Consider increasing posting frequency to maintain audience engagement")
        elif campaign.tweet_frequency > 5:
            recommendations.append("High posting frequency detected - ensure content quality remains high")
        
        # Analyze content performance
        total_tweets = analytics.get('tweet_count', 0)
        if total_tweets > 0:
            avg_likes = analytics.get('likes', 0) / total_tweets
            if avg_likes < 5:
                recommendations.append("Focus on creating more shareable and relatable content")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations = [
                "Continue monitoring campaign performance regularly",
                "Experiment with different posting times",
                "Engage with your audience through replies and interactions"
            ]
        
        return recommendations
    
    def pause_campaign(self, campaign_id: int) -> bool:
        """Pause a campaign and its scheduled tweets"""
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return False
            
            campaign.is_active = False
            
            # Cancel scheduled tweets
            scheduled_tweets = ScheduledTweet.query.filter_by(
                campaign_id=campaign_id,
                status='scheduled'
            ).all()
            
            for tweet in scheduled_tweets:
                tweet.status = 'cancelled'
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Campaign pause error: {e}")
            return False
    
    def resume_campaign(self, campaign_id: int) -> bool:
        """Resume a paused campaign"""
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return False
            
            campaign.is_active = True
            
            # Reactivate future scheduled tweets
            future_tweets = ScheduledTweet.query.filter(
                ScheduledTweet.campaign_id == campaign_id,
                ScheduledTweet.status == 'cancelled',
                ScheduledTweet.scheduled_time > datetime.utcnow()
            ).all()
            
            for tweet in future_tweets:
                tweet.status = 'scheduled'
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Campaign resume error: {e}")
            return False
