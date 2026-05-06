# SPECS.md — TRENCHCOAT Feature Specifications

> **Read PROJECT_CONTEXT.md first.** Each spec below is self-contained. Build them in the order listed. Don't move to the next spec until the current one passes its acceptance test.

---

## SPEC-001: Birdeye client wrapper

**File:** `backend/app/services/birdeye.py`

**Purpose:** A single, well-tested client class that all other services use to talk to Birdeye. Handles auth, chain routing, retries, and caching transparently.

**Interface:**

```python
class BirdeyeClient:
    def __init__(self, api_key: str, redis_client, default_chain: str = "solana"): ...
    
    async def token_overview(self, address: str, chain: str | None = None) -> dict: ...
    async def token_security(self, address: str, chain: str | None = None) -> dict: ...
    async def token_creation_info(self, address: str, chain: str | None = None) -> dict: ...
    async def token_holders(self, address: str, limit: int = 20, chain: str | None = None) -> dict: ...
    async def token_txs(self, address: str, limit: int = 50, sort: str = "asc", chain: str | None = None) -> dict: ...
    async def token_trending(self, limit: int = 20, chain: str | None = None) -> dict: ...
    async def new_listings(self, chain: str | None = None) -> dict: ...
```

**Required behaviors:**

1. Uses `httpx.AsyncClient` for all calls
2. Sends `X-API-KEY` and `x-chain` headers on every request
3. Caches every response in Redis with key pattern `birdeye:{endpoint}:{chain}:{address}` and 300s TTL
4. On 429, retries up to 3 times with exponential backoff (1s, 2s, 4s)
5. On 5xx, retries up to 2 times
6. On 4xx (other than 429), raises a `BirdeyeNotFoundError` or `BirdeyeBadRequestError` — does not retry
7. Logs every external call with `logger.info(f"birdeye {endpoint} {chain} {address}")`
8. Never returns mock data on failure — always raises

**Acceptance test:**

Create a script `backend/scripts/test_birdeye.py` that:
- Initializes the client
- Calls `token_overview` for the $BONK CA on Solana
- Asserts the response has `data.symbol == "Bonk"`
- Calls it again immediately and confirms second call hits cache (log line should differ)

Run it. If it passes, this spec is done.

---

## SPEC-002: Dossier orchestrator endpoint

**File:** `backend/app/api/dossier.py`

**Purpose:** The main public endpoint. Takes a CA + chain, fans out to Birdeye, runs scoring, returns a complete dossier JSON.

**Endpoint:** `GET /dossier/{ca}?chain=solana`

**Response shape (Pydantic model in `backend/app/models/dossier.py`):**

```python
class Dossier(BaseModel):
    ca: str
    chain: str
    generated_at: datetime
    score: int  # 0-100
    band: Literal["AVOID", "CAUTION", "CLEAR"]
    
    overview: TokenOverview  # symbol, name, price, mc, liquidity, supply
    security: TokenSecurity  # mint_revoked, freeze_revoked, top10_pct, etc.
    deployer: DeployerProfile  # wallet, prior_tokens, prior_outcomes
    distribution: SupplyDistribution  # bundle_pct, top10_pct, suspect_wallets
    
    verdict: str  # AI-generated, ≤2 sentences
    
    raw_signals: dict  # all the underlying numbers, for transparency
```

**Required behaviors:**

1. All sub-fetches (overview, security, holders, txs, deployer history) run in parallel using `asyncio.gather`
2. If any sub-fetch fails, that section returns null but the dossier still renders — don't fail the whole request
3. Total cache-hit response time: <100ms
4. Total cold response time: <3000ms (Birdeye fan-out + Claude verdict)
5. Final dossier is cached in Redis at key `dossier:{chain}:{ca}` for 300s
6. The AI verdict is generated last, using all prior signals as input
7. CORS configured to allow `https://<your-vercel-url>.vercel.app` and `http://localhost:3000`

**Acceptance test:**

```bash
curl -s http://localhost:8000/dossier/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263 | jq
```

Must return a valid Dossier JSON within 3 seconds. Score must be a number 0-100. `band` must be one of the three literals. `verdict` must be a non-empty string.

---

## SPEC-003: Bundle detection algorithm

**File:** `backend/app/services/bundle.py`

**Purpose:** Detect whether early buyers of a token were coordinated (i.e., a "bundle" — likely insider/sniper buying).

**Function signature:**

```python
async def detect_bundle(ca: str, chain: str, birdeye: BirdeyeClient) -> BundleAnalysis:
    ...

class BundleAnalysis(BaseModel):
    bundled: bool
    bundle_pct: float  # % of supply held by suspect wallets
    suspect_wallet_count: int
    earliest_block: int
    confidence: Literal["high", "medium", "low"]
```

**Algorithm:**

