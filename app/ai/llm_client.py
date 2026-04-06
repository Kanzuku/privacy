"""
LLM Client — wraps Anthropic and OpenAI with structured JSON output
"""
import json
import re
from typing import Any
import httpx
from app.core.config import settings


async def call_llm(
    user_prompt: str,
    system_prompt: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """
    Call the configured LLM provider.
    Always returns parsed JSON dict.
    Raises ValueError if response cannot be parsed.
    """
    if settings.LLM_PROVIDER == "anthropic":
        return await _call_anthropic(user_prompt, system_prompt, max_tokens, temperature)
    return await _call_openai(user_prompt, system_prompt, max_tokens, temperature)


async def _call_anthropic(user_prompt, system_prompt, max_tokens, temperature) -> dict:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    kwargs = {
        "model": settings.LLM_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    msg = await client.messages.create(**kwargs)
    raw = msg.content[0].text
    return _parse_json(raw)


async def _call_openai(user_prompt, system_prompt, max_tokens, temperature) -> dict:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    resp = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=messages,
    )
    return json.loads(resp.choices[0].message.content)


def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON robustly."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned non-JSON: {e}\nRaw: {raw[:500]}")
