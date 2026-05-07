from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


class SupabaseError(RuntimeError):
    pass


class SupabaseClient:
    def __init__(self, url: str, service_key: str, timeout: float = 10.0) -> None:
        if not url:
            raise ValueError("SUPABASE_URL is required")
        if not service_key:
            raise ValueError("SUPABASE_SERVICE_KEY is required")

        self.url = url.rstrip("/")
        self.service_key = service_key
        self._client = httpx.AsyncClient(
            base_url=f"{self.url}/rest/v1",
            headers={
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
            trust_env=False,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = await self._client.request(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
        )
        if response.status_code >= 400:
            raise SupabaseError(f"{response.status_code} {response.text}")
        if not response.content:
            return None
        return response.json()

    async def upsert_deployer_record(
        self,
        deployer_wallet: str,
        token_ca: str,
        chain: str,
        deployed_at: str | datetime,
    ) -> dict[str, Any] | None:
        row = {
            "deployer_wallet": deployer_wallet,
            "token_ca": token_ca,
            "chain": chain,
            "deployed_at": _as_iso(deployed_at),
        }
        rows = await self._request(
            "POST",
            "/deployer_history",
            params={"on_conflict": "deployer_wallet,token_ca,chain"},
            json=row,
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        )
        return rows[0] if rows else None

    async def get_tokens_by_deployer(self, deployer_wallet: str, chain: str) -> list[str]:
        rows = await self._request(
            "GET",
            "/deployer_history",
            params={
                "select": "token_ca",
                "deployer_wallet": f"eq.{deployer_wallet}",
                "chain": f"eq.{chain}",
                "order": "deployed_at.desc",
            },
        )
        return [row["token_ca"] for row in rows or [] if row.get("token_ca")]

    async def upsert_token_outcome(
        self,
        token_ca: str,
        chain: str,
        outcome: str,
        pct_from_ath: float | None,
    ) -> dict[str, Any] | None:
        row = {
            "token_ca": token_ca,
            "chain": chain,
            "outcome": outcome,
            "pct_from_ath": pct_from_ath,
            "last_evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        rows = await self._request(
            "POST",
            "/token_outcomes",
            params={"on_conflict": "token_ca,chain"},
            json=row,
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        )
        return rows[0] if rows else None

    async def get_token_outcome(self, token_ca: str, chain: str) -> dict[str, Any] | None:
        rows = await self._request(
            "GET",
            "/token_outcomes",
            params={
                "select": "*",
                "token_ca": f"eq.{token_ca}",
                "chain": f"eq.{chain}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    async def count_deployer_history(self, chain: str | None = None) -> int:
        params = {"select": "id"}
        if chain:
            params["chain"] = f"eq.{chain}"
        response = await self._client.get(
            "/deployer_history",
            params=params,
            headers={"Prefer": "count=exact", "Range": "0-0"},
        )
        if response.status_code >= 400:
            raise SupabaseError(f"{response.status_code} {response.text}")

        content_range = response.headers.get("content-range", "")
        if "/" in content_range:
            total = content_range.rsplit("/", 1)[-1]
            if total.isdigit():
                return int(total)
        rows = response.json() if response.content else []
        return len(rows)

    async def get_deployer_history_rows(
        self,
        chain: str,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        return await self._request(
            "GET",
            "/deployer_history",
            params={
                "select": "deployer_wallet,token_ca,chain,deployed_at",
                "chain": f"eq.{chain}",
                "order": "deployed_at.desc",
                "limit": str(limit),
            },
        ) or []


def from_env() -> SupabaseClient:
    return SupabaseClient(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )


def _as_iso(value: str | datetime) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value
