"""
ME — The Life Game | Redis Cache Layer
Caches expensive AI responses to avoid redundant LLM calls.

Cache TTLs:
- State Engine result:      6 hours  (changes slowly)
- Future Simulation:        24 hours (very expensive, changes rarely)
- Profile Analysis:         12 hours
- Quest suggestions:        1 hour   (should feel fresh daily)
"""
import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_cache(key: str) -> Optional[Any]:
    """Retrieve a cached value. Returns None on miss or error."""
    try:
        r = await get_redis()
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


async def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """Store a value with TTL in seconds. Returns True on success."""
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        return False


async def delete_cache(key: str) -> bool:
    """Invalidate a cache entry."""
    try:
        r = await get_redis()
        await r.delete(key)
        return True
    except Exception:
        return False


async def invalidate_user_cache(user_id: str):
    """Wipe all cache entries for a user (call after profile update)."""
    keys = [
        f"state:{user_id}",
        f"profile_analysis:{user_id}",
        f"simulation:{user_id}",
    ]
    for key in keys:
        await delete_cache(key)


# ─── Cache decorators for routes ─────────────────────────────────────────────

async def cached_state_engine(user_id: str, profile: dict, history: list) -> dict:
    """Return cached state or run engine and cache result."""
    from app.ai.engines import StateEngine
    key = f"state:{user_id}"
    cached = await get_cache(key)
    if cached:
        return cached
    result = await StateEngine().evaluate(profile, history)
    await set_cache(key, result, ttl=21600)   # 6 hours
    return result


async def cached_profile_analysis(user_id: str, profile: dict) -> dict:
    """Return cached profile analysis or run engine and cache."""
    from app.ai.engines import UserModelEngine
    key = f"profile_analysis:{user_id}"
    cached = await get_cache(key)
    if cached:
        return cached
    result = await UserModelEngine().analyze(profile)
    await set_cache(key, result, ttl=43200)   # 12 hours
    return result


async def cached_future_simulation(user_id: str) -> Optional[dict]:
    """Return cached simulation if available (does not regenerate — use API for that)."""
    return await get_cache(f"simulation:{user_id}")


async def rate_limit_check(user_id: str, action: str, limit: int, window_seconds: int) -> bool:
    """
    Simple sliding-window rate limiter.
    Returns True if the action is allowed, False if rate-limited.

    Example: limit decision simulations to 10 per hour:
        allowed = await rate_limit_check(user_id, "decision_simulate", 10, 3600)
    """
    try:
        r = await get_redis()
        key = f"ratelimit:{action}:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, window_seconds)
        return count <= limit
    except Exception:
        return True   # fail open — don't block on Redis errors
