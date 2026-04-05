"""
ME — The Life Game | AI Engine Classes
UserModelEngine, StateEngine, DecisionEngine, GameEngine
"""
from typing import Any
from app.ai.llm_client import call_llm
from app.ai.prompts.prompts import (
    GAME_MASTER_SYSTEM,
    user_model_prompt,
    state_engine_prompt,
    decision_engine_prompt,
    quest_generator_prompt,
    random_event_prompt,
    event_consequence_prompt,
    future_simulation_prompt,
)


class UserModelEngine:
    """Analyzes the user profile and produces structured life intelligence."""

    async def analyze(self, profile: dict) -> dict:
        prompt = user_model_prompt(profile)
        result = await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        return result

    async def get_archetype(self, profile: dict) -> str:
        result = await self.analyze(profile)
        return result.get("archetype", "Unknown")


class StateEngine:
    """Evaluates current life state, buffs/debuffs, and 30-day stat forecast."""

    async def evaluate(self, profile: dict, history: list[dict]) -> dict:
        prompt = state_engine_prompt(profile, history)
        return await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )

    async def get_debuffs(self, profile: dict) -> list[dict]:
        result = await self.evaluate(profile, [])
        return result.get("active_debuffs", [])


class DecisionEngine:
    """Simulates life decisions with multi-scenario analysis and risk scoring."""

    async def simulate(
        self,
        question: str,
        profile: dict,
        context: dict | None = None,
    ) -> dict:
        prompt = decision_engine_prompt(question, profile, context)
        return await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )

    async def get_risk_score(self, question: str, profile: dict) -> int:
        result = await self.simulate(question, profile)
        return result.get("risk_score", 50)


class GameEngine:
    """Generates quests, random events, and simulates event consequences."""

    async def generate_quests(
        self,
        profile: dict,
        game_stats: dict,
        quest_type: str = "daily",
        focus_area: str | None = None,
        count: int = 3,
    ) -> list[dict]:
        prompt = quest_generator_prompt(profile, game_stats, quest_type, focus_area)
        result = await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=3000,
            temperature=0.6,   # higher temp = more creative quests
        )
        quests = result.get("quests", [])
        return quests[:count]

    async def generate_random_event(
        self,
        profile: dict,
        game_stats: dict,
        recent_events: list,
    ) -> dict:
        prompt = random_event_prompt(profile, game_stats, recent_events)
        return await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=1500,
            temperature=0.7,
        )

    async def resolve_event(
        self,
        event: dict,
        chosen_option: str,
        profile: dict,
    ) -> dict:
        prompt = event_consequence_prompt(event, chosen_option, profile)
        return await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=1500,
            temperature=0.3,
        )

    def calculate_level(self, total_xp: int) -> int:
        """XP curve: level = floor(sqrt(total_xp / 100))"""
        import math
        return max(1, int(math.sqrt(total_xp / 100)))

    def xp_for_level(self, level: int) -> int:
        """XP required to reach a given level."""
        return level * level * 100

    def apply_stat_changes(self, current_stats: dict, changes: dict) -> dict:
        """Apply stat deltas and clamp to 0-100."""
        updated = dict(current_stats)
        for stat, delta in changes.items():
            key = f"stat_{stat}" if not stat.startswith("stat_") else stat
            if key in updated:
                updated[key] = max(0, min(100, updated[key] + int(delta)))
        return updated


class FutureSimulationEngine:
    """Generates 10-year dual-path life simulation."""

    async def simulate(
        self,
        profile: dict,
        game_stats: dict,
        goals: list,
    ) -> dict:
        prompt = future_simulation_prompt(profile, game_stats, goals)
        return await call_llm(
            user_prompt=prompt,
            system_prompt=GAME_MASTER_SYSTEM,
            max_tokens=6000,
            temperature=0.2,
        )
