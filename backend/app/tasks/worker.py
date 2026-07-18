from celery import Celery
from app.config.settings import settings

# Create Celery app instance using Redis as broker and result storage
celery_app = Celery(
    "sentinel_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.scan_tasks"]
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Shorten time limits for safety
    task_time_limit=3600, # 1 hour max
    task_soft_time_limit=3000
)

# Configure Celery Beat schedule to check hourly for scheduled scans
celery_app.conf.beat_schedule = {
    "check-scheduled-scans-every-hour": {
        "task": "app.tasks.scan_tasks.check_scheduled_scans",
        "schedule": 3600.0,  # Run every hour (3600 seconds)
    }
}
