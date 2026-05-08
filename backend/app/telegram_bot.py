import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from html import escape

from dotenv import load_dotenv
from fastapi import APIRouter, Request

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "https://trenchcoat.onrender.com").rstrip("/")
BASE = f"https://api.telegram.org/bot{TOKEN}"

SOLANA_CA = __import__("re").compile(r"[1-9A-HJ-NP-Za-km-z]{32,50}")
rate_limits = {}
router = APIRouter()


def api_call(method, data=None):
    url = f"{BASE}/{method}"
    if data:
        payload = json.dumps(data).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"Telegram API error method={method} status={e.code} body={body}")
        raise


def send_message(chat_id, text, parse_mode="Markdown"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return api_call("sendMessage", payload)


def edit_message(chat_id, message_id, text, parse_mode="Markdown"):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return api_call("editMessageText", payload)


def get_me():
    return api_call("getMe")


def delete_webhook():
    return api_call("deleteWebhook", {"drop_pending_updates": False})


def set_webhook():
    webhook_url = f"{BACKEND_URL}/telegram/webhook"
    return api_call("setWebhook", {"url": webhook_url, "drop_pending_updates": True})


def configure_webhook():
    if not TOKEN:
        print("No TELEGRAM_BOT_TOKEN found, skipping Telegram webhook")
        return

    print("Configuring Telegram webhook...")
    print(f"Telegram backend URL: {BACKEND_URL}")
    try:
        me = get_me()
        username = ((me.get("result") or {}).get("username")) or "unknown"
        print(f"Telegram bot identity: @{username}")
    except Exception as e:
        print(f"Telegram getMe failed: {e}")

    try:
        webhook_result = set_webhook()
        print(f"Telegram webhook set: {webhook_result.get('ok')}")
    except Exception as e:
        print(f"Telegram setWebhook failed: {e}")


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    message = update.get("message")
    if message and "text" in message:
        threading.Thread(target=handle_message, args=(message,), daemon=True).start()
    return {"ok": True}


def fetch_dossier(ca):
    encoded_ca = urllib.parse.quote(ca, safe="")
    url = f"{BACKEND_URL}/dossier/{encoded_ca}?chain=solana"
    print(f"Fetching dossier from {url}")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"Backend dossier error status={e.code} body={body}")
        raise


def format_dossier(dossier, ca):
    band = dossier.get("band", "UNKNOWN")
    score = dossier.get("score", 0)
    overview = dossier.get("overview") or {}
    symbol = overview.get("symbol", "UNKNOWN")
    name = overview.get("name")
    liquidity = overview.get("liquidity")
    market_cap = overview.get("mc")
    age_days = overview.get("age_days")
    deployer = dossier.get("deployer") or {}
    wallet = deployer.get("wallet", "unknown")
    prior_count = deployer.get("prior_count", 0)
    rugged_count = deployer.get("rugged_count", 0)
    distribution = dossier.get("distribution") or {}
    bundle = distribution.get("bundle") or {}
    bundle_pct = bundle.get("bundle_pct", distribution.get("bundle_pct"))
    top10_pct = distribution.get("top10_pct")
    verdict = dossier.get("verdict") or "No verdict."

    emoji = band_emoji(band)
    action = band_action(band)
    wallet_short = truncate_wallet(wallet)
    bundle_text = format_pct(bundle_pct)
    top10_text = format_pct(top10_pct)
    liquidity_text = format_money(liquidity)
    market_cap_text = format_money(market_cap)
    age_text = format_age(age_days)
    score_bar = make_score_bar(score)
    symbol_text = escape(str(symbol))
    name_text = f" · {escape(str(name))}" if name else ""
    verdict_text = escape(str(verdict))
    ca_text = escape(ca)
    wallet_text = escape(wallet_short)
    solscan_url = f"https://solscan.io/token/{ca}"
    rugcheck_url = f"https://rugcheck.xyz/tokens/{ca}"

    return "\n".join(
        [
            f"{emoji} <b>TRENCHCOAT RAP SHEET</b>",
            f"<b>${symbol_text}</b>{name_text}",
            "",
            f"<b>{action}</b>  ·  <b>{band}</b>",
            f"<code>{score_bar}</code>  <b>{score}/100</b>",
            "",
            "<b>VERDICT</b>",
            f"<i>{verdict_text}</i>",
            "",
            "<b>DEV FILE</b>",
            f"Wallet: <code>{wallet_text}</code>",
            f"Prior tokens: <b>{prior_count}</b>",
            f"Rugged: <b>{rugged_count}</b>",
            "",
            "<b>SUPPLY / MARKET</b>",
            f"Bundle: <b>{bundle_text}</b>",
            f"Top 10: <b>{top10_text}</b>",
            f"Liquidity: <b>{liquidity_text}</b>",
            f"Market cap: <b>{market_cap_text}</b>",
            f"Age: <b>{age_text}</b>",
            "",
            "<b>CHECKS</b>",
            f'<a href="{solscan_url}">Solscan</a>  |  <a href="{rugcheck_url}">RugCheck</a>',
            "",
            f"CA: <code>{ca_text}</code>",
        ]
    )


