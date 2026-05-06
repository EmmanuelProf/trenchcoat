# AGENT_PLAYBOOK.md — Codex/Claude Code Prompts in Order

> **How to use:** Codex is your builder. Claude Code is your reviewer. After each Codex run, optionally run the review prompt with Claude Code as a second pair of eyes. Most prompts assume Codex is launched in your repo root with `PROJECT_CONTEXT.md`, `SPECS.md`, and `BIRDEYE_REFERENCE.md` already there.

---

## Pre-flight (do this once, before any agent prompts)

### Manual setup checklist (you, not the agents — 30 min)

- [ ] Sign up at `bds.birdeye.so`, generate API key, save to a password manager
- [ ] Sign up at `console.anthropic.com`, generate API key, add $5-10 credit
- [ ] Sign up at `supabase.com`, create project "trenchcoat", note the URL + anon key + service role key
- [ ] Sign up at `console.upstash.com`, create Redis database (free tier), note REST URL + token
- [ ] Sign up at `railway.app`, link GitHub
- [ ] Sign up at `vercel.com`, link GitHub
- [ ] Create GitHub repo `trenchcoat` (public), clone locally
- [ ] Place `PROJECT_CONTEXT.md`, `SPECS.md`, `BIRDEYE_REFERENCE.md` in repo root, commit

Once that's done, you're ready for agent work.

---

# DAY 1 — BACKEND FOUNDATION

## Prompt 1.1 — Repo scaffold

**Run with:** Codex (working directory = repo root)

```
Read PROJECT_CONTEXT.md, SPECS.md, and BIRDEYE_REFERENCE.md fully before doing anything else.

Then create the repo structure described in PROJECT_CONTEXT.md under the "Repository structure" section. Create empty placeholder files where specified, except create real content for:

1. backend/requirements.txt — pin: fastapi, uvicorn[standard], httpx, redis, supabase, anthropic, python-telegram-bot, python-dotenv, pydantic
2. backend/.env.example — list all env vars needed: BIRDEYE_API_KEY, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, ALLOWED_ORIGINS
3. backend/railway.json — minimal Railway config for a FastAPI app on port $PORT
4. backend/app/main.py — FastAPI app with CORS middleware reading ALLOWED_ORIGINS, a /health endpoint that returns {"ok": true, "service": "trenchcoat-api"}, and a placeholder router import
5. frontend/package.json — Next.js 14 + TypeScript + Tailwind + shadcn/ui dependencies
6. README.md — public-facing readme with project description, demo URL placeholder, "built with Birdeye Data" credit, GitHub badge

Do NOT install dependencies yet. Do NOT write any service code yet. Just the scaffold.

After scaffolding: print a tree of what you created and stop.
```

**Review checklist:**
- [ ] All directories from PROJECT_CONTEXT.md exist
- [ ] `requirements.txt` has all 9 packages, no extras
- [ ] `.env.example` has all 7 env vars listed
- [ ] `main.py` has a working `/health` endpoint
- [ ] No service code was written prematurely

---

## Prompt 1.2 — Build SPEC-001: Birdeye client wrapper

**Run with:** Codex

```
Read SPECS.md SPEC-001 and BIRDEYE_REFERENCE.md fully.

Implement the Birdeye client wrapper at backend/app/services/birdeye.py exactly as specified. Also create backend/app/db/redis_client.py with an Upstash Redis REST client using httpx (not the redis-py library — Upstash REST is simpler for serverless-ish backends).

Then create backend/scripts/test_birdeye.py that runs the acceptance test from SPEC-001:
1. Initializes the client with env vars
2. Calls token_overview for $BONK CA on Solana (DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263)
3. Asserts response data.symbol == "Bonk"
4. Calls it again and asserts second call hits cache (use a counter or log inspection)
5. Prints "✅ SPEC-001 passes" if all assertions hold

Run the test script. Paste the output. If it fails, fix and re-run until it passes.

Constraints:
- Use httpx.AsyncClient with timeout=10
- Implement retry with exponential backoff (1s, 2s, 4s) on 429
- Cache key pattern: birdeye:{endpoint_slug}:{chain}:{address}
- TTL 300s default, but make it configurable per method
- Log every external call. Format: f"birdeye GET {path} chain={chain}"
- Raise BirdeyeNotFoundError on 404, BirdeyeBadRequestError on other 4xx
```

