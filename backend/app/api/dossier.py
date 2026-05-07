from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.models.dossier import (
    DeployerProfile,
    Dossier,
    SupplyDistribution,
    TokenOverview,
    TokenSecurity,
)
from app.services.bundle import detect_bundle, get_deployer_from_txs
from app.services.dev_history import get_deployer_profile
from app.services.scorer import score_dossier
from app.services.verdict import generate_verdict


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dossier", tags=["dossier"])

BASE58_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


@router.get("/{ca}", response_model=Dossier)
async def get_dossier(ca: str, request: Request, chain: str = "solana") -> Dossier | dict[str, Any]:
    chain = chain.lower()
    if not _valid_ca(ca, chain):
        raise HTTPException(status_code=422, detail="Invalid contract address")

    redis = request.app.state.redis
    birdeye = request.app.state.birdeye
    supabase = request.app.state.supabase

    cache_key = f"dossier:{chain}:{ca}"
    cached = await redis.get_json(cache_key)
    if cached is not None:
        return cached

    overview_result, security_result, holders_result, bundle_result = await asyncio.gather(
        _section("overview", birdeye.token_overview(ca, chain=chain)),
        _section("security", birdeye.token_security(ca, chain=chain)),
        _section("holders", birdeye.token_holders(ca, limit=20, chain=chain)),
        _section("bundle", detect_bundle(ca, chain, birdeye)),
    )

    logger.warning("raw token_security response=%s", security_result)

    overview = _overview_model(overview_result, bundle_result)
    security = _security_model(security_result)
    distribution = _distribution_model(security, holders_result, bundle_result)

    deployer = await _deployer_profile(ca, chain, birdeye, supabase)
    score, band = score_dossier(security, distribution, deployer, overview)

    raw_signals = _raw_signals(
        ca=ca,
        chain=chain,
        overview=overview,
        security=security,
        deployer=deployer,
        distribution=distribution,
    )
    verdict = await generate_verdict(raw_signals, score, band, redis_client=redis)

    dossier = Dossier(
        ca=ca,
        chain=chain,
        generated_at=datetime.now(timezone.utc),
        score=score,
        band=band,
        overview=overview,
        security=security,
        deployer=deployer,
        distribution=distribution,
        verdict=verdict,
        raw_signals=raw_signals,
    )
    payload = dossier.model_dump(mode="json")
    await redis.set_json(cache_key, payload, ttl=300)
    return dossier


async def _section(name: str, awaitable: Any) -> Any | None:
    try:
        return await awaitable
    except Exception as exc:
        logger.warning("dossier section failed name=%s error=%s", name, exc)
        return None


async def _deployer_profile(ca: str, chain: str, birdeye: Any, supabase: Any) -> DeployerProfile:
    wallet = await _section("deployer", get_deployer_from_txs(ca, chain, birdeye))
    if not wallet:
        return DeployerProfile(wallet="unknown")
    profile = await _section("deployer_profile", get_deployer_profile(wallet, chain, birdeye, supabase))
    return profile or DeployerProfile(wallet=wallet)


def _valid_ca(ca: str, chain: str) -> bool:
    if chain == "solana":
        return not ca.startswith("0x") and bool(BASE58_RE.fullmatch(ca))
    if chain in {"ethereum", "arbitrum", "avalanche", "bsc", "optimism", "polygon", "base", "zksync"}:
        return bool(EVM_RE.fullmatch(ca))
    return bool(BASE58_RE.fullmatch(ca) or EVM_RE.fullmatch(ca))


def _overview_model(response: dict[str, Any] | None, bundle: Any | None = None) -> TokenOverview | None:
    data = _data(response)
    if not isinstance(data, dict):
        return None
    age_days = _age_days_from_overview(data)
    if age_days is None and bundle is not None and bundle.earliest_block is not None:
        age_days = _age_days_from_unix(bundle.earliest_block)
    return TokenOverview(
        symbol=_str(data.get("symbol")),
        name=_str(data.get("name")),
        price=_number(data.get("price"), data.get("value")),
        mc=_number(data.get("mc"), data.get("marketCap"), data.get("marketcap")),
        liquidity=_number(data.get("liquidity"), data.get("liquidityUsd"), data.get("liquidityUSD")),
        supply=_number(data.get("supply"), data.get("circulatingSupply"), data.get("totalSupply")),
        age_days=age_days,
    )


