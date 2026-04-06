"""
Profile Service — assembles the full structured user model for AI engine calls
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models import UserProfile, User, UserGoal
from app.models import User as UserModel


async def get_full_profile(user_id: UUID, db: AsyncSession) -> dict | None:
    """
    Returns a complete, structured profile dict ready to pass to any AI engine.
    Returns None if onboarding is incomplete.
    """
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    if not profile or not profile.onboarding_done:
        return None

    user = await db.scalar(select(UserModel).where(UserModel.id == user_id))

    goals = await db.scalars(
        select(UserGoal).where(UserGoal.user_id == user_id, UserGoal.status == "active")
    )
    goals_list = [
        {"title": g.title, "category": g.category, "progress": g.progress}
        for g in goals
    ]

    return {
        "age": profile.age,
        "location": profile.location,
        "job": profile.job,
        "industry": profile.industry,
        "income": float(profile.income) if profile.income else None,
        "savings": float(profile.savings) if profile.savings else None,
        "health": profile.health,
        "energy": profile.energy,
        "happiness": profile.happiness,
        "discipline": profile.discipline,
        "habits": {
            "sleep": profile.habit_sleep,
            "sport": profile.habit_sport,
            "learning": profile.habit_learning,
        },
        "personality": {
            "risk_tolerance": profile.risk_tolerance,
            "behavior_type": profile.behavior_type,
        },
        "goals": goals_list,
        "streak_days": user.streak_days if user else 0,
        "is_premium": user.is_premium if user else False,
    }
