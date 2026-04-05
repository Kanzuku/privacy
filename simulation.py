"""
Future Simulation routes — the viral "your life in 10 years" feature
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.ai.engines import FutureSimulationEngine, GameEngine
from app.services.profile_service import get_full_profile
from app.models.game_stats import GameStats
from app.models.goal import UserGoal
from app.models.simulation import FutureSimulation
from app.models.event import LifeEvent
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
sim_engine = FutureSimulationEngine()
game_engine = GameEngine()


# --- FUTURE SIMULATION ---

@router.post("/future")
async def generate_future_simulation(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate the viral "your life in 10 years" dual-path simulation.
    Expensive call — cached per user for 24h via Redis (see services).
    """
    profile = await get_full_profile(user_id, db)
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")

    stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
    goals = await db.scalars(
        select(UserGoal).where(UserGoal.user_id == user_id, UserGoal.status == "active")
    )
    goals_list = [
        {"title": g.title, "category": g.category, "target_date": str(g.target_date)}
        for g in goals
    ]

    stats_dict = {k: v for k, v in vars(stats).items() if not k.startswith("_")} if stats else {}

    result = await sim_engine.simulate(profile, stats_dict, goals_list)

    simulation = FutureSimulation(
        user_id=user_id,
        baseline_path=result.get("baseline_path"),
        optimized_path=result.get("optimized_path"),
        horizon_years=10,
    )
    db.add(simulation)
    await db.flush()

    return {
        "simulation_id": str(simulation.id),
        **result,
    }


@router.get("/future/latest")
async def get_latest_simulation(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    sim = await db.scalar(
        select(FutureSimulation)
        .where(FutureSimulation.user_id == user_id)
        .order_by(desc(FutureSimulation.generated_at))
        .limit(1)
    )
    if not sim:
        raise HTTPException(status_code=404, detail="No simulation found. Generate one first.")
    return {
        "simulation_id": str(sim.id),
        "baseline_path": sim.baseline_path,
        "optimized_path": sim.optimized_path,
        "generated_at": sim.generated_at.isoformat(),
    }


# --- RANDOM EVENTS ---

@router.post("/event/generate")
async def generate_random_event(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone, timedelta
    profile = await get_full_profile(user_id, db)
    stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
    recent = await db.scalars(
        select(LifeEvent)
        .where(LifeEvent.user_id == user_id)
        .order_by(desc(LifeEvent.created_at))
        .limit(5)
    )
    recent_list = [{"title": e.title, "category": e.category} for e in recent]

    stats_dict = {k: v for k, v in vars(stats).items() if not k.startswith("_")} if stats else {}
    event_data = await game_engine.generate_random_event(profile, stats_dict, recent_list)

    event = LifeEvent(
        user_id=user_id,
        title=event_data["title"],
        description=event_data["description"],
        category=event_data.get("category"),
        options=event_data.get("options", []),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=event_data.get("expires_hours", 48)),
    )
    db.add(event)
    await db.flush()

    return {"event_id": str(event.id), **event_data}


@router.post("/event/{event_id}/choose")
async def choose_event_option(
    event_id: UUID,
    option_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    event = await db.scalar(
        select(LifeEvent).where(LifeEvent.id == event_id, LifeEvent.user_id == user_id)
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != "pending":
        raise HTTPException(status_code=400, detail="Event already resolved")

    profile = await get_full_profile(user_id, db)
    consequence = await game_engine.resolve_event(
        event={"title": event.title, "description": event.description, "options": event.options},
        chosen_option=option_id,
        profile=profile,
    )

    event.chosen_option = option_id
    event.consequence = consequence
    event.status = "resolved"

    # Apply stat changes
    if "stat_changes" in consequence:
        stats = await db.scalar(select(GameStats).where(GameStats.user_id == user_id))
        if stats:
            updated = game_engine.apply_stat_changes(
                {k: v for k, v in vars(stats).items() if not k.startswith("_")},
                consequence["stat_changes"],
            )
            for k, v in updated.items():
                if hasattr(stats, k):
                    setattr(stats, k, v)

    return {"consequence": consequence}