**Review checklist:**
- [ ] All 7 endpoint methods from BIRDEYE_REFERENCE.md are implemented
- [ ] Cache hit/miss is observable in logs
- [ ] Test script printed "✅ SPEC-001 passes"
- [ ] No mocks/stubs anywhere — real API calls only

**Optional second-pair-of-eyes prompt for Claude Code:**

```
Read backend/app/services/birdeye.py and BIRDEYE_REFERENCE.md.

Audit the client for:
1. Endpoint paths matching BIRDEYE_REFERENCE.md exactly
2. Header names and casing (X-API-KEY, x-chain) being correct
3. Cache key collisions across chains
4. Race conditions between cache check and write

Report any issues found. Don't fix them — just list.
```

---

## Prompt 1.3 — Build SPEC-006: Scorer (pure logic, fast win)

**Run with:** Codex

```
Read SPECS.md SPEC-006 fully.

Implement backend/app/services/scorer.py exactly as specified. Also create backend/app/models/dossier.py with the Pydantic models for TokenOverview, TokenSecurity, DeployerProfile, SupplyDistribution, BundleAnalysis, and Dossier.

Then create backend/tests/test_scorer.py with 5 hand-crafted test cases as Python dicts:
1. Clean token (mint revoked, freeze revoked, top10 30%, no bundle, deployer with 0 priors, $50k liquidity) → expect score >70, band CLEAR
2. Bundled new launch (mint not revoked, top10 75%, bundle high confidence 35%, deployer with 0 priors, $5k liquidity) → expect score <30, band AVOID
3. Serial rugger (mint revoked, top10 40%, no bundle, deployer with 3 prior rugs, $20k liquidity) → expect score <40, band AVOID
4. Borderline (mint revoked, freeze not revoked, top10 55%, bundle medium 18%, deployer with 1 prior rug, $30k liquidity) → expect score 30-60, band CAUTION
5. Edge case (deployer unknown, security data missing) → should not crash, return CAUTION with reasonable score

Run the tests. Paste output. Fix until all 5 pass.

Use pytest. Add pytest to requirements.txt.
```

**Review checklist:**
- [ ] Scoring rubric matches SPEC-006 exactly (deductions add up correctly)
- [ ] Score is bounded 0-100
- [ ] Bands match the thresholds
- [ ] All 5 test cases pass
- [ ] Edge case (missing data) doesn't crash

---

## Prompt 1.4 — Build SPEC-003: Bundle detection

**Run with:** Codex

```
Read SPECS.md SPEC-003 and BIRDEYE_REFERENCE.md fully.

Implement backend/app/services/bundle.py with the detect_bundle function exactly as specified.

Important constraints:
- Use the BirdeyeClient from services/birdeye.py — do NOT create a new HTTP client
- Token transactions endpoint paginates: you may need 2 calls (limit 50 each) to get 100 txs
- "Same launch window" = within 30 seconds of the FIRST transaction's blockUnixTime
- "Top 10 launch buyers" — group by `owner` address in tx data, sum amounts bought, take top 10
- Compare top-10 sum to overview.supply (you'll need to call token_overview here too)
- Handle case where token has <10 transactions in launch window (insufficient data)

After implementing, create backend/scripts/test_bundle.py that runs detection against:
1. $BONK (established, should report bundled=false)
2. The most recent token from /defi/v2/tokens/new_listing (test on whatever is fresh)

Run it, paste output.

Edge cases to confirm working:
- Empty tx response → returns null, logs warning, doesn't crash
- Token >30 days old → returns bundled=false, confidence=low (skip detection)
- Token <30 days but very few txs → returns bundled=false, confidence=low
```

**Review checklist:**
- [ ] Bundle algorithm matches SPEC-003 step-by-step
- [ ] Tested against at least 2 real tokens
- [ ] Edge cases (empty, old, sparse) handled without crashing
- [ ] Returns valid BundleAnalysis Pydantic model

---

## Prompt 1.5 — Build SPEC-004: Dev history (database + bootstrap + lookup)

**Run with:** Codex

