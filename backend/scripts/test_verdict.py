import asyncio
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
from app.services.verdict import generate_verdict


CASES = [
    (
        "Clean",
        {
            "symbol": "BONK",
            "ca": "BONK",
            "mint_revoked": True,
            "freeze_revoked": True,
            "top10_pct": 28,
            "bundled": False,
            "bundle_pct": 0,
            "prior_count": 0,
            "rugged_count": 0,
            "abandoned_count": 0,
            "liquidity": 75000,
            "age_days": 12,
        },
        85,
        "CLEAR",
    ),
    (
        "Serial rugger",
        {
            "symbol": "SCAM",
            "ca": "SCAM",
            "mint_revoked": False,
            "freeze_revoked": False,
            "top10_pct": 78,
            "bundled": True,
            "bundle_pct": 38,
            "prior_count": 4,
            "rugged_count": 4,
            "abandoned_count": 0,
            "liquidity": 3200,
            "age_days": 2,
        },
        12,
        "AVOID",
    ),
    (
        "Bundled launch",
        {
            "symbol": "PUMP",
            "ca": "PUMP",
            "mint_revoked": True,
            "freeze_revoked": True,
            "top10_pct": 65,
            "bundled": True,
            "bundle_pct": 41,
            "prior_count": 0,
            "rugged_count": 0,
            "abandoned_count": 0,
            "liquidity": 18000,
            "age_days": 1,
        },
        22,
        "AVOID",
    ),
    (
        "Borderline",
        {
            "symbol": "MEH",
            "ca": "MEH",
            "mint_revoked": True,
            "freeze_revoked": False,
            "top10_pct": 52,
            "bundled": False,
            "bundle_pct": 0,
            "prior_count": 1,
            "rugged_count": 0,
            "abandoned_count": 1,
            "liquidity": 22000,
            "age_days": 8,
        },
        45,
        "CAUTION",
    ),
    (
        "Missing data",
        {
            "symbol": "UNKNOWN",
            "ca": "UNKNOWN",
            "mint_revoked": None,
            "freeze_revoked": None,
            "top10_pct": None,
            "bundled": False,
            "bundle_pct": 0,
            "prior_count": 0,
            "rugged_count": 0,
            "abandoned_count": 0,
            "liquidity": None,
            "age_days": None,
        },
        50,
        "CAUTION",
    ),
]


async def main() -> None:
    redis = UpstashRedisClient(
        os.getenv("UPSTASH_REDIS_REST_URL", ""),
        os.getenv("UPSTASH_REDIS_REST_TOKEN", ""),
    )
    try:
        for label, signals, score, band in CASES:
            verdict = await generate_verdict(signals, score, band, redis_client=redis)
            print(f"{label}: {verdict}")
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
