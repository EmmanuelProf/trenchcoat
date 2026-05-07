import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.dossier import router as dossier_router
from app.db.redis_client import UpstashRedisClient
from app.db.supabase import SupabaseClient
from app.services.birdeye import BirdeyeClient


load_dotenv()


def _allowed_origins() -> list[str]:
    origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,https://trenchcoat.vercel.app",
    )
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = UpstashRedisClient(
        os.getenv("UPSTASH_REDIS_REST_URL", ""),
        os.getenv("UPSTASH_REDIS_REST_TOKEN", ""),
    )
    birdeye = BirdeyeClient(os.getenv("BIRDEYE_API_KEY", ""), redis)
    supabase = SupabaseClient(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )

    app.state.redis = redis
    app.state.birdeye = birdeye
    app.state.supabase = supabase
    try:
        yield
    finally:
        await birdeye.close()
        await redis.close()
        await supabase.close()


app = FastAPI(title="TRENCHCOAT API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(dossier_router)


@app.get("/health")
async def health() -> dict[str, bool | str]:
    return {"ok": True, "service": "trenchcoat-api"}
