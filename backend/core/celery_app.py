"""Celery application configuration."""

import os
from celery import Celery
from celery.schedules import crontab

# Create Celery instance
celery_app = Celery(
    "research_papers",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "backend.tasks.paper_tasks",
        "backend.tasks.pipeline_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Daily paper ingestion at 2 AM UTC
    "daily-paper-ingestion": {
        "task": "backend.tasks.pipeline_tasks.daily_paper_ingestion",
        "schedule": crontab(hour=2, minute=0),
    },
    # Weekly backfill on Mondays at 3 AM UTC
    "weekly-paper-backfill": {
        "task": "backend.tasks.pipeline_tasks.weekly_paper_backfill",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),
    },
    # Cleanup old tasks daily at 4 AM UTC
    "cleanup-old-tasks": {
        "task": "backend.tasks.pipeline_tasks.cleanup_old_tasks",
        "schedule": crontab(hour=4, minute=0),
    },
}