def format_plain_dossier(dossier, ca):
    band = dossier.get("band", "UNKNOWN")
    score = dossier.get("score", 0)
    overview = dossier.get("overview") or {}
    symbol = overview.get("symbol", "UNKNOWN")
    deployer = dossier.get("deployer") or {}
    wallet = truncate_wallet(deployer.get("wallet", "unknown"))
    prior_count = deployer.get("prior_count", 0)
    rugged_count = deployer.get("rugged_count", 0)
    distribution = dossier.get("distribution") or {}
    bundle = distribution.get("bundle") or {}
    bundle_pct = format_pct(bundle.get("bundle_pct", distribution.get("bundle_pct")))
    top10_pct = format_pct(distribution.get("top10_pct"))
    verdict = dossier.get("verdict") or "No verdict."
    emoji = band_emoji(band)

    return "\n".join(
        [
            f"{emoji} TRENCHCOAT RAP SHEET",
            f"${symbol} - {band}",
            f"Score: {score}/100",
            "",
            f"Verdict: {verdict}",
            "",
            f"Dev: {wallet}",
            f"Prior tokens: {prior_count}",
            f"Rugged: {rugged_count}",
            f"Bundle: {bundle_pct}",
            f"Top 10: {top10_pct}",
            "",
            f"Solscan: https://solscan.io/token/{ca}",
            f"RugCheck: https://rugcheck.xyz/tokens/{ca}",
            "",
            f"CA: {ca}",
        ]
    )


def band_emoji(band):
    return {"AVOID": "\U0001f534", "CAUTION": "\U0001f7e1", "CLEAR": "\U0001f7e2"}.get(
        band,
        "\u26aa",
    )


def band_action(band):
    if band == "AVOID":
        return "DUMP"
    if band == "CLEAR":
        return "APE"
    if band == "CAUTION":
        return "CAUTION"
    return "UNKNOWN"


def make_score_bar(score):
    try:
        value = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        value = 0
    filled = round(value / 10)
    return "█" * filled + "░" * (10 - filled)


def format_pct(value):
    if isinstance(value, (int, float)):
        return f"{value:.1f}%"
    return "unknown"


def format_money(value):
    if not isinstance(value, (int, float)):
        return "unknown"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


def format_age(days):
    if not isinstance(days, (int, float)):
        return "unknown"
    if days < 1:
        return "< 1 day"
    if days < 30:
        return f"{int(days)} days"
    if days < 365:
        return f"{int(days / 30)} months"
    return f"{days / 365:.1f} years"


def truncate_wallet(wallet):
    if not wallet or wallet == "unknown" or len(wallet) <= 8:
        return wallet or "unknown"
    return f"{wallet[:4]}...{wallet[-4:]}"


def rate_limited(user_id):
    now = time.time()
    recent = [ts for ts in rate_limits.get(user_id, []) if now - ts < 60]
    if len(recent) >= 3:
        rate_limits[user_id] = recent
        return True
    recent.append(now)
    rate_limits[user_id] = recent
    return False


def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id", chat_id)
    text = (message.get("text") or "").strip()
    print(f"Telegram message received chat_id={chat_id} user_id={user_id} text={text[:80]!r}")

    if text == "/start":
        print(f"Sending start response chat_id={chat_id}")
        send_message(chat_id, "Paste a Solana token contract address and I will pull its TRENCHCOAT rap sheet.")
        return

    match = SOLANA_CA.search(text)
    if not match:
        print(f"Invalid contract address chat_id={chat_id}")
        send_message(chat_id, "Invalid contract address.")
        return

    if rate_limited(user_id):
        print(f"Rate limited user_id={user_id}")
        send_message(chat_id, "Slow down. 3 raps per minute max.")
        return

    ca = match.group(0)
    print(f"Valid contract address chat_id={chat_id} ca={ca}")
    loading = send_message(chat_id, "SCANNING...", parse_mode=None)
    message_id = loading["result"]["message_id"]

    try:
        dossier = fetch_dossier(ca)
    except Exception as e:
        print(f"Dossier fetch failed chat_id={chat_id} ca={ca}: {e}")
        edit_message(
            chat_id,
            message_id,
            "Couldn't pull data on this one.\n\nIf this is a fresh token, try again in 1-2 minutes.",
            parse_mode=None,
        )
        return

    try:
        edit_message(chat_id, message_id, format_dossier(dossier, ca), parse_mode="HTML")
        print(f"Dossier sent chat_id={chat_id} ca={ca}")
    except Exception as e:
        print(f"Formatted Telegram send failed chat_id={chat_id} ca={ca}: {e}")
        edit_message(chat_id, message_id, format_plain_dossier(dossier, ca), parse_mode=None)
        print(f"Plain dossier sent chat_id={chat_id} ca={ca}")


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    configure_webhook()


if __name__ == "__main__":
    main()
