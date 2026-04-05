"""
ME — The Life Game | Modular AI Prompt System
All prompts are structured, data-driven, and output valid JSON.
"""

from typing import Any


# ============================================================
# SYSTEM PROMPT  (base Game Master persona)
# ============================================================
GAME_MASTER_SYSTEM = """
You are the Game Master (GM) of "ME — The Life Game" — an AI-powered life simulation system.

Your role:
- Analyze real user data (age, income, habits, goals, personality) with precision
- Generate actionable, measurable, non-generic output
- Always output valid JSON matching the schema requested
- Never produce motivational fluff or generic advice
- Use numbers, probabilities, and realistic ranges
- Think step-by-step internally before finalizing output
- Treat the user's life as a complex system, not a self-help exercise

Rules:
- Avoid generic statements like "exercise more" or "save money"
- Be specific: "Walk 8,000 steps/day for 21 days straight" not "be active"
- All probability estimates must be realistic (avoid 95%+ for life outcomes)
- Financial projections must account for taxes, inflation (3% baseline)
- Stress scores are real — acknowledge when a path is genuinely hard
"""


# ============================================================
# MODULE 1 — USER MODEL ANALYSIS
# ============================================================
def user_model_prompt(profile: dict) -> str:
    return f"""
Analyze this user profile and return structured JSON.

USER DATA:
{profile}

Return ONLY this JSON (no markdown, no preamble):
{{
  "life_stage": "<emerging_adult|establishing|peak_building|transitioning|consolidating>",
  "stage_description": "<2 sentences specific to this user, not generic>",
  "archetype": "<The Drifter|The Builder|The Optimizer|The Burned-Out|The Climber|...>",
  "archetype_description": "<why this user matches this archetype based on their data>",
  "main_problems": [
    {{"problem": "...", "severity": 1-10, "evidence": "based on [specific data point]", "impact_area": "career|finance|health|social"}}
  ],
  "hidden_risks": [
    {{"risk": "...", "probability_12mo": "0.0-1.0", "trigger": "...", "consequence": "..."}}
  ],
  "growth_opportunities": [
    {{"opportunity": "...", "effort_level": 1-10, "payoff_timeline": "...", "stat_impact": {{"stat": "value_change"}}}}
  ],
  "key_insight": "<the single most important non-obvious insight about this user's situation>"
}}
"""


# ============================================================
# MODULE 2 — STATE ENGINE
# ============================================================
def state_engine_prompt(profile: dict, history: list[dict]) -> str:
    return f"""
Evaluate the user's current life state and generate a comprehensive state report.

USER PROFILE:
{profile}

RECENT HISTORY (last 30 days):
{history}

Return ONLY this JSON:
{{
  "overall_trajectory": "<ascending|stable|declining|volatile>",
  "momentum_score": 0-100,
  "momentum_description": "<specific reason based on their data>",
  "active_buffs": [
    {{"name": "...", "effect": "...", "expires": "<timeframe>"}}
  ],
  "active_debuffs": [
    {{"name": "...", "effect": "...", "severity": 1-10, "source": "..."}}
  ],
  "critical_alerts": [
    {{"alert": "...", "urgency": "immediate|this_week|this_month", "action": "..."}}
  ],
  "stat_forecast_30d": {{
    "health": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "energy": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "wealth": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "knowledge": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "happiness": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "discipline": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "career": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}},
    "social": {{"current": 0-100, "projected": 0-100, "delta": -100 to 100}}
  }}
}}
"""


# ============================================================
# MODULE 3 — DECISION ENGINE
# ============================================================
def decision_engine_prompt(question: str, profile: dict, context: dict | None = None) -> str:
    return f"""
Simulate this life decision for a specific user. Generate realistic, data-grounded scenarios.

DECISION: {question}

USER PROFILE:
{profile}

ADDITIONAL CONTEXT:
{context or "None provided"}

Return ONLY this JSON:
{{
  "decision_category": "career|financial|relationship|health|lifestyle|relocation",
  "scenarios": [
    {{
      "id": "optimistic",
      "label": "Best case (realistic)",
      "probability": 0.0-1.0,
      "description": "<2-3 sentences, specific to this user>",
      "financial_impact_monthly": 0.0,
      "financial_impact_12mo": 0.0,
      "stress_level": 1-10,
      "career_impact": "<specific description>",
      "lifestyle_impact": "<specific description>",
      "stat_changes": {{"stat_name": delta_int}},
      "timeline": "<when outcomes materialize>",
      "key_dependencies": ["<what must go right>"]
    }},
    {{
      "id": "realistic",
      "label": "Most likely outcome",
      ...
    }},
    {{
      "id": "pessimistic",
      "label": "Worst case (realistic)",
      ...
    }},
    {{
      "id": "high_risk_reward",
      "label": "High risk / high reward",
      ...
    }}
  ],
  "risk_score": 0-100,
  "risk_factors": [
    {{"factor": "...", "weight": 0.0-1.0, "mitigable": true|false, "mitigation": "..."}}
  ],
  "recommendation": "yes|no|conditional",
  "recommendation_rationale": "<data-driven reasoning, 3-4 sentences>",
  "conditional_triggers": ["<if X, then proceed>"],
  "questions_to_answer_first": ["<specific due diligence items>"],
  "comparable_outcomes": "<reference to similar real-world patterns with rough statistics>"
}}
"""


