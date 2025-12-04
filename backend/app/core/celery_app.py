"""
Celery Application Configuration

Initializes Celery with Redis broker and result backend.
Configures task serialization, tracking, and autodiscovery.
"""
from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "transfer2read",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.ai_tasks']
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
    
    # Timeouts (15 minutes max per job for LLM API calls)
    task_time_limit=900,  # 15 minutes hard limit
    task_soft_time_limit=840,  # 14 minutes warning
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result expiration
    result_expires=3600,  # 1 hour
)
