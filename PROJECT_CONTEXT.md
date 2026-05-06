# PROJECT_CONTEXT.md

> **Read this entire file at the start of every session.** When you're about to make an architectural decision, check here first. When this file contradicts your instinct, this file wins.

## What we're building

**TRENCHCOAT** — a trading copilot that exposes serial token ruggers on Solana (and later Base/Ethereum) by checking the deployer's wallet history before you buy. Paste a token contract address, get a "Rap Sheet" in under 3 seconds.

Tagline: *"Paste a token. Know who's behind it before you lose your money."*

## Why we're building it

We're competing in the **Birdeye Data 4-Week BIP Competition Sprint 3** ($500 USDC + API credits). Submission deadline: **May 9, 2026**. Judging: Community Support (X engagement) + Product Utility + Technical Depth + Presentation. Winning the contest is the goal. Everything else is a non-goal.

## Hard constraints

- **3-day build window** (May 7-9, 2026). Solo developer. No scope creep.
- **Must hit minimum 50 Birdeye API calls** during the sprint to qualify. Trivial to hit.
- **Must use Birdeye Data Services API** (`bds.birdeye.so`) as the primary data source.
- **Must be open-source** on GitHub for the Presentation score.
- **Public live URL** must be accessible at submission time.

## Stack — non-negotiable

| Layer | Tech | Why |
|---|---|---|
| Backend API | FastAPI (Python 3.11) | Fast to write, async-native, easy deploys |
| Backend host | Railway | Easiest Python deploy, free tier sufficient |
| Frontend | Next.js 14 App Router + TypeScript | Vercel deploys in seconds, OG image gen |
| Frontend host | Vercel | One-click, production URL works immediately |
| UI components | Tailwind + shadcn/ui | Fast to build polished UI |
| Database | Supabase (Postgres) | Free tier, simple client |
| Cache | Upstash Redis | Free tier, REST API works from anywhere |
| AI verdict | Anthropic Claude API (claude-sonnet-4-5 or claude-haiku-4-5) | Punchy verdict writing |
| Telegram bot | python-telegram-bot library | Same Python ecosystem as backend |
| Domain | trenchcoat.vercel.app | Vercel default |

**DO NOT** suggest alternatives to this stack unless explicitly asked. No Postgres self-host, no Vercel functions for the backend, no Solana RPC direct calls (we use Birdeye exclusively), no Drizzle/Prisma (Supabase client is fine).

## Architecture

```
┌──────────────────────┐         ┌──────────────────────┐
│  Next.js (Vercel)    │ ──HTTP──▶  FastAPI (Railway)   │
│  <your-app>.vercel.app │       │  <your-backend>.railway.app │
└──────────────────────┘         └─────────┬────────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                    ┌─────▼─────┐    ┌────▼─────┐    ┌─────▼─────┐
                    │ Birdeye   │    │ Supabase │    │ Upstash   │
                    │   API     │    │ Postgres │    │   Redis   │
                    └───────────┘    └──────────┘    └───────────┘

┌──────────────────────┐
│ Telegram Bot         │ ──HTTP──▶ Same FastAPI
│ (Railway, separate)  │
└──────────────────────┘
```

The **same FastAPI backend** powers both the web UI and the Telegram bot. Don't duplicate logic.

## Repository structure

```
trenchcoat/
├── PROJECT_CONTEXT.md          # This file
├── SPECS.md                    # Feature specs (read per-task)
├── BIRDEYE_REFERENCE.md        # Real Birdeye endpoint documentation
├── README.md                   # Public-facing
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── dossier.py
│   │   ├── services/
│   │   │   ├── birdeye.py
│   │   │   ├── bundle.py
│   │   │   ├── dev_history.py
│   │   │   ├── scorer.py
│   │   │   └── verdict.py
│   │   ├── models/
│   │   │   └── dossier.py
│   │   └── db/
│   │       ├── supabase.py
│   │       └── redis_client.py
│   ├── scripts/
│   │   └── bootstrap_dev_history.py
│   ├── requirements.txt
│   ├── railway.json
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── dossier/[ca]/page.tsx
│   │   └── api/og/[ca]/route.tsx
│   ├── components/
│   │   ├── RapSheet.tsx
│   │   ├── PasteHero.tsx
│   │   ├── ChainSelector.tsx
│   │   └── ui/             # shadcn components
│   ├── lib/
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── package.json
│   └── tailwind.config.ts
└── telegram-bot/
    ├── bot.py
    ├── requirements.txt
    └── railway.json
```

