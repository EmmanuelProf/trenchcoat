from __future__ import annotations

import asyncio
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from app.db.redis_client import UpstashRedisClient
from app.db.supabase import SupabaseClient
from app.services.birdeye import BirdeyeClient, BirdeyeError
from app.services.bundle import _items, get_deployer_from_txs
from app.services.dev_history import get_deployer_profile


logger = logging.getLogger(__name__)

CHAIN = "solana"
PAGE_LIMIT = 20
SECONDS_IN_30_DAYS = 30 * 24 * 60 * 60
CONCURRENCY = 5
DEFAULT_MAX_TOKENS = 200


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    redis = UpstashRedisClient(
        os.getenv("UPSTASH_REDIS_REST_URL", ""),
        os.getenv("UPSTASH_REDIS_REST_TOKEN", ""),
    )
    birdeye = BirdeyeClient(os.getenv("BIRDEYE_API_KEY", ""), redis, default_chain=CHAIN)
    supabase = SupabaseClient(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )

    try:
        before_count = await supabase.count_deployer_history(CHAIN)
        _emit(f"deployer_history rows before={before_count}")

        processed = 0
        with_deployer = 0
        seen_tokens: set[str] = set()
        cutoff = int(datetime.now(timezone.utc).timestamp()) - SECONDS_IN_30_DAYS
        time_to = int(datetime.now(timezone.utc).timestamp())
        max_tokens = int(os.getenv("BOOTSTRAP_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
        _emit(f"bootstrap_max_tokens={max_tokens}")

        while time_to > cutoff and processed < max_tokens:
            page = await _fetch_new_listing_page(birdeye, time_to)
            tokens = _items(page)
            if not tokens:
                break

            oldest_seen = time_to
            work_items: list[tuple[str, int | None]] = []
            for token in tokens:
                token_ca = _token_address(token)
                deployed_at_unix = _listing_time(token)
                if deployed_at_unix is not None:
                    oldest_seen = min(oldest_seen, deployed_at_unix)

                if not token_ca or token_ca in seen_tokens:
                    continue
                if deployed_at_unix is not None and deployed_at_unix < cutoff:
                    continue
                if processed + len(work_items) >= max_tokens:
                    break

                seen_tokens.add(token_ca)
                work_items.append((token_ca, deployed_at_unix))

            results = await _process_page(work_items, birdeye, supabase)
            processed += len(work_items)
            with_deployer += results

            _emit(f"processed={processed} deployers_found={with_deployer} time_to={time_to}")

            next_time_to = oldest_seen - 1
            if next_time_to >= time_to:
                break
            time_to = next_time_to

        after_count = await supabase.count_deployer_history(CHAIN)
        inserted = after_count - before_count
        _emit(f"processed_tokens={processed}")
        _emit(f"rows_with_deployer_seen_this_run={with_deployer}")
        _emit(f"deployer_history rows after={after_count}")
        _emit(f"deployer_history rows inserted={inserted}")

        wallet = await _wallet_with_multiple_tokens(supabase)
        if wallet is None:
            _emit("no deployer wallet with 2+ tokens found in sampled deployer_history rows")
            return

        _emit(f"profile_wallet={wallet}")
        profile = await get_deployer_profile(wallet, CHAIN, birdeye, supabase)
        _emit(str(profile.model_dump()))
    finally:
        await birdeye.close()
        await redis.close()
        await supabase.close()


async def _fetch_new_listing_page(birdeye: BirdeyeClient, time_to: int) -> dict[str, Any]:
    try:
        return await birdeye._get(
            "/defi/v2/tokens/new_listing",
            {
                "time_to": time_to,
                "limit": PAGE_LIMIT,
                "meme_platform_enabled": "true",
            },
            CHAIN,
            "new_listings",
            "global",
        )
    except BirdeyeError as exc:
        logger.warning("new listing fetch failed time_to=%s error=%s", time_to, exc)
        return {}


async def _process_page(
    work_items: list[tuple[str, int | None]],
    birdeye: BirdeyeClient,
    supabase: SupabaseClient,
) -> int:
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def process_one(token_ca: str, deployed_at_unix: int | None) -> bool:
        async with semaphore:
            deployer = await get_deployer_from_txs(token_ca, CHAIN, birdeye)
            if deployer is None:
                return False

            deployed_at = _iso_from_unix(deployed_at_unix) if deployed_at_unix else _now_iso()
            await supabase.upsert_deployer_record(deployer, token_ca, CHAIN, deployed_at)
            return True

    results = await asyncio.gather(
        *(process_one(token_ca, deployed_at_unix) for token_ca, deployed_at_unix in work_items),
        return_exceptions=True,
    )
    for result in results:
        if isinstance(result, Exception):
            logger.warning("token bootstrap failed: %s", result)
    return sum(1 for result in results if result is True)


def _emit(message: str) -> None:
    print(message, flush=True)


def _token_address(token: dict[str, Any]) -> str | None:
    for key in ("address", "tokenAddress", "mint", "ca"):
        value = token.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _listing_time(token: dict[str, Any]) -> int | None:
    for key in ("liquidityAddedAt", "createdAt", "listingTime", "blockUnixTime"):
        parsed = _to_unix(token.get(key))
        if parsed is not None:
            return parsed
    return None


def _to_unix(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        parsed = int(value)
        if parsed > 10_000_000_000:
            parsed //= 1000
        return parsed
    if isinstance(value, str):
        if value.isdigit():
            return _to_unix(int(value))
        try:
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
        except ValueError:
            return None
    return None


def _iso_from_unix(value: int) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _wallet_with_multiple_tokens(supabase: SupabaseClient) -> str | None:
    rows = await supabase.get_deployer_history_rows(CHAIN, limit=5000)
    counts = Counter(row.get("deployer_wallet") for row in rows if row.get("deployer_wallet"))
    for wallet, count in counts.most_common():
        if count >= 2:
            return wallet
    return None


if __name__ == "__main__":
    asyncio.run(main())
