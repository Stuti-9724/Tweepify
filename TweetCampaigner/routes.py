from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import json
import logging

from app import app, db
from models import User, Campaign, ScheduledTweet, TweetTemplate, TweetAnalytics, TrendingHashtag
from services.ai_service import AIService
from services.twitter_service import TwitterService
from services.analytics_service import AnalyticsService
from services.campaign_service import CampaignService
from tasks import schedule_tweet_task, collect_tweet_analytics

ai_service = AIService()
twitter_service = TwitterService()
analytics_service = AnalyticsService()
campaign_service = CampaignService()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            logging.error(f"Registration error: {e}")
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    total_campaigns = Campaign.query.filter_by(user_id=current_user.id).count()
    active_campaigns = Campaign.query.filter_by(user_id=current_user.id, is_active=True).count()
    total_tweets = ScheduledTweet.query.filter_by(user_id=current_user.id).count()
    posted_tweets = ScheduledTweet.query.filter_by(user_id=current_user.id, status='posted').count()
    
    # Get recent campaigns
    recent_campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).limit(5).all()
    
    # Get recent tweets
    recent_tweets = ScheduledTweet.query.filter_by(user_id=current_user.id).order_by(ScheduledTweet.created_at.desc()).limit(10).all()
    
    # Get trending hashtags
    trending_hashtags = TrendingHashtag.query.order_by(TrendingHashtag.trend_rank.asc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         total_campaigns=total_campaigns,
                         active_campaigns=active_campaigns,
                         total_tweets=total_tweets,
                         posted_tweets=posted_tweets,
                         recent_campaigns=recent_campaigns,
                         recent_tweets=recent_tweets,
                         trending_hashtags=trending_hashtags)

@app.route('/campaigns')
@login_required
def campaigns():
    page = request.args.get('page', 1, type=int)
    campaigns_query = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc())
    campaigns_pagination = campaigns_query.paginate(page=page, per_page=10, error_out=False)
    return render_template('campaigns.html', campaigns=campaigns_pagination)

@app.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        keywords = request.form['keywords']
        hashtags = request.form['hashtags']
        target_audience = request.form['target_audience']
        tweet_frequency = int(request.form.get('tweet_frequency', 3))
        
        campaign = Campaign(
            name=name,
            description=description,
            keywords=keywords,
            hashtags=hashtags,
            target_audience=target_audience,
            tweet_frequency=tweet_frequency,
            user_id=current_user.id
        )
        
        try:
            db.session.add(campaign)
            db.session.commit()
            flash('Campaign created successfully!', 'success')
            return redirect(url_for('campaigns'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create campaign. Please try again.', 'error')
            logging.error(f"Campaign creation error: {e}")
    
    return render_template('create_campaign.html')

@app.route('/campaigns/<int:campaign_id>/generate_content', methods=['POST'])
@login_required
def generate_content(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first_or_404()
    
    try:
        # Get trending hashtags for context
        trending_hashtags = twitter_service.get_trending_hashtags()
        
        # Generate AI content
        content = ai_service.generate_tweet_content(
            keywords=campaign.keywords,
            hashtags=campaign.hashtags,
            target_audience=campaign.target_audience,
            trending_hashtags=trending_hashtags
        )
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        logging.error(f"Content generation error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/schedule_tweet', methods=['POST'])
@login_required
def schedule_tweet():
    content = request.form['content']
    scheduled_time_str = request.form['scheduled_time']
    campaign_id = request.form.get('campaign_id')
    
    try:
        scheduled_time = datetime.fromisoformat(scheduled_time_str)
        
        # Check content length
        if len(content) > 280:
            flash('Tweet content exceeds 280 characters', 'error')
            return redirect(request.referrer)
        
        # Check for spam patterns
        if ai_service.check_spam_content(content):
            flash('Content flagged as potential spam. Please revise.', 'warning')
            return redirect(request.referrer)
        
        scheduled_tweet = ScheduledTweet(
            content=content,
            scheduled_time=scheduled_time,
            user_id=current_user.id,
            campaign_id=campaign_id if campaign_id else None
        )
        
        db.session.add(scheduled_tweet)
        db.session.commit()
        
        # Schedule the background task
        schedule_tweet_task.apply_async(args=[scheduled_tweet.id], eta=scheduled_time)
        
        flash('Tweet scheduled successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        db.session.rollback()
        flash('Failed to schedule tweet. Please try again.', 'error')
        logging.error(f"Tweet scheduling error: {e}")
        return redirect(request.referrer)

@app.route('/analytics')
@login_required
def analytics():
    # Get analytics data for the last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Get tweet performance data
    tweet_analytics = analytics_service.get_user_analytics(current_user.id, start_date, end_date)
    
    # Get campaign performance
    campaign_analytics = analytics_service.get_campaign_analytics(current_user.id, start_date, end_date)
    
    return render_template('analytics.html', 
                         tweet_analytics=tweet_analytics,
                         campaign_analytics=campaign_analytics)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        if 'twitter_auth' in request.form:
            # Handle Twitter OAuth
            auth_url = twitter_service.get_auth_url()
            session['oauth_token'] = twitter_service.get_request_token()
            return redirect(auth_url)
        
        elif 'update_profile' in request.form:
            # Update user profile
            current_user.email = request.form['email']
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Failed to update profile', 'error')
                logging.error(f"Profile update error: {e}")
    
    return render_template('settings.html')

@app.route('/twitter_callback')
@login_required
def twitter_callback():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    
    if oauth_token and oauth_verifier:
        try:
            access_token, access_token_secret = twitter_service.get_access_token(
                oauth_token, oauth_verifier
            )
            
            current_user.twitter_access_token = access_token
            current_user.twitter_access_token_secret = access_token_secret
            db.session.commit()
            
            flash('Twitter account connected successfully!', 'success')
        except Exception as e:
            flash('Failed to connect Twitter account', 'error')
            logging.error(f"Twitter callback error: {e}")
    
    return redirect(url_for('settings'))

@app.route('/api/trending_hashtags')
@login_required
def api_trending_hashtags():
    try:
        hashtags = twitter_service.get_trending_hashtags()
        return jsonify({'success': True, 'hashtags': hashtags})
    except Exception as e:
        logging.error(f"Trending hashtags error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
