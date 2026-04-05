"""SQLAlchemy ORM Models"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, SmallInteger, Boolean, Text, Numeric, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def now(): return datetime.now(timezone.utc)
def gen_uuid(): return uuid.uuid4()


# --- USER ---
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_at: Mapped[datetime | None] = mapped_column(Date, nullable=True)


# --- PROFILE ---
class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    age: Mapped[int | None] = mapped_column(SmallInteger)
    location: Mapped[str | None] = mapped_column(Text)
    job: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    income: Mapped[float | None] = mapped_column(Numeric(12, 2))
    savings: Mapped[float | None] = mapped_column(Numeric(12, 2))
    health: Mapped[int | None] = mapped_column(SmallInteger)
    energy: Mapped[int | None] = mapped_column(SmallInteger)
    happiness: Mapped[int | None] = mapped_column(SmallInteger)
    discipline: Mapped[int | None] = mapped_column(SmallInteger)
    habit_sleep: Mapped[int | None] = mapped_column(SmallInteger)
    habit_sport: Mapped[int | None] = mapped_column(SmallInteger)
    habit_learning: Mapped[int | None] = mapped_column(SmallInteger)
    risk_tolerance: Mapped[int | None] = mapped_column(SmallInteger)
    behavior_type: Mapped[str | None] = mapped_column(String(50))
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


# --- GAME STATS ---
class GameStats(Base):
    __tablename__ = "game_stats"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    stat_health: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_energy: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_wealth: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_knowledge: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_happiness: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_discipline: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_career: Mapped[int] = mapped_column(SmallInteger, default=50)
    stat_social: Mapped[int] = mapped_column(SmallInteger, default=50)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


# --- QUEST ---
class Quest(Base):
    __tablename__ = "quests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    action_steps: Mapped[dict | None] = mapped_column(JSONB)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    stat_rewards: Mapped[dict | None] = mapped_column(JSONB)
    buff_rewards: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="active")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# --- DECISION ---
class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSONB)
    scenarios: Mapped[dict] = mapped_column(JSONB)
    risk_score: Mapped[int | None] = mapped_column(SmallInteger)
    risk_factors: Mapped[dict | None] = mapped_column(JSONB)
    recommendation: Mapped[str | None] = mapped_column(String(20))
    chosen_scenario: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# --- LIFE EVENT ---
class LifeEvent(Base):
    __tablename__ = "life_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(30))
    options: Mapped[dict] = mapped_column(JSONB)
    chosen_option: Mapped[str | None] = mapped_column(String(50))
    consequence: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# --- GOAL ---
class UserGoal(Base):
    __tablename__ = "user_goals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(30))
    target_date: Mapped[datetime | None] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


# --- FUTURE SIMULATION ---
class FutureSimulation(Base):
    __tablename__ = "future_simulations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    baseline_path: Mapped[dict | None] = mapped_column(JSONB)
    optimized_path: Mapped[dict | None] = mapped_column(JSONB)
    horizon_years: Mapped[int] = mapped_column(SmallInteger, default=10)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# --- STAT HISTORY ---
class StatHistory(Base):
    __tablename__ = "stat_history"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    level: Mapped[int | None] = mapped_column(Integer)
    stat_health: Mapped[int | None] = mapped_column(SmallInteger)
    stat_energy: Mapped[int | None] = mapped_column(SmallInteger)
    stat_wealth: Mapped[int | None] = mapped_column(SmallInteger)
    stat_knowledge: Mapped[int | None] = mapped_column(SmallInteger)
    stat_happiness: Mapped[int | None] = mapped_column(SmallInteger)
    stat_discipline: Mapped[int | None] = mapped_column(SmallInteger)
    stat_career: Mapped[int | None] = mapped_column(SmallInteger)
    stat_social: Mapped[int | None] = mapped_column(SmallInteger)
