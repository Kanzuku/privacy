"""Game Stats route"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.game_stats import GameStats
from app.models.stat_history import StatHistory

router = APIRouter()


@router.get("/")
async def get_stats(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found — complete onboarding")
    return stats


@router.get("/history")
async def get_stat_history(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    days: int = 30,
):
    from datetime import datetime, timezone, timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)
    history = await db.scalars(
        select(StatHistory)
        .where(StatHistory.user_id == user_id, StatHistory.snapshot_at >= since)
        .order_by(desc(StatHistory.snapshot_at))
    )
    return list(history)