## Naming conventions

- **Python:** snake_case files, snake_case functions, PascalCase classes, SCREAMING_SNAKE for constants
- **TypeScript:** camelCase functions, PascalCase components and types, kebab-case for routes
- **Branding:** Always "TRENCHCOAT" (all caps) in user-facing copy. Lowercase `trenchcoat` in code, package names, URLs.
- **Verdict bands:** `AVOID` (red, score 0-30), `CAUTION` (yellow, score 31-60), `CLEAR` (green, score 61-100)

## Brand voice

Direct, slightly menacing, knowing. Like a noir detective who's seen too many rugs. Examples of *good* verdict copy:

- "Same wallet's deployed three tokens. All three are zeros. This makes four."
- "72% of supply in ten wallets. Mint authority still alive. You know the rest."
- "Clean deployer, locked liquidity, even holder distribution. Rare. Could actually be real."

Examples of *bad* verdict copy (do not write like this):

- "This token shows several risk indicators that you should consider..."
- "Our analysis suggests caution is warranted..."
- "Multiple metrics indicate elevated risk levels..."

Punchy. Specific. Numbers > adjectives. Never use the words "leverage," "synergy," "ecosystem," or "robust."

## What we ARE building

- Web app at the Vercel production URL: paste CA → render Rap Sheet
- Trending feed page: top 20 tokens with mini Rap Sheets
- Telegram bot: `/rap CA` returns Rap Sheet as text
- AI verdict layer powered by Claude API
- Dev history index seeded from past 30 days of new listings
- Bundle detection algorithm (early-buyer concentration in same block range)
- Dynamic OG images so dossier links share beautifully on X
- Multi-chain support: Solana primary, Base added day 3

## What we are NOT building

- Wallet connection / sign-in / accounts (we're stateless v1)
- Trading execution (we're advisory only)
- Real-time websockets (5-min Redis cache is plenty)
- Mobile app
- Chrome extension (cut from scope due to solo time constraints)
- Subscription system / payments / pro tier
- KOL tracking with social media scraping (use only Birdeye-derived signals)
- Anything that requires storing user PII

## Birdeye API key facts

- Base URL: `https://public-api.birdeye.so`
- Auth header: `X-API-KEY: <key>`
- Chain header: `x-chain: solana` (or `base`, `ethereum`, etc.)
- Free tier: 30K compute units/month — more than enough for the sprint
- **Always parameterize the chain.** Never hardcode "solana" anywhere.
- Always retry 429s with exponential backoff
- Always cache responses in Redis with 5-min TTL keyed by `{endpoint}:{chain}:{address}`

**For exact endpoint paths, parameters, and response shapes, see `BIRDEYE_REFERENCE.md`. Do not guess endpoints from memory.**

## Caching strategy (mandatory)

- Every external API call goes through `redis_cache_or_fetch(key, ttl, fetcher)` helper
- Default TTL: 300s (5 min)
- Dev history index entries: 7 days (prior token outcomes change slowly)
- Cache stampede protection: use a lock key during fetch
- On cache miss, fetch, write to cache, return

## Error handling philosophy

- **Never silently fall back to fake data.** If Birdeye returns an error, the dossier shows that section as "data unavailable" — don't fabricate.
- The AI verdict is allowed to say "insufficient data" if signals are missing.
- Frontend always shows a structured error state. No spinners that spin forever.

## Sequencing principle

Each task produces a **verifiable artifact** before moving on. We don't write Day 2 code until Day 1's endpoint returns real Birdeye data in production. This is non-negotiable for solo speed.

## Definition of done (for any feature)

1. Code written
2. **Tested against real Birdeye API** with a real Solana CA (use $TRUMP `6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN` or any active token as test CA)
3. Deployed to Railway/Vercel
4. Smoke-tested via curl or browser
5. Committed to git with a clear message

If any of those 5 isn't done, the feature isn't done.

## When in doubt

- Cut scope, don't add complexity
- Ship something ugly that works > something beautiful that doesn't
- Prefer hardcoded values over config systems for v1
- Prefer raw SQL over ORMs
- Prefer one big file over premature abstraction

## Test CAs (use these for development)

- **$TRUMP** (Solana): `6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN` — known controversial, good demo
- **$BONK** (Solana): `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263` — established, should score CLEAR
- **$WIF** (Solana): `EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm` — established memecoin

Always test with at least one known scam CA and one known clean CA before declaring a feature done.
