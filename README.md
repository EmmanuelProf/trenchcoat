# TRENCHCOAT

Paste a token. Know who's behind it before you lose your money.

TRENCHCOAT is a trading copilot that exposes serial token ruggers by checking a token deployer's wallet history, launch distribution, security posture, and on-chain signals before you buy.

## Demo

Live demo: `https://<your-vercel-url>.vercel.app`

[![Built with Birdeye Data](https://img.shields.io/badge/Built%20with-Birdeye%20Data-0a0a0a)](https://birdeye.so/)

## Stack

- FastAPI backend on Railway
- Next.js 14 frontend on Vercel
- Supabase Postgres for deployer history
- Upstash Redis for caching
- Birdeye Data Services API for token intelligence
- Claude API for verdict writing

## Status

Scaffolded for the Birdeye Data 4-Week BIP Competition Sprint 3.
