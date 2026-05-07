from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "anthropic/claude-haiku-4-5"
VERDICT_TTL_SECONDS = 300

SYSTEM_PROMPT = """You are TRENCHCOAT, a no-bullshit on-chain detective. You write verdicts on tokens for degens about to ape. Your style: noir, terse, specific. Numbers over adjectives. Never use words like "leverage," "ecosystem," "robust," "synergy," "consider." Never disclaim. Never moralize. Just call what you see.

You write 1-2 sentences max. Each sentence is short. The reader has 3 seconds.

Examples of good verdicts:
- "Same wallet shipped three tokens. All three zeros. This makes four."
- "72% of supply in ten wallets. Mint not revoked. You know the rest."  
- "Clean deployer. Locked liquidity. Even distribution. Rare. Could actually be real."
- "Bundled launch — top 10 buyers in the same block grabbed 38%. Skip."

Bad examples (never write like this):
- "This token shows several concerning risk indicators..."
- "Our analysis suggests caution is warranted..."
- "Multiple metrics indicate elevated risk..."

Output the verdict only. No preamble, no quotes, no labels."""


async def generate_verdict(
    signals: dict[str, Any],
    score: int,
    band: str,
    redis_client: Any | None = None,
    api_key: str | None = None,
) -> str:
    cache_key = _cache_key(signals, score, band)
    if redis_client is not None:
        cached = await redis_client.get_json(cache_key)
        if isinstance(cached, str):
            return cached

    verdict = await _generate_with_openrouter(signals, score, band, api_key)
    if len(verdict) > 200:
        verdict = await _generate_with_openrouter(signals, score, band, api_key)
    if len(verdict) > 200:
        verdict = verdict[:200]

    if redis_client is not None:
        await redis_client.set_json(cache_key, verdict, ttl=VERDICT_TTL_SECONDS)
    return verdict


async def _generate_with_openrouter(
    signals: dict[str, Any],
    score: int,
    band: str,
    api_key: str | None,
) -> str:
    resolved_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
    if not resolved_key or resolved_key.startswith("your_"):
        return _fallback_verdict(score, band)

    payload = {
        "model": OPENROUTER_MODEL,
        "max_tokens": 100,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(signals, score, band)},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {resolved_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://trenchcoat.vercel.app",
                    "X-Title": "TRENCHCOAT",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return _fallback_verdict(score, band)

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    verdict = _clean_verdict(content)
    return verdict or _fallback_verdict(score, band)


def _user_prompt(signals: dict[str, Any], score: int, band: str) -> str:
    symbol = signals.get("symbol") or "UNKNOWN"
    ca = signals.get("ca") or signals.get("token_ca") or "unknown"
    mint_revoked = signals.get("mint_revoked")
    freeze_revoked = signals.get("freeze_revoked")
    top10_pct = signals.get("top10_pct")
    bundled = signals.get("bundled")
    bundle_pct = signals.get("bundle_pct")
    prior_count = signals.get("prior_count")
    rugged_count = signals.get("rugged_count")
    abandoned_count = signals.get("abandoned_count")
    liquidity = signals.get("liquidity")
    age_days = signals.get("age_days")

    return f"""Token: {symbol} ({ca})
Score: {score}/100 — {band}

Signals:
- Mint authority revoked: {mint_revoked}
- Freeze authority revoked: {freeze_revoked}
- Top 10 holders %: {top10_pct}
- Bundled launch: {bundled} (top-10 launch buyers hold {bundle_pct}%)
- Deployer prior tokens: {prior_count} (rugged: {rugged_count}, abandoned: {abandoned_count})
- Liquidity: ${liquidity}
- Age: {age_days} days

Write the verdict."""


def _fallback_verdict(score: int, band: str) -> str:
    if band == "AVOID":
        return f"Multiple red flags. Score: {score}/100. Don't."
    if band == "CAUTION":
        return f"Mixed signals. Score: {score}/100. Size small if at all."
    if band == "CLEAR":
        return f"No major red flags found. Score: {score}/100. Still memecoin — DYOR."
    return f"Insufficient signal. Score: {score}/100."


def _clean_verdict(value: str) -> str:
    verdict = value.strip()
    verdict = re.sub(r"^```(?:text)?", "", verdict).strip()
    verdict = re.sub(r"```$", "", verdict).strip()
    verdict = verdict.strip("\"'“”‘’")
    return verdict


def _cache_key(signals: dict[str, Any], score: int, band: str) -> str:
    encoded = json.dumps(
        signals,
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"verdict:{digest}"