def _security_model(response: dict[str, Any] | None) -> TokenSecurity | None:
    data = _data(response)
    if not isinstance(data, dict):
        return TokenSecurity()

    mint_authority = data.get("mintAuthority")
    freeze_authority = data.get("freezeAuthority")
    return TokenSecurity(
        mint_revoked=_revoked(mint_authority, data.get("mint_revoked")),
        freeze_revoked=_revoked(freeze_authority, data.get("freeze_revoked")),
        top10_pct=_pct(
            data.get("top10HolderPercent"),
            data.get("top10HolderPercentage"),
            data.get("top10_pct"),
        ),
        mutable_metadata=_bool(data.get("mutableMetadata"), data.get("mutable_metadata")),
        transfer_fee_enabled=_bool(data.get("transferFeeEnable"), data.get("transfer_fee_enabled")),
    )


def _distribution_model(
    security: TokenSecurity | None,
    holders_response: dict[str, Any] | None,
    bundle: Any | None,
) -> SupplyDistribution:
    holders = _items(holders_response)
    suspect_wallets = [_owner(holder) for holder in holders[:10]]
    suspect_wallets = [wallet for wallet in suspect_wallets if wallet]
    return SupplyDistribution(
        bundle_pct=bundle.bundle_pct if bundle is not None else None,
        top10_pct=security.top10_pct if security is not None else None,
        suspect_wallets=suspect_wallets,
        bundle=bundle,
    )


def _raw_signals(
    ca: str,
    chain: str,
    overview: TokenOverview | None,
    security: TokenSecurity | None,
    deployer: DeployerProfile | None,
    distribution: SupplyDistribution | None,
) -> dict[str, Any]:
    bundle = distribution.bundle if distribution is not None else None
    return {
        "ca": ca,
        "chain": chain,
        "symbol": overview.symbol if overview is not None else None,
        "mint_revoked": security.mint_revoked if security is not None else None,
        "freeze_revoked": security.freeze_revoked if security is not None else None,
        "top10_pct": security.top10_pct if security is not None else None,
        "bundled": bundle.bundled if bundle is not None else False,
        "bundle_pct": bundle.bundle_pct if bundle is not None else 0,
        "prior_count": deployer.prior_count if deployer is not None else 0,
        "rugged_count": deployer.rugged_count if deployer is not None else 0,
        "abandoned_count": deployer.abandoned_count if deployer is not None else 0,
        "liquidity": overview.liquidity if overview is not None else None,
        "age_days": overview.age_days if overview is not None else None,
    }


def _data(response: dict[str, Any] | None) -> Any:
    if not isinstance(response, dict):
        return None
    return response.get("data", response)


def _items(response: dict[str, Any] | None) -> list[dict[str, Any]]:
    data = _data(response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "holders", "tokens"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _number(*values: Any) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _pct(*values: Any) -> float | None:
    value = _number(*values)
    if value is None:
        return None
    if 0 <= value <= 1:
        return value * 100
    return value


def _bool(*values: Any) -> bool | None:
    for value in values:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
    return None


def _revoked(authority: Any, explicit: Any = None) -> bool | None:
    parsed = _bool(explicit)
    if parsed is not None:
        return parsed
    if authority is None:
        return True
    if isinstance(authority, str):
        return authority.strip() == ""
    return False


def _owner(holder: dict[str, Any]) -> str | None:
    for key in ("owner", "wallet", "address"):
        value = holder.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _age_days_from_overview(data: dict[str, Any]) -> float | None:
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        extensions = {}

    created_at = _timestamp(
        data.get("createdTime"),
        data.get("creationTime"),
        data.get("createdAt"),
        data.get("created_at"),
        data.get("launchTime"),
        extensions.get("createdTime"),
        extensions.get("creationTime"),
        extensions.get("createdAt"),
        extensions.get("created_at"),
        extensions.get("launchTime"),
    )
    if created_at is None:
        return None
    return _age_days_from_unix(created_at)


def _timestamp(*values: Any) -> int | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            parsed = int(value)
            if parsed > 10_000_000_000:
                parsed //= 1000
            return parsed
        if isinstance(value, str):
            if value.isdigit():
                return _timestamp(int(value))
            try:
                return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
            except ValueError:
                continue
    return None


def _age_days_from_unix(timestamp: int) -> float:
    now = datetime.now(timezone.utc).timestamp()
    return max(0, round((now - timestamp) / 86_400, 2))
