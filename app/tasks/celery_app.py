"""
ME — The Life Game | Celery Task Queue
Handles all async AI operations and scheduled jobs.

Tasks:
- generate_daily_quests_for_all  (scheduled, midnight)
- expire_stale_quests            (scheduled, every hour)
- reset_daily_streaks            (scheduled, midnight)
- generate_quests_async          (on-demand, called from API)
- run_state_engine_async         (on-demand, background analysis)
- generate_random_event_async    (on-demand, probability-gated)
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "me_game",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.ai_tasks", "app.tasks.scheduled_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_soft_time_limit=120,   # 2 min — AI calls can be slow
    task_time_limit=180,
    worker_prefetch_multiplier=1,  # fair scheduling for slow AI tasks
    task_acks_late=True,
)

# ─── Beat Schedule (recurring tasks) ─────────────────────────────────────────

celery_app.conf.beat_schedule = {
    # Expire daily quests every night at 00:05 UTC
    "expire-daily-quests": {
        "task": "app.tasks.scheduled_tasks.expire_daily_quests",
        "schedule": crontab(hour=0, minute=5),
    },
    # Expire weekly quests every Monday at 00:10 UTC
    "expire-weekly-quests": {
        "task": "app.tasks.scheduled_tasks.expire_weekly_quests",
        "schedule": crontab(hour=0, minute=10, day_of_week=1),
    },
    # Reset streak check every day at 00:15 UTC
    "check-streak-breaks": {
        "task": "app.tasks.scheduled_tasks.check_streak_breaks",
        "schedule": crontab(hour=0, minute=15),
    },
    # Generate random events for active users — every 6 hours, 20% probability
    "maybe-generate-events": {
        "task": "app.tasks.scheduled_tasks.maybe_generate_random_events",
        "schedule": crontab(hour="*/6", minute=30),
    },
    # Take stat snapshots for all users daily
    "daily-stat-snapshot": {
        "task": "app.tasks.scheduled_tasks.take_daily_stat_snapshots",
        "schedule": crontab(hour=1, minute=0),
    },
}
