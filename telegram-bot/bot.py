import json
import os
import re
import urllib.request
from collections import defaultdict, deque
from time import monotonic

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SOLANA_CA = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,50}$")
EVM_CA = re.compile(r"^0x[a-fA-F0-9]{40}$")
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 3
user_requests: dict[int, deque[float]] = defaultdict(deque)


def is_valid_ca(value: str) -> bool:
    return bool(SOLANA_CA.fullmatch(value) or EVM_CA.fullmatch(value))


def truncate_wallet(wallet: str | None) -> str:
    if not wallet or wallet == "unknown" or len(wallet) <= 8:
        return wallet or "unknown"
    return f"{wallet[:4]}...{wallet[-4:]}"


def band_emoji(band: str) -> str:
    if band == "AVOID":
        return "🔴"
    if band == "CAUTION":
        return "🟡"
    if band == "CLEAR":
        return "🟢"
    return "⚪"


def check_rate_limit(user_id: int) -> bool:
    now = monotonic()
    requests = user_requests[user_id]
    while requests and now - requests[0] > RATE_LIMIT_WINDOW_SECONDS:
        requests.popleft()
    if len(requests) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    requests.append(now)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Paste a token contract address and I will pull its TRENCHCOAT rap sheet."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    ca = (update.message.text or "").strip()
    if not is_valid_ca(ca):
        await update.message.reply_text("Invalid contract address.")
        return

    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("Slow down. 3 raps per minute max.")
        return

    chain = "ethereum" if ca.startswith("0x") else "solana"
    loading = await update.message.reply_text("SCANNING...")

    try:
        dossier = fetch_dossier(ca, chain)
        await loading.edit_text(format_dossier(dossier))
    except Exception:
        await loading.edit_text("Couldn't pull data on this one.")


def fetch_dossier(ca: str, chain: str = "solana") -> dict:
    backend_url = os.getenv("BACKEND_URL", "https://trenchcoat.onrender.com")
    url = f"{backend_url}/dossier/{ca}?chain={chain}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def format_dossier(dossier: dict) -> str:
    overview = dossier.get("overview") or {}
    deployer = dossier.get("deployer") or {}
    distribution = dossier.get("distribution") or {}
    bundle = distribution.get("bundle") or {}

    symbol = overview.get("symbol") or "UNKNOWN"
    band = dossier.get("band") or "UNKNOWN"
    score = dossier.get("score", "?")
    verdict = dossier.get("verdict") or "No verdict."
    wallet = truncate_wallet(deployer.get("wallet"))
    prior_count = deployer.get("prior_count", 0)
    rugged_count = deployer.get("rugged_count", 0)
    bundle_pct = bundle.get("bundle_pct", distribution.get("bundle_pct"))
    top10_pct = distribution.get("top10_pct")

    bundle_text = f"{bundle_pct:.1f}%" if isinstance(bundle_pct, (int, float)) else "unknown"
    top10_text = f"{top10_pct:.1f}%" if isinstance(top10_pct, (int, float)) else "unknown"

    return "\n".join(
        [
            f"{band_emoji(band)} ${symbol} — {band}",
            f"Score: {score}/100",
            "",
            f"Verdict: {verdict}",
            "",
            f"Dev: {wallet}",
            f"Prior tokens: {prior_count}",
            f"Rugged: {rugged_count}",
            f"Bundle: {bundle_text}",
            f"Top 10: {top10_text}",
            "",
            f"CA: {dossier.get('ca', 'unknown')}",
        ]
    )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


if __name__ == "__main__":
    main()
