"""Events and Admin route stubs"""
from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.security import get_current_user_id

router = APIRouter()  # events
admin_router = APIRouter()  # admin — import both

@router.get("/pending")
async def get_pending_events(user_id: UUID = Depends(get_current_user_id)):
    return {"events": [], "note": "Use /api/v1/simulation/event/generate to create events"}
