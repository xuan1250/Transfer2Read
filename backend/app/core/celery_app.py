"""
Celery Application Configuration

Initializes Celery with Redis broker and result backend.
Configures task serialization, tracking, and autodiscovery.
Includes periodic task scheduling via Celery Beat.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "transfer2read",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.ai_tasks', 'app.tasks.conversion_pipeline', 'app.tasks.usage_tasks']
)

# Configure Celery settings
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    
    # Timeouts (20 minutes max per job for LLM API calls)
    task_time_limit=1200,  # 20 minutes hard limit
    task_soft_time_limit=900,  # 15 minutes warning
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result expiration
    result_expires=3600,  # 1 hour
)

# Configure Celery Beat for periodic tasks
celery_app.conf.beat_schedule = {
    'monthly-usage-reset': {
        'task': 'app.tasks.usage_tasks.monthly_usage_reset',
        'schedule': crontab(day_of_month='1', hour='0', minute='0'),  # Run on 1st of month at 00:00 UTC
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        }
    },
}
