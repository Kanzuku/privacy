"""
Quest system routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.ai.engines import GameEngine
from app.services.profile_service import get_full_profile
from app.services.stats_service import apply_quest_rewards
from app.models.quest import Quest
from app.models.game_stats import GameStats

router = APIRouter()
engine = GameEngine()


class GenerateQuestsRequest(BaseModel):
    quest_type: str = "daily"   # daily | weekly | main | skill
    focus_area: Optional[str] = None
    count: int = 3


@router.post("/generate")
async def generate_quests(
    body: GenerateQuestsRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """AI-generates personalized quests for the user."""
    profile = await get_full_profile(user_id, db)
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")

    stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
    stats_dict = {k: v for k, v in vars(stats).items() if not k.startswith("_")} if stats else {}

    quests_data = await engine.generate_quests(
        profile=profile,
        game_stats=stats_dict,
        quest_type=body.quest_type,
        focus_area=body.focus_area,
        count=body.count,
    )

    created = []
    for q in quests_data:
        due = None
        if body.quest_type == "daily":
            due = datetime.now(timezone.utc) + timedelta(days=1)
        elif body.quest_type == "weekly":
            due = datetime.now(timezone.utc) + timedelta(days=7)

        quest = Quest(
            user_id=user_id,
            type=body.quest_type,
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
        created.append({"id": str(quest.id), **q})

    return {"quests": created}


@router.get("/active")
async def get_active_quests(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    quests = await db.scalars(
        select(Quest).where(
            and_(Quest.user_id == user_id, Quest.status == "active")
        )
    )
    return [
        {
            "id": str(q.id),
            "type": q.type,
            "title": q.title,
            "description": q.description,
            "action_steps": q.action_steps,
            "xp_reward": q.xp_reward,
            "stat_rewards": q.stat_rewards,
            "buff_rewards": q.buff_rewards,
            "due_at": q.due_at.isoformat() if q.due_at else None,
            "status": q.status,
        }
        for q in quests
    ]


@router.post("/{quest_id}/complete")
async def complete_quest(
    quest_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    quest = await db.scalar(
        select(Quest).where(Quest.id == quest_id, Quest.user_id == user_id)
    )
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.status != "active":
        raise HTTPException(status_code=400, detail=f"Quest is {quest.status}")

    quest.status = "completed"
    quest.completed_at = datetime.now(timezone.utc)

    rewards = await apply_quest_rewards(user_id, quest, db)
    return {
        "message": "Quest completed!",
        "xp_gained": quest.xp_reward,
        "new_level": rewards.get("new_level"),
        "stat_changes": quest.stat_rewards,
        "buffs_activated": quest.buff_rewards,
    }


@router.post("/{quest_id}/fail")
async def fail_quest(
    quest_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    quest = await db.scalar(
        select(Quest).where(Quest.id == quest_id, Quest.user_id == user_id)
    )
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    quest.status = "failed"
    return {"message": "Quest marked as failed", "quest_id": str(quest_id)}
