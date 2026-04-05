"""
Decision Engine routes — AI-powered life decision simulation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.ai.engines import DecisionEngine
from app.services.profile_service import get_full_profile
from app.models.decision import Decision

router = APIRouter()
engine = DecisionEngine()


class DecisionRequest(BaseModel):
    question: str
    context: Optional[dict] = None


class ChooseScenarioRequest(BaseModel):
    decision_id: UUID
    scenario_id: str


@router.post("/simulate")
async def simulate_decision(
    body: DecisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    The core Decision Engine endpoint.
    Accepts a life question, returns 3-5 scenarios with risk analysis.
    """
    profile = await get_full_profile(user_id, db)
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")

    result = await engine.simulate(body.question, profile, body.context)

    decision = Decision(
        user_id=user_id,
        question=body.question,
        context=body.context,
        scenarios=result.get("scenarios", []),
        risk_score=result.get("risk_score"),
        risk_factors=result.get("risk_factors"),
        recommendation=result.get("recommendation"),
    )
    db.add(decision)
    await db.flush()

    return {
        "decision_id": str(decision.id),
        **result,
    }


@router.post("/choose")
async def choose_scenario(
    body: ChooseScenarioRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Record which scenario the user chose."""
    decision = await db.scalar(
        select(Decision).where(
            Decision.id == body.decision_id,
            Decision.user_id == user_id,
        )
    )
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.chosen_scenario = body.scenario_id
    return {"status": "recorded", "chosen": body.scenario_id}


@router.get("/history")
async def decision_history(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    from sqlalchemy import desc
    decisions = await db.scalars(
        select(Decision)
        .where(Decision.user_id == user_id)
        .order_by(desc(Decision.created_at))
        .limit(limit)
        .offset(offset)
    )
    return [
        {
            "id": str(d.id),
            "question": d.question,
            "risk_score": d.risk_score,
            "recommendation": d.recommendation,
            "chosen_scenario": d.chosen_scenario,
            "created_at": d.created_at.isoformat(),
        }
        for d in decisions
    ]
