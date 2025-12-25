"""
Usage Tracking Celery Tasks

Periodic tasks for usage tracking maintenance and cleanup.
"""
import logging
from datetime import datetime, timezone
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.usage_tasks.monthly_usage_reset')
def monthly_usage_reset():
    """
    Monthly usage reset task (no-op in current design).

    This task runs on the 1st of every month at 00:00 UTC. However, it doesn't
    need to perform any actual reset operations because:

    1. New months are auto-created via UPSERT logic when users start conversions
    2. Old usage records are preserved for analytics (no deletion)
    3. Monthly boundaries are enforced by the (user_id, month) composite key

    The task serves as:
    - A logging checkpoint for monthly transitions
    - A placeholder for future cleanup tasks (e.g., archive old usage data)
    - A health check to verify Celery Beat is running

    Returns:
        dict: Task status with timestamp

    Example log output:
        INFO: Monthly usage reset triggered at 2025-12-01 00:00:00 UTC
        INFO: New month will auto-create on first conversion (UPSERT behavior)
        INFO: Old usage records preserved for analytics
    """
    now = datetime.now(timezone.utc)
    logger.info(f"Monthly usage reset triggered at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info("New month will auto-create on first conversion (UPSERT behavior)")
    logger.info("Old usage records preserved for analytics")

    # Future enhancement: Archive usage data older than 12 months
    # Example:
    # archive_threshold = (now - timedelta(days=365)).strftime('%Y-%m-01')
    # archive_old_usage(archive_threshold)

    return {
        "status": "success",
        "message": "Monthly reset checkpoint logged (no action needed)",
        "timestamp": now.isoformat()
    }
