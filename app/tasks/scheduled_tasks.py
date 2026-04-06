"""
ME — The Life Game | Scheduled Tasks (Celery Beat)
Runs on a timer to maintain game state for all users.
"""
import asyncio
import random
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task
def expire_daily_quests():
    """Mark all overdue daily quests as 'expired'."""
    return _run(_expire_quests("daily"))


@shared_task
def expire_weekly_quests():
    """Mark all overdue weekly quests as 'expired'."""
    return _run(_expire_quests("weekly"))


async def _expire_quests(quest_type: str):
    from datetime import datetime, timezone
    from sqlalchemy import update, and_
    from app.core.database import AsyncSessionLocal
    from app.models.__init__ import Quest

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Quest)
            .where(and_(
                Quest.type == quest_type,
                Quest.status == "active",
                Quest.due_at < now,
            ))
            .values(status="expired")
            .returning(Quest.id)
        )
        await db.commit()
        expired = result.rowcount
        logger.info(f"Expired {expired} {quest_type} quests")
        return {"expired": expired}


@shared_task
def check_streak_breaks():
    """
    Reset streaks for users who missed yesterday.
    Runs daily at 00:15 UTC.
    """
    return _run(_check_streaks())


async def _check_streaks():
    from datetime import date, timedelta
    from sqlalchemy import select, update
    from app.core.database import AsyncSessionLocal
    from app.models.__init__ import User

    yesterday = date.today() - timedelta(days=1)

    async with AsyncSessionLocal() as db:
        # Users who have a streak but haven't logged in since before yesterday
        result = await db.execute(
            update(User)
            .where(
                User.streak_days > 0,
                User.last_streak_at < yesterday,
            )
            .values(streak_days=0)
            .returning(User.id)
        )
        await db.commit()
        reset = result.rowcount
        logger.info(f"Reset streaks for {reset} users")
        return {"reset": reset}


@shared_task
def maybe_generate_random_events():
    """
    For each active user, roll a 20% chance to generate a random life event.
    Only runs if user has no pending events already.
    Runs every 6 hours.
    """
    return _run(_maybe_generate_events())


async def _maybe_generate_events():
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.__init__ import User, LifeEvent, UserProfile
    from app.tasks.ai_tasks import generate_random_event_async

    async with AsyncSessionLocal() as db:
        # Get active users (logged in within last 7 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        active_users = await db.scalars(
            select(User.id)
            .join(UserProfile, UserProfile.user_id == User.id)
            .where(
                User.last_active_at >= cutoff,
                UserProfile.onboarding_done == True,
            )
        )
        user_ids = list(active_users)

        triggered = 0
        for user_id in user_ids:
            # Check no pending event already
            pending_count = await db.scalar(
                select(func.count())
                .select_from(LifeEvent)
                .where(
                    LifeEvent.user_id == user_id,
                    LifeEvent.status == "pending",
                )
            )
            if pending_count and pending_count > 0:
                continue

            # 20% chance
            if random.random() < 0.20:
                generate_random_event_async.delay(str(user_id))
                triggered += 1

        logger.info(f"Random events triggered for {triggered}/{len(user_ids)} users")
        return {"triggered": triggered, "checked": len(user_ids)}


@shared_task
def take_daily_stat_snapshots():
    """
    Snapshot all users' current stats for history charts.
    Runs daily at 01:00 UTC.
    """
    return _run(_snapshot_stats())


async def _snapshot_stats():
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.__init__ import GameStats, StatHistory

    async with AsyncSessionLocal() as db:
        all_stats = await db.scalars(select(GameStats))
        count = 0
        for stats in all_stats:
            snapshot = StatHistory(
                user_id=stats.user_id,
                level=stats.level,
                stat_health=stats.stat_health,
                stat_energy=stats.stat_energy,
                stat_wealth=stats.stat_wealth,
                stat_knowledge=stats.stat_knowledge,
                stat_happiness=stats.stat_happiness,
                stat_discipline=stats.stat_discipline,
                stat_career=stats.stat_career,
                stat_social=stats.stat_social,
            )
            db.add(snapshot)
            count += 1
        await db.commit()
        logger.info(f"Snapshotted stats for {count} users")
        return {"snapshots": count}