```
Read SPECS.md SPEC-004 fully.

This task has 4 parts. Do them in order:

PART A — Supabase schema:
Create backend/supabase/migrations/001_dev_history.sql with the schema from SPEC-004. Apply it manually via Supabase SQL editor — print the SQL and tell me to run it.

PART B — Database client:
Create backend/app/db/supabase.py with a Supabase client wrapper using the supabase-py library. Provide functions:
- upsert_deployer_record(deployer_wallet, token_ca, chain, deployed_at)
- get_tokens_by_deployer(deployer_wallet, chain) → list of token_ca
- upsert_token_outcome(token_ca, chain, outcome, pct_from_ath)
- get_token_outcome(token_ca, chain) → returns outcome row or None

PART C — Lookup function:
Implement backend/app/services/dev_history.py with:
- evaluate_token_outcome(token_ca, chain, birdeye) — uses Birdeye to determine outcome rules from SPEC-004, returns ('rugged'|'abandoned'|'alive'|'unknown', pct_from_ath)
- get_deployer_profile(wallet, chain, birdeye, supabase) — queries Supabase for prior tokens, evaluates outcomes (re-evaluates if >7 days stale), returns DeployerProfile

PART D — Bootstrap script:
Create backend/scripts/bootstrap_dev_history.py that:
- Fetches /defi/v2/tokens/new_listing for the past 30 days, paginating with time_to
- For each token, fetches token_creation_info to get the deployer
- Upserts (deployer_wallet, token_ca, chain='solana', deployed_at) into Supabase
- Logs progress every 100 tokens
- Idempotent (re-running doesn't duplicate)

Run the bootstrap script. Tell me how many rows are in deployer_history afterward.

Then run a manual test: pick a deployer wallet that has 2+ tokens (you can find one by querying the table), and call get_deployer_profile. Print the result.
```

**Review checklist:**
- [ ] SQL migration is valid Postgres
- [ ] Bootstrap script ran without errors
- [ ] `deployer_history` table has >500 rows after bootstrap
- [ ] `get_deployer_profile` returns sensible data for a real wallet
- [ ] Outcome evaluation rules from SPEC-004 are followed exactly

---

## Prompt 1.6 — Build SPEC-005: AI verdict generator

**Run with:** Codex

```
Read SPECS.md SPEC-005 fully.

Implement backend/app/services/verdict.py with generate_verdict() exactly as specified.

Use the Anthropic Python SDK (`anthropic` package). Default model: claude-haiku-4-5. The system prompt and user prompt template must match SPEC-005 word-for-word.

Required:
- Cache verdict in Redis keyed by hash of the signals dict (use hashlib.sha256 of json.dumps with sort_keys=True)
- TTL 300s for verdict cache
- 5-second timeout on Claude call
- Fall back to rule-based verdict if Claude fails
- Strip quotes/markdown from response
- If response >200 chars, regenerate once; if still >200, truncate at 200 chars

Then create backend/scripts/test_verdict.py that calls generate_verdict with 5 different signal sets (clean, bundled, serial rugger, borderline, missing data). Print each verdict.

I'll manually verify the verdicts feel punchy and match brand voice. If they're too verbose or generic, we'll adjust the prompt.
```

**Review checklist:**
- [ ] System prompt is exactly what SPEC-005 specifies
- [ ] All 5 test verdicts ≤200 chars
- [ ] Brand voice — terse, specific, numeric
- [ ] Fallback works (test by setting wrong API key briefly)

---

## Prompt 1.7 — Build SPEC-002: Dossier orchestrator (the wiring)

**Run with:** Codex

```
Read SPECS.md SPEC-002 fully.

This is the wire-up. It uses everything built so far. No new logic, just orchestration.

Implement backend/app/api/dossier.py with the GET /dossier/{ca}?chain=solana endpoint exactly as specified.

Behavior:
1. Validate CA format (Solana base58, EVM 0x-prefixed)
2. Check Redis for cached final dossier first — if hit, return it
3. asyncio.gather() these in parallel:
   - birdeye.token_overview(ca, chain)
   - birdeye.token_security(ca, chain) 
   - birdeye.token_creation_info(ca, chain)
   - birdeye.token_holders(ca, limit=20, chain=chain)
   - bundle.detect_bundle(ca, chain, birdeye)
4. Once token_creation_info returns, extract deployer wallet, then call dev_history.get_deployer_profile(deployer, chain)
5. Pass everything to scorer.score_dossier() → (score, band)
6. Build raw_signals dict
7. Call verdict.generate_verdict(raw_signals, score, band) → verdict text
8. Build final Dossier model
9. Cache final dossier in Redis at "dossier:{chain}:{ca}" with TTL 300
10. Return dossier

Wire it into backend/app/main.py via APIRouter.

Run the acceptance test from SPEC-002:
curl -s http://localhost:8000/dossier/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263?chain=solana | jq

Paste the response. It must have: ca, chain, generated_at, score (0-100), band (AVOID|CAUTION|CLEAR), overview, security, deployer, distribution, verdict (non-empty string).

Time the response. Cold cache should be <3s. Run again — cached should be <100ms.
```

