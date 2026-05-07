import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from app.db.redis_client import UpstashRedisClient
from app.services.birdeye import BirdeyeClient
from app.services.bundle import (
    _fetch_transactions,
    _supply,
    analyze_transactions,
    detect_bundle,
    get_deployer_from_txs,
)


BONK_CA = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


def _items(response):
    data = response.get("data", response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "tokens"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

    redis = UpstashRedisClient(
        rest_url=os.environ["UPSTASH_REDIS_REST_URL"],
        rest_token=os.environ["UPSTASH_REDIS_REST_TOKEN"],
    )
    birdeye = BirdeyeClient(
        api_key=os.environ["BIRDEYE_API_KEY"],
        redis_client=redis,
    )

    try:
        print("$BONK")
        bonk_result = await detect_bundle(BONK_CA, "solana", birdeye)
        print(bonk_result.model_dump() if bonk_result else None)

        listings = _items(await birdeye.new_listings(chain="solana", limit=20))
        if not listings:
            raise RuntimeError("No new listings returned")

        latest = listings[0]
        latest_ca = latest.get("address") or latest.get("tokenAddress") or latest.get("mint")
        if not latest_ca:
            raise RuntimeError(f"Could not find latest token address in listing: {latest}")

        symbol = latest.get("symbol") or latest.get("name") or "latest"
        print(f"${symbol} latest listing ({latest_ca})")
        raw_transactions = await _fetch_transactions(latest_ca, "solana", birdeye)
        print("first_10_raw_transactions=")
        print(json.dumps(raw_transactions[:10], indent=2, sort_keys=True))

        overview = await birdeye.token_overview(latest_ca, chain="solana")
        _, debug = analyze_transactions(latest_ca, raw_transactions, _supply(overview))
        print(f"launch_window_start={debug['launch_window_start']}")
        print(f"launch_window_end={debug['launch_window_end']}")
        print(f"launch_buy_count={debug['launch_buy_count']}")
        print(f"top_buyers={debug['top_buyers']}")

        latest_result = await detect_bundle(latest_ca, "solana", birdeye)
        print(latest_result.model_dump() if latest_result else None)
        deployer = await get_deployer_from_txs(latest_ca, "solana", birdeye)
        print(f"derived_deployer={deployer}")
    finally:
        await birdeye.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
