import os
from celery import Celery

# Celery configuration
broker_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
result_expires = 3600
timezone = 'UTC'
enable_utc = True

# Task routing
task_routes = {
    'tasks.schedule_tweet_task': {'queue': 'tweet_posting'},
    'tasks.collect_tweet_analytics': {'queue': 'analytics'},
    'tasks.refresh_trending_hashtags': {'queue': 'background'},
    'tasks.cleanup_old_data': {'queue': 'background'},
    'tasks.batch_analytics_update': {'queue': 'analytics'},
}

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
worker_disable_rate_limits = False

# Error handling
task_reject_on_worker_lost = True
task_ignore_result = False

# Retry settings
task_default_retry_delay = 60
task_max_retries = 3
