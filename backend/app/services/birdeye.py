import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BirdeyeError(RuntimeError):
    pass


class BirdeyeNotFoundError(BirdeyeError):
    pass


class BirdeyeBadRequestError(BirdeyeError):
    pass


class BirdeyeRateLimitError(BirdeyeError):
    pass


class BirdeyeServerError(BirdeyeError):
    pass


class BirdeyeClient:
    BASE_URL = "https://public-api.birdeye.so"

    def __init__(
        self,
        api_key: str,
        redis_client,
        default_chain: str = "solana",
        timeout: float = 10.0,
    ) -> None:
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY is required")

        self.api_key = api_key
        self.redis = redis_client
        self.default_chain = default_chain
        self.external_call_count = 0
        self.cache_hit_count = 0
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    def _cache_key(self, endpoint_slug: str, chain: str, address: str) -> str:
        return f"birdeye:{endpoint_slug}:{chain}:{address}"

    async def _cached_get(
        self,
        endpoint_slug: str,
        path: str,
        params: dict[str, Any] | None = None,
        chain: str | None = None,
        address: str | None = None,
        ttl: int = 300,
    ) -> dict[str, Any]:
        resolved_chain = chain or self.default_chain
        cache_address = address or "global"
        cache_key = self._cache_key(endpoint_slug, resolved_chain, cache_address)

        cached = await self.redis.get_json(cache_key)
        if cached is not None:
            logger.info(f"birdeye {endpoint_slug} {resolved_chain} {cache_address} [cache hit]")
            self.cache_hit_count += 1
            return cached

        logger.info(f"birdeye {endpoint_slug} {resolved_chain} {cache_address} [cache miss]")
        lock_key = f"birdeye:lock:{endpoint_slug}:{resolved_chain}:{cache_address}"
        lock_acquired = await self.redis.set_if_not_exists(lock_key, "1", ttl=10)
        if not lock_acquired:
            await asyncio.sleep(0.5)
            cached = await self.redis.get_json(cache_key)
            if cached is not None:
                logger.info(f"birdeye {endpoint_slug} {resolved_chain} {cache_address} [cache hit]")
                self.cache_hit_count += 1
                return cached

        try:
            payload = await self._get(path, params, resolved_chain, endpoint_slug, cache_address)
            await self.redis.set_json(cache_key, payload, ttl=ttl)
            return payload
        finally:
            if lock_acquired:
                await self.redis.delete(lock_key)

    def _scope_from_params(self, params: dict[str, Any] | None) -> str:
        if not params:
            return "global"
        parts = [f"{key}={params[key]}" for key in sorted(params)]
        return "&".join(parts)

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None,
        chain: str,
        endpoint_slug: str,
        address: str,
    ) -> dict[str, Any]:
        headers = {
            "accept": "application/json",
            "X-API-KEY": self.api_key,
            "x-chain": chain,
        }

        rate_limit_delays = [1, 2, 4]
        server_attempts = 0
        rate_limit_attempts = 0

        while True:
            logger.info(f"birdeye {endpoint_slug} {chain} {address}")
            self.external_call_count += 1
            response = await self._client.get(
                f"{self.BASE_URL}{path}",
                headers=headers,
                params=params or {},
            )

            if response.status_code == 429 and rate_limit_attempts < len(rate_limit_delays):
                delay = rate_limit_delays[rate_limit_attempts]
                rate_limit_attempts += 1
                await asyncio.sleep(delay)
                continue

            if response.status_code == 429:
                raise BirdeyeRateLimitError(response.text)

            if response.status_code >= 500 and server_attempts < 2:
                server_attempts += 1
                await asyncio.sleep(server_attempts)
                continue

            if response.status_code == 404:
                raise BirdeyeNotFoundError(response.text)

            if 400 <= response.status_code < 500:
                raise BirdeyeBadRequestError(response.text)

            if response.status_code >= 500:
                raise BirdeyeServerError(response.text)

            response.raise_for_status()
            return response.json()

    async def token_overview(
        self,
        address: str,
        chain: str | None = None,
        ttl: int = 300,
    ) -> dict[str, Any]:
        return await self._cached_get(
            "token_overview",
            "/defi/token_overview",
            {"address": address},
            chain,
            address,
            ttl,
        )

    async def token_security(
        self,
        address: str,
        chain: str | None = None,
        ttl: int = 300,
    ) -> dict[str, Any]:
        return await self._cached_get(
            "token_security",
            "/defi/token_security",
            {"address": address},
            chain,
            address,
            ttl,
        )

    async def token_creation_info(
        self,
        address: str,
        chain: str | None = None,
        ttl: int = 86400,
    ) -> dict[str, Any]:
        return await self._cached_get(
            "token_creation_info",
            "/defi/token_creation_info",
            {"address": address},
            chain,
            address,
            ttl,
        )

    async def token_holders(
        self,
        address: str,
        limit: int = 20,
        chain: str | None = None,
        offset: int = 0,
        ttl: int = 300,
    ) -> dict[str, Any]:
        return await self._cached_get(
            "token_holders",
            "/defi/v3/token/holder",
            {"address": address, "offset": offset, "limit": limit},
            chain,
            address,
            ttl,
        )

    async def token_txs(
        self,
        address: str,
        limit: int = 50,
        sort: str = "asc",
        chain: str | None = None,
        offset: int = 0,
        tx_type: str = "all",
        ttl: int = 60,
    ) -> dict[str, Any]:
        return await self._cached_get(
            "token_txs",
            "/defi/txs/token",
            {
                "address": address,
                "offset": offset,
                "limit": limit,
                "tx_type": tx_type,
                "sort_type": sort,
            },
            chain,
            f"{address}:offset={offset}:limit={limit}:tx_type={tx_type}:sort={sort}",
            ttl,
        )

    async def token_trending(
        self,
        limit: int = 20,
        chain: str | None = None,
        sort_by: str = "rank",
        sort_type: str = "asc",
        offset: int = 0,
        ttl: int = 60,
    ) -> dict[str, Any]:
        return await self._cached_get(
            "token_trending",
            "/defi/token_trending",
            {
                "sort_by": sort_by,
                "sort_type": sort_type,
                "offset": offset,
                "limit": limit,
            },
            chain,
            "global",
            ttl,
        )

    async def new_listings(
        self,
        chain: str | None = None,
        time_to: int | None = None,
        limit: int = 20,
        meme_platform_enabled: bool = True,
        ttl: int = 60,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "limit": limit,
            "meme_platform_enabled": str(meme_platform_enabled).lower(),
        }
        if time_to is not None:
            params["time_to"] = time_to

        return await self._cached_get(
            "new_listings",
            "/defi/v2/tokens/new_listing",
            params,
            chain,
            "global",
            ttl,
        )
