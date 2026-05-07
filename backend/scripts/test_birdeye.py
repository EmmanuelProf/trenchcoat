import asyncio
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


BONK_CA = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

    required_env = [
        "BIRDEYE_API_KEY",
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
    ]
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    redis = UpstashRedisClient(
        rest_url=os.environ["UPSTASH_REDIS_REST_URL"],
        rest_token=os.environ["UPSTASH_REDIS_REST_TOKEN"],
    )
    birdeye = BirdeyeClient(
        api_key=os.environ["BIRDEYE_API_KEY"],
        redis_client=redis,
    )

    cache_key = birdeye._cache_key("token_overview", "solana", BONK_CA)
    await redis.delete(cache_key)

    try:
        first = await birdeye.token_overview(BONK_CA, chain="solana")
        symbol = first.get("data", {}).get("symbol")
        assert symbol == "Bonk", f'expected data.symbol == "Bonk", got {symbol!r}'

        external_calls_after_first = birdeye.external_call_count
        second = await birdeye.token_overview(BONK_CA, chain="solana")
        assert second == first, "cached response differed from first response"
        assert birdeye.external_call_count == external_calls_after_first, (
            "second token_overview call did not hit cache"
        )
        assert birdeye.cache_hit_count >= 1, "cache hit counter did not increment"

        print(f"first_call_external_calls={external_calls_after_first}")
        print(f"second_call_external_calls={birdeye.external_call_count}")
        print(f"cache_hits={birdeye.cache_hit_count}")
        print("✅ SPEC-001 passes")
    finally:
        await birdeye.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