# ============================================================
# MODULE 4 — QUEST GENERATOR
# ============================================================
def quest_generator_prompt(
    profile: dict,
    game_stats: dict,
    quest_type: str,  # daily | weekly | main | skill
    focus_area: str | None = None,
) -> str:
    return f"""
Generate {quest_type} quests for this user. Quests must be specific, measurable, and directly tied to their real life data.

USER PROFILE: {profile}
CURRENT GAME STATS: {game_stats}
FOCUS AREA: {focus_area or "auto-detect based on lowest stats and urgent needs"}

Rules:
- Daily quests: completable in 15-60 min
- Weekly quests: require 3-7 days of consistent action
- Main quests: 2-8 week arcs aligned with goals
- Skill quests: directly level up a specific user skill
- All quests must include exact measurable criteria (not "exercise more" but "complete 3 sets of 15 pushups")
- XP rewards scale with difficulty and time investment
- Stat rewards must be realistic (not +20 health for drinking water once)

Return ONLY this JSON:
{{
  "quests": [
    {{
      "type": "{quest_type}",
      "title": "...",
      "description": "<compelling 1-2 sentence description>",
      "why_now": "<why this quest matters for this specific user right now>",
      "action_steps": [
        {{"step": 1, "action": "<exact measurable action>", "duration": "...", "done": false}}
      ],
      "success_criteria": "<how to know it's truly complete>",
      "xp_reward": int,
      "stat_rewards": {{"stat_name": delta_int}},
      "buff_rewards": [{{"name": "...", "effect": "...", "duration_hours": int}}],
      "failure_consequence": {{"stat_changes": {{}}, "description": "..."}},
      "difficulty": 1-10,
      "category": "health|career|finance|social|knowledge|discipline"
    }}
  ]
}}
"""


# ============================================================
# MODULE 5 — RANDOM EVENT GENERATOR
# ============================================================
def random_event_prompt(profile: dict, game_stats: dict, recent_events: list) -> str:
    return f"""
Generate a realistic, unexpected life event for this user. Events must feel plausible given their situation.

USER PROFILE: {profile}
GAME STATS: {game_stats}
RECENT EVENTS (avoid repetition): {recent_events}

Return ONLY this JSON:
{{
  "title": "<event headline>",
  "description": "<2-3 sentence narrative, immersive>",
  "category": "job|financial|social|health|relocation|opportunity|risk",
  "urgency": "immediate|this_week|flexible",
  "options": [
    {{
      "id": "option_a",
      "label": "<short label>",
      "description": "<what this choice means>",
      "consequence_preview": "<hint at outcome without full reveal>",
      "risk_level": 1-10
    }},
    {{
      "id": "option_b",
      ...
    }},
    {{
      "id": "option_c",
      "label": "Ignore / Do nothing",
      ...
    }}
  ],
  "expires_hours": int
}}
"""


# ============================================================
# MODULE 6 — EVENT CONSEQUENCE SIMULATOR
# ============================================================
def event_consequence_prompt(event: dict, chosen_option: str, profile: dict) -> str:
    return f"""
Simulate the realistic consequence of this life event choice.

EVENT: {event}
USER CHOSE: {chosen_option}
USER PROFILE: {profile}

Return ONLY this JSON:
{{
  "immediate_outcome": "<what happens in the next 24-72 hours>",
  "short_term_outcome": "<1-4 weeks>",
  "long_term_impact": "<3-6 months view>",
  "stat_changes": {{"stat_name": delta_int}},
  "xp_gained": int,
  "new_opportunities_unlocked": ["<opportunity>"],
  "new_risks_created": ["<risk>"],
  "narrative": "<2-3 sentence story of what unfolds>",
  "lesson": "<non-preachy single insight from this outcome>"
}}
"""


# ============================================================
# MODULE 7 — FUTURE SIMULATION
# ============================================================
def future_simulation_prompt(profile: dict, game_stats: dict, goals: list) -> str:
    return f"""
Simulate two life trajectories for this user over 10 years.

USER PROFILE: {profile}
CURRENT STATS: {game_stats}
GOALS: {goals}

TRAJECTORY A: "If nothing changes" — user continues current habits exactly
TRAJECTORY B: "If they follow the plan" — user executes their top 3 goals with 70% consistency

For each year, estimate realistic values. Account for compound effects (skills, income growth, health depreciation).

Return ONLY this JSON:
{{
  "baseline_path": {{
    "label": "If nothing changes",
    "summary": "<2-sentence brutal honest projection>",
    "yearly": [
      {{
        "year": 1,
        "age": int,
        "income_monthly": float,
        "savings_total": float,
        "health_score": 0-100,
        "happiness_score": 0-100,
        "career_level": "<specific title or stage>",
        "key_event": "<likely life event>",
        "stat_snapshot": {{...}}
      }}
    ],
    "year_10_summary": "..."
  }},
  "optimized_path": {{
    "label": "If you follow the plan",
    "summary": "<2-sentence ambitious but realistic projection>",
    "yearly": [...],
    "year_10_summary": "..."
  }},
  "delta_at_year_10": {{
    "income_difference_monthly": float,
    "savings_difference": float,
    "health_difference": int,
    "happiness_difference": int,
    "summary": "<stark comparison in plain English>"
  }}
}}
"""
