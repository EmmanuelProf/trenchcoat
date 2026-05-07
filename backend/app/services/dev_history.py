from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.dossier import DeployerProfile, PriorToken
from app.services.birdeye import BirdeyeClient, BirdeyeError
from app.services.bundle import _block_time, _data, _first_number, _items


SECONDS_IN_DAY = 24 * 60 * 60
STALE_OUTCOME_SECONDS = 7 * SECONDS_IN_DAY


async def evaluate_token_outcome(
    token_ca: str,
    chain: str,
    birdeye: BirdeyeClient,
) -> tuple[str, float | None]:
    try:
        overview = _data(await birdeye.token_overview(token_ca, chain=chain))
    except BirdeyeError:
        return "unknown", None

    if not isinstance(overview, dict):
        return "unknown", None

    price = _first_number(overview.get("price"), overview.get("value"))
    ath = _first_number(
        overview.get("ath"),
        overview.get("athPrice"),
        overview.get("priceAth"),
        overview.get("highestPrice"),
        overview.get("historicalHigh"),
        overview.get("allTimeHigh"),
    )
    liquidity = _first_number(
        overview.get("liquidity"),
        overview.get("liquidityUsd"),
        overview.get("liquidityUSD"),
    )

    age_days = await _token_age_days(token_ca, chain, birdeye)
    last_tx_age_days = await _last_tx_age_days(token_ca, chain, birdeye)
    no_txs_in_7_days = last_tx_age_days is not None and last_tx_age_days > 7

    pct_from_ath = None
    if price is not None and ath is not None and ath > 0:
        pct_from_ath = (price / ath) * 100

    if age_days is not None and age_days < 30:
        return "alive", pct_from_ath

    if pct_from_ath is not None and pct_from_ath >= 50:
        return "alive", pct_from_ath

    if (
        age_days is not None
        and age_days > 7
        and pct_from_ath is not None
        and pct_from_ath < 5
        and (liquidity is None or liquidity < 1000)
    ):
        return "rugged", pct_from_ath

    if (
        age_days is not None
        and age_days > 30
        and pct_from_ath is not None
        and pct_from_ath < 20
        and no_txs_in_7_days
    ):
        return "abandoned", pct_from_ath

    return "unknown", pct_from_ath


async def get_deployer_profile(
    wallet: str,
    chain: str,
    birdeye: BirdeyeClient,
    supabase: Any,
) -> DeployerProfile:
    token_cas = await supabase.get_tokens_by_deployer(wallet, chain)

    prior_tokens: list[PriorToken] = []
    for token_ca in token_cas:
        row = await supabase.get_token_outcome(token_ca, chain)
        if row is None or _is_stale(row.get("last_evaluated_at")):
            outcome, pct_from_ath = await evaluate_token_outcome(token_ca, chain, birdeye)
            row = await supabase.upsert_token_outcome(token_ca, chain, outcome, pct_from_ath)

        prior_tokens.append(
            PriorToken(
                ca=token_ca,
                outcome=(row or {}).get("outcome", "unknown"),
                pct_from_ath=_first_number((row or {}).get("pct_from_ath")),
            )
        )

    rugged_count = sum(1 for token in prior_tokens if token.outcome == "rugged")
    abandoned_count = sum(1 for token in prior_tokens if token.outcome == "abandoned")
    alive_count = sum(1 for token in prior_tokens if token.outcome == "alive")
    unknown_count = sum(1 for token in prior_tokens if token.outcome == "unknown")

    return DeployerProfile(
        wallet=wallet,
        prior_tokens=prior_tokens,
        prior_count=len(prior_tokens),
        rugged_count=rugged_count,
        abandoned_count=abandoned_count,
        alive_count=alive_count,
        unknown_count=unknown_count,
    )


async def _token_age_days(token_ca: str, chain: str, birdeye: BirdeyeClient) -> float | None:
    try:
        txs = _items(await birdeye.token_txs(token_ca, limit=5, sort="asc", chain=chain, offset=0))
    except BirdeyeError:
        return None

    block_times = [_block_time(tx) for tx in txs]
    block_times = [block_time for block_time in block_times if block_time is not None]
    if not block_times:
        return None
    return (datetime.now(timezone.utc).timestamp() - min(block_times)) / SECONDS_IN_DAY


async def _last_tx_age_days(token_ca: str, chain: str, birdeye: BirdeyeClient) -> float | None:
    try:
        txs = _items(await birdeye.token_txs(token_ca, limit=1, sort="desc", chain=chain, offset=0))
    except BirdeyeError:
        return None

    if not txs:
        return None
    block_time = _block_time(txs[0])
    if block_time is None:
        return None
    return (datetime.now(timezone.utc).timestamp() - block_time) / SECONDS_IN_DAY


def _is_stale(value: Any) -> bool:
    if not value:
        return True
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif isinstance(value, datetime):
        parsed = value
    else:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age_seconds = datetime.now(timezone.utc).timestamp() - parsed.timestamp()
    return age_seconds > STALE_OUTCOME_SECONDS
