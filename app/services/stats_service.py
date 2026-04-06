"""
Stats Service — XP calculation, leveling, stat change application
"""
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models import GameStats, StatHistory, Quest


def calculate_level(total_xp: int) -> int:
    """XP curve: each level requires level² × 100 XP. Smooth logarithmic feel."""
    return max(1, int(math.sqrt(total_xp / 100)))


def xp_to_next_level(current_level: int) -> int:
    """XP needed to reach next level."""
    return ((current_level + 1) ** 2) * 100


def xp_progress_percent(total_xp: int) -> float:
    """Percentage progress toward next level (0.0–1.0)."""
    level = calculate_level(total_xp)
    current_level_xp = (level ** 2) * 100
    next_level_xp = ((level + 1) ** 2) * 100
    if next_level_xp == current_level_xp:
        return 1.0
    return (total_xp - current_level_xp) / (next_level_xp - current_level_xp)


async def apply_quest_rewards(user_id: UUID, quest: Quest, db: AsyncSession) -> dict:
    """
    Apply XP and stat rewards from a completed quest.
    Handles leveling up and stat clamping.
    Returns dict with new_level and leveled_up flag.
    """
    stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
    if not stats:
        return {}

    old_level = stats.level
    stats.total_xp += quest.xp_reward or 0
    new_level = calculate_level(stats.total_xp)
    stats.level = new_level

    # Apply stat changes
    if quest.stat_rewards:
        stat_map = {
            "health": "stat_health",
            "energy": "stat_energy",
            "wealth": "stat_wealth",
            "knowledge": "stat_knowledge",
            "happiness": "stat_happiness",
            "discipline": "stat_discipline",
            "career": "stat_career",
            "social": "stat_social",
        }
        for stat_name, delta in quest.stat_rewards.items():
            col = stat_map.get(stat_name, f"stat_{stat_name}")
            if hasattr(stats, col):
                current = getattr(stats, col) or 0
                setattr(stats, col, max(0, min(100, current + int(delta))))

    # Snapshot stat history daily
    await _snapshot_stats(user_id, stats, db)

    return {
        "new_level": new_level,
        "leveled_up": new_level > old_level,
        "total_xp": stats.total_xp,
        "xp_progress": xp_progress_percent(stats.total_xp),
    }


async def _snapshot_stats(user_id: UUID, stats: GameStats, db: AsyncSession):
    """Record a stat history snapshot (called on significant events)."""
    from datetime import datetime, timezone
    snapshot = StatHistory(
        user_id=user_id,
        snapshot_at=datetime.now(timezone.utc),
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
