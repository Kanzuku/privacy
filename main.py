"""
ME — The Life Game | FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import (
    auth, profile, game_stats, quests,
    decisions, events, simulation, admin
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ME — The Life Game API",
    version="1.0.0",
    description="AI-powered life simulation game backend",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Register routers
app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["auth"])
app.include_router(profile.router,    prefix="/api/v1/profile",     tags=["profile"])
app.include_router(game_stats.router, prefix="/api/v1/stats",       tags=["game-stats"])
app.include_router(quests.router,     prefix="/api/v1/quests",      tags=["quests"])
app.include_router(decisions.router,  prefix="/api/v1/decisions",   tags=["decisions"])
app.include_router(events.router,     prefix="/api/v1/events",      tags=["events"])
app.include_router(simulation.router, prefix="/api/v1/simulation",  tags=["simulation"])
app.include_router(admin.router,      prefix="/api/v1/admin",       tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