1. Fetch first 100 transactions for the token, sorted ascending (oldest first)
2. Filter to BUY transactions only
3. Identify the launch window: the first transaction's block, plus the next 30 seconds of activity
4. Group all buys in the launch window by wallet
5. For each wallet, sum the total amount bought in that window
6. Get top 10 launch-window buyers by amount
7. Compare their combined holdings to current circulating supply
8. If top-10 launch buyers hold >25% of supply → bundled = true, confidence = high
9. If between 15-25% → bundled = true, confidence = medium
10. If between 10-15% → bundled = true, confidence = low
11. If <10% → bundled = false

**Edge cases to handle:**

- New tokens with <10 transactions: return `bundled=false, confidence="low"` (insufficient data)
- Tokens older than 30 days: skip bundle detection (the early window is meaningless now), return `bundled=false, confidence="low"`
- Birdeye returns no transactions: return null, log warning

**Acceptance test:**

Run against three CAs:
- A known bundled launch (find one from this week's `pump.fun` migration scams)
- $BONK (should be unbundled, established)
- A brand-new launch from `/v2/tokens/new_listing`

Print the BundleAnalysis for each. Manually verify the known-bundled case returns `bundled=true`.

---

## SPEC-004: Dev history indexer + lookup

**Files:** 
- `backend/app/services/dev_history.py` (lookup)
- `backend/scripts/bootstrap_dev_history.py` (one-time backfill)
- Supabase migration: `backend/supabase/migrations/001_dev_history.sql`

**Purpose:** Given a deployer wallet, return all known prior tokens they deployed and the outcome of each (rugged / abandoned / alive).

**Supabase schema:**

```sql
CREATE TABLE deployer_history (
    id BIGSERIAL PRIMARY KEY,
    deployer_wallet TEXT NOT NULL,
    token_ca TEXT NOT NULL,
    chain TEXT NOT NULL,
    deployed_at TIMESTAMPTZ NOT NULL,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(deployer_wallet, token_ca, chain)
);
CREATE INDEX idx_deployer ON deployer_history(deployer_wallet, chain);

CREATE TABLE token_outcomes (
    token_ca TEXT NOT NULL,
    chain TEXT NOT NULL,
    outcome TEXT NOT NULL,  -- 'rugged', 'abandoned', 'alive', 'unknown'
    pct_from_ath DECIMAL,
    last_evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (token_ca, chain)
);
```

**Outcome rules:**

- `alive`: token <30 days old, OR price within 50% of ATH
- `abandoned`: token >30 days old, price <20% of ATH, no transactions in 7 days
- `rugged`: token >7 days old, price <5% of ATH, AND liquidity <$1k (or removed)
- `unknown`: insufficient data

**Lookup function:**

```python
async def get_deployer_profile(wallet: str, chain: str, birdeye: BirdeyeClient, supabase) -> DeployerProfile:
    # 1. Query deployer_history for this wallet
    # 2. For each prior token, fetch (or read cached) outcome from token_outcomes
    # 3. If outcome >7 days stale, re-evaluate using Birdeye token_overview + token_security
    # 4. Return DeployerProfile with summary stats
```

**Bootstrap script:**

`scripts/bootstrap_dev_history.py` does the following on a single run:
1. Fetches `/v2/tokens/new_listing` from Birdeye for the past 30 days (paginate as needed)
2. For each token, fetches `token_creation_info` to get the deployer wallet
3. Inserts (deployer_wallet, token_ca, chain, deployed_at) into Supabase
4. Logs progress every 100 tokens
5. Idempotent — re-running doesn't duplicate rows (use UPSERT on the unique constraint)

**Acceptance test:**

1. Run the bootstrap script. Verify Supabase has >500 rows.
2. Pick a deployer wallet that has multiple tokens. Call `get_deployer_profile`. Verify it returns the right tokens and outcomes.

---

## SPEC-005: AI verdict generator

**File:** `backend/app/services/verdict.py`

**Purpose:** Given the structured signals from the dossier, generate a 1-2 sentence punchy verdict in TRENCHCOAT brand voice.

**Function signature:**

```python
async def generate_verdict(signals: dict, score: int, band: str) -> str:
    ...
```

**Implementation:**

Use `anthropic` Python SDK. Model: `claude-haiku-4-5` (cheapest, fast enough; upgrade to sonnet only if quality is poor).

System prompt (use exactly this):

```
You are TRENCHCOAT, a no-bullshit on-chain detective. You write verdicts on tokens for degens about to ape. Your style: noir, terse, specific. Numbers over adjectives. Never use words like "leverage," "ecosystem," "robust," "synergy," "consider." Never disclaim. Never moralize. Just call what you see.

You write 1-2 sentences max. Each sentence is short. The reader has 3 seconds.

Examples of good verdicts:
- "Same wallet shipped three tokens. All three zeros. This makes four."
- "72% of supply in ten wallets. Mint not revoked. You know the rest."  
- "Clean deployer. Locked liquidity. Even distribution. Rare. Could actually be real."
- "Bundled launch — top 10 buyers in the same block grabbed 38%. Skip."

Bad examples (never write like this):
- "This token shows several concerning risk indicators..."
- "Our analysis suggests caution is warranted..."
- "Multiple metrics indicate elevated risk..."

Output the verdict only. No preamble, no quotes, no labels.
```

User prompt template:

```
Token: ${symbol} (${ca})
Score: ${score}/100 — ${band}

Signals:
- Mint authority revoked: ${mint_revoked}
- Freeze authority revoked: ${freeze_revoked}
- Top 10 holders %: ${top10_pct}
- Bundled launch: ${bundled} (top-10 launch buyers hold ${bundle_pct}%)
- Deployer prior tokens: ${prior_count} (rugged: ${rugged_count}, abandoned: ${abandoned_count})
- Liquidity: $${liquidity}
- Age: ${age_days} days

Write the verdict.
```

**Required behaviors:**

1. Cache verdicts in Redis keyed by hash of signals (TTL 300s) — same signals = same verdict, no re-spend
2. Timeout: 5 seconds. If Claude doesn't respond, fall back to a rule-based verdict (see fallback below)
3. Strip any quotes or markdown the model adds
4. Reject responses >200 chars; on rejection, regenerate once

**Rule-based fallback:**

If band == "AVOID": `"Multiple red flags. Score: {score}/100. Don't."`
If band == "CAUTION": `"Mixed signals. Score: {score}/100. Size small if at all."`
If band == "CLEAR": `"No major red flags found. Score: {score}/100. Still memecoin — DYOR."`

**Acceptance test:**

Generate verdicts for 5 different test CAs. Print all 5. Manually check: punchy, ≤200 chars, fits brand voice.

---

## SPEC-006: Scorer

**File:** `backend/app/services/scorer.py`

**Purpose:** Convert raw signals into a 0-100 score and band.

**Function:**

```python
def score_dossier(
    security: TokenSecurity,
    distribution: SupplyDistribution,
    deployer: DeployerProfile,
    overview: TokenOverview,
) -> tuple[int, str]:  # (score, band)
```

**Scoring rubric (start with 100, deduct):**

| Signal | Deduction |
|---|---|
| Mint authority NOT revoked | -25 |
| Freeze authority NOT revoked | -10 |
| Top 10 holders > 80% | -20 |
| Top 10 holders 50-80% | -10 |
| Bundle detected, confidence high | -25 |
| Bundle detected, confidence medium | -15 |
| Bundle detected, confidence low | -5 |
| Deployer has 1 prior rug | -15 |
| Deployer has 2 prior rugs | -25 |
| Deployer has 3+ prior rugs | -35 |
| Liquidity < $5k | -15 |
| Liquidity $5k-$20k | -5 |

Floor at 0. Ceiling at 100.

**Bands:**
- 0-30: AVOID
- 31-60: CAUTION
- 61-100: CLEAR

**Acceptance test:**

Unit-test 5 hand-crafted scenarios — print expected vs actual. No external calls needed for this test.

---

## SPEC-007: Frontend — paste hero + dossier page

**Files:**
- `frontend/app/page.tsx` (landing + paste hero)
- `frontend/app/dossier/[ca]/page.tsx` (dossier detail)
- `frontend/components/PasteHero.tsx`
- `frontend/components/RapSheet.tsx`
- `frontend/components/ChainSelector.tsx`
- `frontend/lib/api.ts` (FastAPI client)

**Landing page (`page.tsx`) requirements:**

- Hero: huge "TRENCHCOAT" logo (monospace, all caps, off-white on near-black bg)
- Subhead: "Paste a token. Know who's behind it before you lose your money."
- Big paste input with chain selector dropdown next to it
- On paste/submit: navigate to `/dossier/{ca}?chain={chain}`
- Below the fold: "How it works" — 3 cards: (1) Dev history check, (2) Bundle detection, (3) AI verdict
- Footer: "Built with Birdeye Data. Not financial advice." + GitHub link

**Dossier page (`dossier/[ca]/page.tsx`) requirements:**

- Server component, fetches from FastAPI on render
- Renders the `<RapSheet />` component with full dossier
- Sets dynamic metadata: title `"$SYMBOL — TRENCHCOAT Rap Sheet"`, OG image `/api/og/{ca}`
- Loading state: terminal-style "SCANNING..." animation with shimmer skeleton
- Error state: "Couldn't pull data on this one. Try again." with retry button

**RapSheet component:**

Card layout matching the format in PROJECT_CONTEXT.md. Five sections:
1. Header: ticker, score, band badge, generated_at
2. The Dev: wallet, prior tokens with mini-status badges
3. Supply Distribution: bundle %, top-10 %, sparkline visualization
4. Token Security: mint/freeze/liquidity status with green/red icons
5. AI Verdict: large quote-style text

Use shadcn/ui `Card`, `Badge`, `Separator`. Color tokens:
- Red: `#ef4444`
- Yellow: `#eab308`
- Green: `#22c55e`
- Background: `#0a0a0a`
- Card: `#171717`
- Text: `#f5f5f5`
- Mono accent: `font-mono` on all addresses, scores, percentages

**Acceptance test:**

1. Visit `https://<your-vercel-url>.vercel.app` — paste a CA, get redirected to dossier page
2. Dossier page renders all 5 sections with real data
3. Lighthouse score >90 on performance
4. Mobile responsive (test at 375px)

---

## SPEC-008: Dynamic OG image generator

**File:** `frontend/app/api/og/[ca]/route.tsx`

**Purpose:** When someone tweets a `<your-vercel-url>.vercel.app/dossier/{ca}` link, the X preview shows a custom Rap Sheet image, not a generic OG.

**Implementation:**

Use Next.js `ImageResponse` from `next/og`. Generate a 1200x630 PNG with:
- Black background
- TRENCHCOAT logo top-left
- Token symbol + score huge in center
- Band badge (AVOID/CAUTION/CLEAR) with color
- 3-line summary of top signals ("4 prior rugs. 72% concentration. Mint not revoked.")
- Your live production URL bottom-right

Cache the OG image: 5-min CDN cache via response headers.

**Acceptance test:**

1. Hit `https://<your-vercel-url>.vercel.app/api/og/{some_ca}` directly — should return a PNG
2. Tweet a dossier link — verify the preview renders the custom image
3. Run through `https://www.opengraph.xyz/` to verify metadata

---

## SPEC-009: Telegram bot

**File:** `telegram-bot/bot.py`

**Purpose:** Daily-use surface where degens DM the bot a CA and get a Rap Sheet in chat.

**Commands:**

- `/start` — welcome message + how to use
- `/rap <ca>` or just paste a CA — fetch dossier from FastAPI, format as Telegram message
- `/help` — show commands

**Rap Sheet format in Telegram (Markdown):**

```
🔴 *$TICKER — AVOID*  (Score: 18/100)

*The Dev*
`9xK2...4mPq`
3 prior tokens, all dead.

*Supply*
Top 10: 72%
Bundled: ⚠️ 38%

*Security*
Mint: ❌ not revoked
Freeze: ✅ revoked

*Verdict*
"Same wallet shipped three tokens. All three zeros. This makes four."

[View full Rap Sheet →](https://<your-vercel-url>.vercel.app/dossier/{ca})
```

**Required behaviors:**

1. Parse CA from any message containing a 32-44 char base58 string
2. Show "🔍 Scanning..." while fetching
3. Edit message in place when ready (no spam)
4. Rate limit: 5 raps per user per minute
5. Inline button: "Share to channel" — generates a forwardable card

**Acceptance test:**

1. Start the bot, open a chat
2. Send `/rap DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`
3. Receive properly formatted Rap Sheet within 5 seconds
4. Send 6 raps in a minute — confirm 6th is rate-limited

---

## SPEC-010: Trending feed page

**File:** `frontend/app/trending/page.tsx` (and supporting backend endpoint)

**Backend endpoint:** `GET /trending?chain=solana&limit=20`

Returns array of mini-dossiers (just ticker, score, band, top signal). Cached 5 min.

**Frontend:**

- Grid of 20 mini Rap Sheet cards
- Each card: ticker, score, band badge, one-liner ("4 prior rugs"), link to full dossier
- Auto-refresh every 60s
- Sort options: by score asc, by score desc, by trending rank

**Acceptance test:**

`/trending` loads in <2s, shows 20 tokens with scores, clicking any opens its dossier.

---

## Build order

Build in this exact order. Don't skip ahead:

1. SPEC-001 (Birdeye client) — everything depends on it
2. SPEC-006 (Scorer) — pure logic, no deps, easy win
3. SPEC-003 (Bundle detection) — uses Birdeye client only
4. SPEC-004 (Dev history) — uses Birdeye + Supabase, takes longest
5. SPEC-005 (AI verdict) — uses Claude API
6. SPEC-002 (Dossier orchestrator) — wires it all together
7. SPEC-007 (Frontend) — once backend is solid
8. SPEC-008 (OG images) — quick win, big visual impact
9. SPEC-009 (Telegram bot) — reuses backend
10. SPEC-010 (Trending feed) — final polish

Specs 1-6 = Day 1 backend. Specs 7-8 = Day 2 frontend. Specs 9-10 = Day 3 + polish.
