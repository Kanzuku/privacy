"""
ME — The Life Game | Async AI Celery Tasks
Called from API routes to avoid blocking the request thread.
"""
import asyncio
from typing import Optional
from uuid import UUID
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _run(coro):
    """Run async coroutine in Celery's sync context."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_quests_async(
    self,
    user_id: str,
    quest_type: str = "daily",
    focus_area: Optional[str] = None,
    count: int = 3,
):
    """
    Background quest generation.
    Triggered after onboarding and daily at midnight.
    """
    try:
        return _run(_generate_quests(user_id, quest_type, focus_area, count))
    except Exception as exc:
        logger.error(f"Quest generation failed for {user_id}: {exc}")
        raise self.retry(exc=exc)


async def _generate_quests(user_id: str, quest_type: str, focus_area, count: int):
    from sqlalchemy import select
    from datetime import datetime, timezone, timedelta
    from app.core.database import AsyncSessionLocal
    from app.ai.engines import GameEngine
    from app.services.profile_service import get_full_profile
    from app.models.__init__ import GameStats, Quest

    engine = GameEngine()

    async with AsyncSessionLocal() as db:
        uid = UUID(user_id)
        profile = await get_full_profile(uid, db)
        if not profile:
            return {"error": "Profile incomplete"}

        stats = await db.scalar(select(GameStats).where(GameStats.user_id == uid))
        stats_dict = {k: v for k, v in vars(stats).items() if not k.startswith("_")} if stats else {}

        quests_data = await engine.generate_quests(
            profile=profile,
            game_stats=stats_dict,
            quest_type=quest_type,
            focus_area=focus_area,
            count=count,
        )

        due = None
        if quest_type == "daily":
            due = datetime.now(timezone.utc) + timedelta(days=1)
        elif quest_type == "weekly":
            due = datetime.now(timezone.utc) + timedelta(days=7)

        created_ids = []
        for q in quests_data:
            quest = Quest(
                user_id=uid,
                type=quest_type,
                title=q["title"],
                description=q["description"],
                action_steps=q.get("action_steps"),
                xp_reward=q.get("xp_reward", 0),
                stat_rewards=q.get("stat_rewards"),
                buff_rewards=q.get("buff_rewards"),
                due_at=due,
            )
            db.add(quest)
            await db.flush()
            created_ids.append(str(quest.id))

        await db.commit()
        logger.info(f"Generated {len(created_ids)} {quest_type} quests for {user_id}")
        return {"created": created_ids}


@shared_task(bind=True, max_retries=2)
def run_state_engine_async(self, user_id: str):
    """
    Run the State Engine in the background and cache the result.
    Triggered after profile updates and on a daily schedule.
    """
    try:
        return _run(_run_state_engine(user_id))
    except Exception as exc:
        logger.error(f"State engine failed for {user_id}: {exc}")
        raise self.retry(exc=exc)


async def _run_state_engine(user_id: str):
    from sqlalchemy import select, desc
    from app.core.database import AsyncSessionLocal
    from app.ai.engines import StateEngine
    from app.services.profile_service import get_full_profile
    from app.models.__init__ import Quest, Decision
    from app.cache.redis_cache import set_cache

    engine = StateEngine()

    async with AsyncSessionLocal() as db:
        uid = UUID(user_id)
        profile = await get_full_profile(uid, db)
        if not profile:
            return {"error": "Profile incomplete"}

        # Build history from recent quests + decisions
        recent_quests = await db.scalars(
            select(Quest)
            .where(Quest.user_id == uid, Quest.status == "completed")
            .order_by(desc(Quest.completed_at))
            .limit(10)
        )
        recent_decisions = await db.scalars(
            select(Decision)
            .where(Decision.user_id == uid)
            .order_by(desc(Decision.created_at))
            .limit(5)
        )

        history = [
            {"type": "quest_completed", "title": q.title, "date": str(q.completed_at)}
            for q in recent_quests
        ] + [
            {"type": "decision", "question": d.question, "recommendation": d.recommendation}
            for d in recent_decisions
        ]

        result = await engine.evaluate(profile, history)

        # Cache for 6 hours
        await set_cache(f"state:{user_id}", result, ttl=21600)
        logger.info(f"State engine completed for {user_id}")
        return result


@shared_task(bind=True, max_retries=2)
def generate_random_event_async(self, user_id: str):
    """Generate a random life event for a user."""
    try:
        return _run(_generate_event(user_id))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _generate_event(user_id: str):
    from sqlalchemy import select, desc
    from datetime import datetime, timezone, timedelta
    from app.core.database import AsyncSessionLocal
    from app.ai.engines import GameEngine
    from app.services.profile_service import get_full_profile
    from app.models.__init__ import GameStats, LifeEvent

    engine = GameEngine()

    async with AsyncSessionLocal() as db:
        uid = UUID(user_id)
        profile = await get_full_profile(uid, db)
        if not profile:
            return

        stats = await db.scalar(select(GameStats).where(GameStats.user_id == uid))
        stats_dict = {k: v for k, v in vars(stats).items() if not k.startswith("_")} if stats else {}

        recent = await db.scalars(
            select(LifeEvent)
            .where(LifeEvent.user_id == uid)
            .order_by(desc(LifeEvent.created_at))
            .limit(5)
        )
        recent_list = [{"title": e.title, "category": e.category} for e in recent]

        event_data = await engine.generate_random_event(profile, stats_dict, recent_list)

        event = LifeEvent(
            user_id=uid,
            title=event_data["title"],
            description=event_data["description"],
            category=event_data.get("category"),
            options=event_data.get("options", []),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=event_data.get("expires_hours", 48)),
        )
        db.add(event)
        await db.commit()
        logger.info(f"Random event generated for {user_id}: {event_data['title']}")
        return {"event_id": str(event.id)}
