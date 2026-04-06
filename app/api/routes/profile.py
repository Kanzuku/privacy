"""
Profile route
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.profile import UserProfile
from app.models.game_stats import GameStats
from app.ai.engines import UserModelEngine, StateEngine

router = APIRouter()
user_model_engine = UserModelEngine()
state_engine = StateEngine()


class ProfileUpsertRequest(BaseModel):
    age: Optional[int] = None
    location: Optional[str] = None
    job: Optional[str] = None
    industry: Optional[str] = None
    income: Optional[float] = None
    savings: Optional[float] = None
    health: Optional[int] = None
    energy: Optional[int] = None
    happiness: Optional[int] = None
    discipline: Optional[int] = None
    habit_sleep: Optional[int] = None
    habit_sport: Optional[int] = None
    habit_learning: Optional[int] = None
    risk_tolerance: Optional[int] = None
    behavior_type: Optional[str] = None


@router.get("/")
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/")
async def upsert_profile(
    body: ProfileUpsertRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    # Auto-initialize game stats if first time
    stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
    if not stats:
        stats = GameStats(user_id=user_id)
        db.add(stats)

    profile.onboarding_done = True
    await db.flush()
    return {"message": "Profile updated", "user_id": str(user_id)}


@router.get("/analyze")
async def analyze_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Run User Model Engine analysis — returns life stage, archetype, problems, opportunities."""
    from app.services.profile_service import get_full_profile
    profile = await get_full_profile(user_id, db)
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")
    return await user_model_engine.analyze(profile)
