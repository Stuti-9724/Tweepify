from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    twitter_access_token = db.Column(db.String(500))
    twitter_access_token_secret = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='user', lazy=True, cascade='all, delete-orphan')
    tweets = db.relationship('ScheduledTweet', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_twitter_auth(self):
        return self.twitter_access_token and self.twitter_access_token_secret

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)  # JSON string of keywords
    hashtags = db.Column(db.Text)  # JSON string of hashtags
    target_audience = db.Column(db.String(500))
    tweet_frequency = db.Column(db.Integer, default=3)  # tweets per day
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    tweets = db.relationship('ScheduledTweet', backref='campaign', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('TweetAnalytics', backref='campaign', lazy=True, cascade='all, delete-orphan')

class TweetTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    template = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScheduledTweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, posted, failed, cancelled
    tweet_id = db.Column(db.String(100))  # Twitter tweet ID after posting
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posted_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))

class TweetAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.String(100), nullable=False)
    likes = db.Column(db.Integer, default=0)
    retweets = db.Column(db.Integer, default=0)
    replies = db.Column(db.Integer, default=0)
    impressions = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class TrendingHashtag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hashtag = db.Column(db.String(200), nullable=False)
    tweet_volume = db.Column(db.Integer)
    trend_rank = db.Column(db.Integer)
    location = db.Column(db.String(100), default='Global')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
