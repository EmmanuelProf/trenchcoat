# BIRDEYE_REFERENCE.md

> **Authoritative reference for the Birdeye Data Services API as we use it in TRENCHCOAT.** When writing or modifying Birdeye-touching code, treat this file as ground truth. Do not guess endpoint paths, parameter names, or response shapes from training data. If something here looks wrong or stale, ask the human to confirm against `https://docs.birdeye.so/` before changing code.

## Auth

- Base URL: `https://public-api.birdeye.so`
- Header: `X-API-KEY: <your_api_key>`
- Header: `x-chain: <chain>` (one of: `solana`, `ethereum`, `arbitrum`, `avalanche`, `bsc`, `optimism`, `polygon`, `base`, `zksync`, `sui`, `monad`)
- All endpoints accept JSON. Always send `accept: application/json`.

## Rate limits

- Free tier: 30k compute units/month
- Compute units per call vary by endpoint (most are 1-3 CU)
- 429 response means rate limited — back off exponentially

## Endpoints we use

### 1. Token overview
- **Path:** `/defi/token_overview`
- **Method:** GET
- **Query params:** `address` (required)
- **Returns:** symbol, name, decimals, supply, price, mc, liquidity, holder count, volume metrics, price changes
- **Cache TTL:** 300s
- **CU cost:** 1

### 2. Token security
- **Path:** `/defi/token_security`
- **Method:** GET
- **Query params:** `address` (required)
- **Returns:** mint authority, freeze authority, top10HolderPercent, top10HolderBalance, ownerPercentage, mutableMetadata, transferFeeEnable, more
- **Cache TTL:** 300s
- **CU cost:** 1
- **Note:** Not supported on Sui

### 3. Token creation info
- **Path:** `/defi/token_creation_info`
- **Method:** GET
- **Query params:** `address` (required)
- **Returns:** owner (deployer wallet), txHash, slot, decimals, blockHumanTime, blockUnixTime
- **Cache TTL:** 86400s (creation info doesn't change)
- **CU cost:** 1
- **Note:** Not supported on Sui

### 4. Token holders (Token Holder list)
- **Path:** `/defi/v3/token/holder` (preferred v3) — or `/defi/token_holder` if v3 not available
- **Method:** GET
- **Query params:** `address`, `offset` (default 0), `limit` (default 100, max 100)
- **Returns:** array of `{owner, amount, ui_amount, decimals, mint, token_account}`
- **Cache TTL:** 300s
- **CU cost:** 5

### 5. Token transactions
- **Path:** `/defi/txs/token`
- **Method:** GET
- **Query params:** `address`, `offset` (default 0), `limit` (max 50), `tx_type` (`swap`/`add`/`remove`/`all`), `sort_type` (`asc`/`desc`)
- **Returns:** array of transaction objects with `txHash, blockUnixTime, owner, from/to tokens, ui amounts, side`
- **Cache TTL:** 60s (transactions are live data — short cache)
- **CU cost:** 5
- **Note:** For bundle detection, use `sort_type=asc` to get oldest first, paginate to first ~100 txs

### 6. Token trending
- **Path:** `/defi/token_trending`
- **Method:** GET
- **Query params:** `sort_by` (`rank`/`volume24hUSD`/`liquidity`), `sort_type` (`asc`/`desc`), `offset`, `limit` (max 20)
- **Returns:** array of trending tokens with `address, name, symbol, rank, price, mc, liquidity, volume24hUSD`
- **Cache TTL:** 60s
- **CU cost:** 1

### 7. New token listings
- **Path:** `/defi/v2/tokens/new_listing`
- **Method:** GET
- **Query params:** `time_to` (unix timestamp), `limit` (max 20), `meme_platform_enabled` (bool)
- **Returns:** array of new tokens with `address, symbol, name, source, liquidityAddedAt, decimals, liquidity`
- **Cache TTL:** 60s
- **CU cost:** 1

### 8. Wallet portfolio (used in dev history evaluation)
- **Path:** `/v1/wallet/token_list`
- **Method:** GET
- **Query params:** `wallet` (required)
- **Returns:** array of tokens held by the wallet
- **Cache TTL:** 300s
- **Note:** Not supported on Sui

### 9. Supported networks (sanity check, occasional)
- **Path:** `/defi/networks`
- **Method:** GET
- **Returns:** `{data: [chain names], success: true}`
- **CU cost:** 0

## Calling pattern (Python)

```python
import httpx

class BirdeyeClient:
    BASE_URL = "https://public-api.birdeye.so"
    
    def __init__(self, api_key: str, default_chain: str = "solana"):
        self.api_key = api_key
        self.default_chain = default_chain
        self._client = httpx.AsyncClient(timeout=10.0)
    
    async def _get(self, path: str, params: dict | None = None, chain: str | None = None) -> dict:
        chain = chain or self.default_chain
        headers = {
            "accept": "application/json",
            "X-API-KEY": self.api_key,
            "x-chain": chain,
        }
        url = f"{self.BASE_URL}{path}"
        resp = await self._client.get(url, headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.json()
    
    async def token_overview(self, address: str, chain: str | None = None) -> dict:
        return await self._get("/defi/token_overview", {"address": address}, chain)
    # ... etc
```

## Response envelope

Most Birdeye responses wrap the actual data:

```json
{
  "success": true,
  "data": { ... actual fields ... }
}
```

Always extract `response["data"]` before using. Some endpoints return `data` as an object, others as `{items: [...], hasNext: bool}`. Read the actual response, don't assume.

## Common gotchas

1. **Solana addresses** are base58, 32-44 chars, no `0x` prefix. EVM is `0x` + 40 hex chars. Validate before sending.
2. **`top10HolderPercent`** is a decimal (0.72) or percent (72) depending on endpoint version — always normalize to a percentage (0-100) at the boundary.
3. **`mintAuthority`** field returns either the wallet address (not revoked) or null/empty (revoked). Test both.
4. **Holder list pagination** — at limit=100 you have to paginate. We don't need >20 for our use case.
5. **Transactions are eventually consistent** — a token launched 5 seconds ago may not have all txs indexed yet. Handle empty arrays gracefully.
6. **Some new tokens have no security data** — endpoint may 404 or return partial. Don't crash the dossier; render "data unavailable" for that section.
7. **Multi-chain** — never hardcode `solana` anywhere except as a default. Always pass `chain` through the call chain.

## When the agent should ask before doing

Stop and ask the user if:

- A response field name doesn't match what's documented here (Birdeye may have updated)
- An endpoint returns an unexpected shape
- You think you need an endpoint that's not in this file
- You're tempted to add a chain to the supported list that's not above

Don't silently work around — surface it.

## Verifying the API works

Quick smoke test (do this once, after backend deploys):

```bash
curl -H "X-API-KEY: $BIRDEYE_API_KEY" -H "x-chain: solana" \
  "https://public-api.birdeye.so/defi/token_overview?address=DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
```

Should return a JSON with `success: true` and `data.symbol == "Bonk"`.