**Review checklist:**
- [ ] Endpoint returns valid Dossier JSON for $BONK
- [ ] All 5 sections populated (or null with reason)
- [ ] Score is reasonable for $BONK (should be CLEAR or CAUTION)
- [ ] Verdict is punchy and reflects the data
- [ ] Cold response <3s, cached <100ms

---

## Prompt 1.8 — Deploy backend to Railway

**Run with:** Codex (or do it manually — Railway's UI is fine)

```
Deploy the FastAPI backend to Railway:

1. Generate a Railway-compatible startup: ensure backend/Procfile exists with: web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
2. Verify backend/railway.json has correct config
3. Commit all changes, push to GitHub
4. Walk me through the Railway UI steps to deploy from GitHub:
   - Create new project from repo
   - Set root directory to backend/
   - Add all env vars from .env.example
   - Deploy
5. After deploy, test: curl https://<railway-url>/health
6. Test: curl https://<railway-url>/dossier/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263

If both work, we have a live backend. Print the Railway URL.
```

**End of Day 1 deliverable:**
- ✅ Live backend at `<something>.railway.app/dossier/{ca}` returning real dossiers
- ✅ ~6 working endpoints
- ✅ Dev history index populated with 30 days of Solana launches
- ✅ AI verdicts generating in the brand voice

**Day 1 EOD tweet (post this):**

> Day 1 of building TRENCHCOAT — exposing serial ruggers on Solana with @birdeye_data.
>
> API live. Pasted $LIBRA → got the full dev rap sheet in 2 seconds.
>
> [screenshot of JSON response]
>
> Frontend tomorrow. #BirdeyeAPI

---

# DAY 2 — FRONTEND + AI POLISH

## Prompt 2.1 — Frontend scaffold + design system

**Run with:** Codex (working directory = `frontend/`)

```
Read PROJECT_CONTEXT.md and SPECS.md SPEC-007 fully.

Initialize a Next.js 14 App Router project in this directory if not already done. Set up:
1. TypeScript strict mode
2. Tailwind CSS with custom theme matching the color tokens in SPEC-007 (background #0a0a0a, card #171717, text #f5f5f5, red #ef4444, yellow #eab308, green #22c55e)
3. shadcn/ui — install and configure with: card, badge, separator, button, input, skeleton
4. JetBrains Mono or IBM Plex Mono as the mono font
5. Inter or Geist as the body font
6. A dark-by-default theme (no theme toggle in v1)
7. Create frontend/lib/api.ts with a typed fetch helper that hits the backend (read NEXT_PUBLIC_API_URL from env)

Do not write the page components yet. Just the foundation.

After this: print the tailwind.config.ts and globals.css. I'll verify the colors before we build pages.
```

**Review checklist:**
- [ ] Tailwind config has the 6 brand colors
- [ ] shadcn components installed
- [ ] Mono font working
- [ ] api.ts handles errors and returns typed responses

---

## Prompt 2.2 — Landing page + paste hero

**Run with:** Codex

```
Read SPEC-007 fully.

Build:
1. frontend/app/page.tsx — landing page
2. frontend/components/PasteHero.tsx — the input
3. frontend/components/ChainSelector.tsx — dropdown for solana/base/ethereum
4. frontend/app/layout.tsx — wraps with the dark theme, fonts, metadata

Landing page sections:
- Hero: massive "TRENCHCOAT" wordmark in mono, off-white on near-black
- Subhead: "Paste a token. Know who's behind it before you lose your money."
- Big paste input — full width on mobile, max-w-2xl on desktop
- Chain selector to the left of input
- Submit button on the right (says "RUN" in mono)
- On submit: navigate to /dossier/{ca}?chain={chain}
- Below the fold: "How it works" — 3 cards in a grid:
  1. "DEV BACKGROUND CHECK — Every prior token they shipped, and how each one ended."
  2. "BUNDLE DETECTION — Spots coordinated launch buys before you ape into a trap."
  3. "AI VERDICT — Plain-English read on whether this thing has any chance."
- Footer: "Built with Birdeye Data. Not financial advice." + GitHub icon link

Validate CA format on submit:
- Solana: 32-44 base58 chars
- EVM: 0x + 40 hex chars

If invalid, shake the input and show "Invalid contract address" below.

Make it look like a noir terminal. Lots of negative space. Mono numbers. Strong typography hierarchy. Don't add unnecessary illustrations or stock SVGs.
```

**Review checklist:**
- [ ] Landing renders cleanly at desktop (1440px), tablet (768px), mobile (375px)
- [ ] Paste flow works end-to-end (paste a CA, lands on a dossier page)
- [ ] Validation rejects garbage inputs
- [ ] Brand voice in copy ("RUN" not "Submit", terse subheads)

---

## Prompt 2.3 — RapSheet component + dossier page

**Run with:** Codex

```
Read SPEC-007 fully, especially the RapSheet component requirements.

Build:
1. frontend/components/RapSheet.tsx — the main artifact. Renders the full Dossier as a card with 5 sections:
   - Header (ticker, score big, band badge, generated_at relative time)
   - The Dev (wallet, prior tokens list with mini status badges)
   - Supply Distribution (bundle %, top10 %, simple horizontal bar chart)
   - Token Security (mint/freeze/liquidity icons green/red)
   - AI Verdict (large quote-style text, italic mono)
2. frontend/app/dossier/[ca]/page.tsx — server component, fetches the dossier from FastAPI on render
3. frontend/components/RapSheetSkeleton.tsx — shimmer loading state
4. frontend/app/dossier/[ca]/error.tsx — error boundary with retry button

Page-level behaviors:
- Set <title> to "$SYMBOL — TRENCHCOAT Rap Sheet"
- Open Graph metadata: og:title, og:description (the verdict), og:image=/api/og/{ca}
- Cache page with revalidate: 300

Visual details:
- Score is huge — 96px font, mono
- Band badge: rounded pill, AVOID red bg, CAUTION yellow bg, CLEAR green bg, all with white text
- Prior tokens list: each one is a row with ticker + outcome badge + age. Hover shows the CA
- Wallet addresses: monospace, truncated middle (9xK2...4mPq), copy-to-clipboard on click
- Verdict: italic, larger font, indented with a left border in the band color

Build it. Test by visiting /dossier/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263?chain=solana.

Run Lighthouse on the deployed page. Score must be >85 on Performance.
```

**Review checklist:**
- [ ] All 5 sections render with real backend data
- [ ] Score and band visually pop
- [ ] Mobile layout doesn't break
- [ ] Loading state shimmers, doesn't jump
- [ ] Error state has a retry that actually works
- [ ] OG metadata renders correctly (test with OpenGraph debugger)

---

## Prompt 2.4 — OG image generator (SPEC-008)

**Run with:** Codex

```
Read SPEC-008 fully.

Build frontend/app/api/og/[ca]/route.tsx using Next.js ImageResponse from next/og.

Generate a 1200x630 PNG with:
- Black background (#0a0a0a)
- Top-left: TRENCHCOAT wordmark, mono, off-white
- Center: token symbol huge ($XXXXX), score below it (e.g., "18 / 100")
- Below: band badge (AVOID/CAUTION/CLEAR) in the band color, all caps
- Below that: 3-line summary of top signals — pick the 3 worst signals from the dossier dynamically
- Bottom-right: your production Vercel URL, small mono

To generate the OG, the route fetches the dossier from the backend on the fly and renders the image with the data.

Set Cache-Control: public, max-age=300, stale-while-revalidate=86400

Test:
1. Hit /api/og/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263 directly — should download a PNG
2. Tweet a dossier link from a test account, verify the preview shows the custom image
3. Test in https://www.opengraph.xyz/

Use the @vercel/og package. Use Tailwind-style inline styles within ImageResponse since CSS classes don't work there.
```

**Review checklist:**
- [ ] OG endpoint returns a 1200x630 PNG
- [ ] Image has all the brand elements
- [ ] X/Twitter preview renders correctly when sharing
- [ ] Different CAs produce visibly different images

---

## Prompt 2.5 — Deploy frontend + connect production URL

**Run with:** You + Codex assisting

```
Deploy frontend to Vercel:

1. Push frontend code to GitHub (in same repo, or separate — your call)
2. Import to Vercel from GitHub
3. Set root directory to frontend/
4. Set env var NEXT_PUBLIC_API_URL to the Railway backend URL
5. Deploy

Use the Vercel production URL:
1. Open the production deployment in Vercel
2. Note the stable production URL, for example `https://<your-vercel-url>.vercel.app`
3. Verify that URL loads the landing

Preview URL note:
- Every push to GitHub can generate a new preview URL like `trenchcoat-abc123.vercel.app`.
- Do not share preview URLs in tweets; they are temporary and can break.
- Share only the stable production deployment URL from Vercel.

Update backend CORS:
- Set ALLOWED_ORIGINS=https://<your-vercel-url>.vercel.app,http://localhost:3000 in Railway env
- Restart backend

Smoke test full flow:
- Visit https://<your-vercel-url>.vercel.app
- Paste $TRUMP CA
- Verify dossier renders with real data
- Tweet the dossier URL from a test account
- Verify OG preview is correct
```

**End of Day 2 deliverable:**
- ✅ Vercel production URL live with full paste-to-dossier flow
- ✅ Beautiful Rap Sheet rendering
- ✅ OG images on share
- ✅ Backend stable

**Day 2 EOD tweet — THE VIRAL ONE (the moneymaker):**

> We pointed TRENCHCOAT at the top 10 trending Solana tokens right now.
>
> 7 of 10 have red flags. Thread 🧵 (1/10)
>
> [first dossier screenshot]
>
> Built with @birdeye_data #BirdeyeAPI · <production-vercel-url>

Then quote-tweet 9 more times, one per token. Each with a screenshot of that token's Rap Sheet.

---

# DAY 3 — TELEGRAM BOT, TRENDING, POLISH, CAMPAIGN

## Prompt 3.1 — Telegram bot (SPEC-009)

**Run with:** Codex (working directory = `telegram-bot/`)

```
Read SPEC-009 fully.

Build telegram-bot/bot.py using python-telegram-bot library (v21+).

Commands:
- /start — welcome message with brand voice
- /rap <ca> or any message containing a base58 CA — fetch dossier from backend, reply with formatted Markdown
- /help — show commands
- Inline button "View full Rap Sheet →" links to https://<your-vercel-url>.vercel.app/dossier/{ca}

Behaviors:
- CA detection regex: 32-44 chars of base58 (Solana). Also detect 0x+40hex (EVM).
- "🔍 Scanning..." reply, then edit-in-place when ready
- Rate limit: 5 raps per user per minute (use a simple in-memory dict)
- Use python-telegram-bot's ApplicationBuilder pattern
- Set webhook on startup if WEBHOOK_URL env var is set, else use polling

Format the reply matching the Markdown shown in SPEC-009 exactly.

Create telegram-bot/requirements.txt: python-telegram-bot[webhooks], httpx
Create telegram-bot/railway.json for Railway deploy
Create telegram-bot/.env.example: TELEGRAM_BOT_TOKEN, BACKEND_URL, WEBHOOK_URL (optional)

Get a bot token: instruct me to message @BotFather on Telegram, run /newbot, name it "TRENCHCOAT Bot" with handle @trenchcoatbot. Save the token.

Deploy to Railway as a separate service from the backend.

Test: open Telegram, message your bot, send "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263". Verify formatted Rap Sheet returns within 5s.
```

**Review checklist:**
- [ ] Bot responds to a CA paste with a formatted Rap Sheet
- [ ] /start, /help work
- [ ] Rate limiting kicks in on 6th call within a minute
- [ ] Inline button opens the Vercel production URL correctly

---

## Prompt 3.2 — Trending feed page (SPEC-010)

**Run with:** Codex

```
Read SPEC-010 fully.

Backend: add GET /trending?chain=solana&limit=20 to backend/app/api/. 

Implementation:
- Calls birdeye.token_trending(limit=20, chain=chain)
- For each trending token, builds a "mini dossier" — just runs scorer + a fast subset (overview + security only, skip dev_history and bundle for speed)
- Returns array of: {ca, symbol, score, band, top_signal_text}
- Caches result in Redis "trending:{chain}" with TTL 300s

Frontend: build frontend/app/trending/page.tsx

Layout:
- 4-column responsive grid (1 col mobile, 2 col tablet, 4 col desktop)
- Each card: ticker top, score huge in middle, band badge, one-line top signal, CTA "Open Rap Sheet"
- Sort dropdown: by score asc, by score desc, by trending rank (default)
- Auto-refresh every 60s (use a simple setInterval + revalidate)

Add "TRENDING" link to landing page nav.

Deploy. Test /trending loads in <2s with 20 cards.
```

**Review checklist:**
- [ ] /trending shows 20 real tokens
- [ ] Each card clickable, opens full dossier
- [ ] Sort works
- [ ] Auto-refresh updates without flicker

---

## Prompt 3.3 — Demo video script + recording

**Run with:** You (no agent for this)

This isn't a code task. Record a 60-second screen capture using Loom or QuickTime + iMovie.

**Script:**

```
[0-3s] TRENCHCOAT logo, voiceover: "Every degen knows the pain. You ape, you get rugged, you swore you'd check next time."

[3-10s] Show landing page. Voiceover: "TRENCHCOAT pulls the dev's full rap sheet in three seconds."

[10-20s] Paste a known rugger's token. Watch the Rap Sheet render. Highlight the prior rugs section. Voiceover: "Same wallet shipped four tokens. All four zeros. This makes five."

[20-32s] Paste a clean token. Show contrast. Voiceover: "Real ones look like this. Mint revoked, even distribution, deployer with no priors."

[32-45s] Switch to Telegram. DM the bot. Show instant reply. Voiceover: "Wherever you trade, TRENCHCOAT goes with you."

[45-55s] Show /trending page. Voiceover: "Live feed of every trending token, scored automatically."

[55-60s] End card: production Vercel URL + GitHub URL + #BirdeyeAPI. Voiceover: "Built with Birdeye Data. Three days. Open source."
```

Edit. Add captions (people watch muted on X). Upload native to X (better algo).

---

## Prompt 3.4 — README polish + final submission

**Run with:** Codex

```
Update README.md to be a strong public face for the project. Sections:

1. **Hero** — TRENCHCOAT logo (use ASCII art), tagline, one-line description
2. **Live demo** — link to the Vercel production URL, badge image
3. **Demo video** — embed YouTube link
4. **What it does** — bullet list of features (paste-to-dossier, dev history, bundle detection, AI verdict, Telegram bot, trending feed, multi-chain ready)
5. **Architecture diagram** — ASCII or Mermaid showing the system
6. **Birdeye endpoints used** — list with brief description of each
7. **Tech stack** — table
8. **Local development** — clone, .env setup, running backend + frontend + bot
9. **Project structure** — directory tree
10. **Roadmap** — what's next (Base, Ethereum chains; Chrome extension; subscription alerts)
11. **Built with @birdeye_data #BirdeyeAPI** credit
12. **License** — MIT

Make the diagrams clear and the writing tight. This README is part of the Presentation score.
```

**Final submission steps:**

1. Verify the Vercel production URL loads cleanly on a fresh browser
2. Run a final end-to-end test: paste 3 different CAs, all return dossiers
3. Verify Telegram bot still responds
4. Verify GitHub repo is public, README is rendered
5. Submit to Superteam Earn:
   - Project name: TRENCHCOAT
   - GitHub: https://github.com/<your-username>/trenchcoat
   - Live URL: https://<your-vercel-url>.vercel.app
   - X campaign link: pinned tweet on your profile
   - Description (200 words max): see "Submission Description" template below

---

## Submission description template

```
TRENCHCOAT is the rap sheet for token deployers. Paste any Solana CA and get a forensic dossier in 3 seconds — every prior token the dev shipped, every one that rugged, who's bundled in early, and an AI verdict in plain English.

Built solo in 3 days for the Birdeye BIP Sprint 3.

What's under the hood:
• 7 Birdeye endpoints stitched together: token_overview, token_security, token_creation_info, token_holders, txs/token, token_trending, new_listing
• Custom dev-wallet history index seeded from 30 days of new listings
• Bundle detection algorithm — flags coordinated launch-window buys
• Risk scorer (0-100) with three bands: AVOID / CAUTION / CLEAR
• Claude API for the AI verdict layer

Three surfaces:
1. Vercel production URL — paste a token, get the rap sheet
2. @trenchcoatbot on Telegram — DM a CA, get the rap sheet in chat
3. /trending — live feed of trending tokens with scores

Multi-chain ready (architecture supports Solana + Base + Ethereum via Birdeye's unified API).

GitHub (open source): https://github.com/<you>/trenchcoat
Demo video: <youtube link>
X campaign: <pinned tweet link>

Built with @birdeye_data. #BirdeyeAPI
```

---

# X CONTENT CALENDAR — pre-written tweets

## Day 1 morning (build-in-public teaser)

> 3 days. Solo. Building something that exposes serial ruggers on Solana.
>
> Paste a token, see every prior token the dev shipped — and how each one ended.
>
> Powered by @birdeye_data. Going live by Friday.
>
> #BirdeyeAPI #buildinpublic

## Day 1 EOD (proof of life)

> Day 1 update.
>
> Backend live. Pointed it at $LIBRA — full dev rap sheet in 2 seconds.
>
> [JSON screenshot]
>
> 7 @birdeye_data endpoints stitched + a custom dev-history index. UI tomorrow.
>
> #BirdeyeAPI

## Day 2 midday — THE VIRAL ONE

> We pointed TRENCHCOAT at the top 10 trending Solana tokens right now.
>
> 7 of 10 have red flags 🧵 (1/10)
>
> $TICKER1 → AVOID. Same dev shipped 4 prior tokens. All zeros.
> [Rap Sheet screenshot]
>
> Powered by @birdeye_data #BirdeyeAPI · <production-vercel-url>

Then quote-tweet 9 more times, one per token. Vary the phrasing on the verdict line for each.

## Day 2 EOD (link drop)

> <production-vercel-url> is live.
>
> Paste any Solana token. See who's behind it. Free, no signup.
>
> Built with @birdeye_data in 48 hours. #BirdeyeAPI
>
> [demo gif or screenshot]

## Day 3 morning (retrospective post — high engagement)

> What if TRENCHCOAT existed before $LIBRA?
>
> Here's what it would have shown you 24h before the rug:
>
> [Rap Sheet screenshot showing the warning signs]
>
> Real on-chain data, retrieved retroactively. The signals were there.
>
> <production-vercel-url> · @birdeye_data #BirdeyeAPI

## Day 3 afternoon (demo video drop)

> 60 seconds. Watch TRENCHCOAT rap-sheet a known scammer in real time.
>
> [native video]
>
> Built solo in 3 days with @birdeye_data. Fully open source.
>
> <production-vercel-url> · github.com/you/trenchcoat · #BirdeyeAPI

## Day 3 evening (submission tweet)

> Submitted TRENCHCOAT to the @birdeye_data BIP Sprint 3.
>
> 3 days. 1 dev. 7 endpoints. ~3,000 lines of code. 200+ dossiers generated in the last 24h.
>
> Whatever happens with the contest, this thing is staying live.
>
> <production-vercel-url> · #BirdeyeAPI

---

# REVIEW PROTOCOL (use after every Codex run)

After Codex finishes a prompt:

1. **Read the diff.** Don't trust, verify.
2. **Run the acceptance test** the prompt specified.
3. **Hit the real API endpoint** if it's a backend change. Use curl. Print the response. Look at it.
4. **Check git diff** for files you didn't expect to change. Codex sometimes "fixes" things you didn't ask for.
5. **If something is broken, take ONE shot at fixing with Claude Code.** Prompt: *"This isn't working: [paste error]. Read [relevant files] and fix without changing scope."*
6. **If still broken after 1 fix attempt, simplify the spec.** Don't sink 2 hours into a bug. Cut the feature.

---

# WHEN TO ASK ME (the human / project lead)

Stop the agent and check with me when:

- Birdeye returns a response shape that doesn't match BIRDEYE_REFERENCE.md
- An acceptance test takes >3 attempts to pass
- The agent suggests adding a dependency not in the approved stack
- Something in PROJECT_CONTEXT.md feels wrong or outdated
- You hit a real-world security thing (API key leaked, CORS open to *, etc.)
- Time is slipping vs the 3-day plan — better to cut scope than push deadline

---

That's the kit. Read it once end-to-end before starting. Then begin with Prompt 1.1.

Good hunting. 🕵️
