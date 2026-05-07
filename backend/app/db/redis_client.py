import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class UpstashRedisError(RuntimeError):
    pass


class UpstashRedisClient:
    def __init__(self, rest_url: str, rest_token: str, timeout: float = 10.0) -> None:
        if not rest_url:
            raise ValueError("UPSTASH_REDIS_REST_URL is required")
        if not rest_token:
            raise ValueError("UPSTASH_REDIS_REST_TOKEN is required")

        self.rest_url = rest_url.rstrip("/")
        self.rest_token = rest_token
        self._client = httpx.AsyncClient(
            base_url=self.rest_url,
            headers={"Authorization": f"Bearer {self.rest_token}"},
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _command(self, *parts: Any) -> Any:
        response = None
        for attempt in range(3):
            response = await self._client.post("/", json=list(parts))
            if response.status_code not in {401, 403} and response.status_code >= 500 and attempt < 2:
                await asyncio.sleep(0.5)
                continue
            break

        if response is None:
            raise UpstashRedisError("No response from Upstash Redis")

        response.raise_for_status()
        payload = response.json()
        if "error" in payload and payload["error"]:
            raise UpstashRedisError(str(payload["error"]))
        return payload.get("result")

    async def get_json(self, key: str) -> Any | None:
        value = await self._command("GET", key)
        if value is None:
            logger.info("redis MISS %s", key)
            return None

        logger.info("redis HIT %s", key)
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        encoded = json.dumps(value, separators=(",", ":"), sort_keys=True)
        await self._command("SET", key, encoded, "EX", ttl)

    async def set_if_not_exists(self, key: str, value: str, ttl: int) -> bool:
        result = await self._command("SET", key, value, "NX", "EX", ttl)
        return result == "OK"

    async def delete(self, key: str) -> None:
        await self._command("DEL", key)
