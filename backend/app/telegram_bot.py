import json
import os
import threading
import time
import urllib.request

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
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def send_message(chat_id, text, parse_mode="Markdown"):
    return api_call(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        },
    )


def edit_message(chat_id, message_id, text, parse_mode="Markdown"):
    return api_call(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        },
    )


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
    url = f"{BACKEND_URL}/dossier/{ca}?chain=solana"
    print(f"Fetching dossier from {url}")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())


def format_dossier(dossier, ca):
    band = dossier.get("band", "UNKNOWN")
    score = dossier.get("score", 0)
    overview = dossier.get("overview") or {}
    symbol = overview.get("symbol", "UNKNOWN")
    deployer = dossier.get("deployer") or {}
    wallet = deployer.get("wallet", "unknown")
    prior_count = deployer.get("prior_count", 0)
    rugged_count = deployer.get("rugged_count", 0)
    distribution = dossier.get("distribution") or {}
    bundle = distribution.get("bundle") or {}
    bundle_pct = bundle.get("bundle_pct", distribution.get("bundle_pct"))
    top10_pct = distribution.get("top10_pct")
    verdict = dossier.get("verdict") or "No verdict."

    emoji = {"AVOID": "\U0001f534", "CAUTION": "\U0001f7e1", "CLEAR": "\U0001f7e2"}.get(
        band,
        "\u26aa",
    )
    wallet_short = truncate_wallet(wallet)
    bundle_text = f"{bundle_pct:.1f}%" if isinstance(bundle_pct, (int, float)) else "unknown"
    top10_text = f"{top10_pct:.1f}%" if isinstance(top10_pct, (int, float)) else "unknown"

    return "\n".join(
        [
            f"{emoji} ${symbol} - {band}",
            f"Score: {score}/100",
            "",
            f"Verdict: {verdict}",
            "",
            f"Dev: {wallet_short}",
            f"Prior tokens: {prior_count}",
            f"Rugged: {rugged_count}",
            f"Bundle: {bundle_text}",
            f"Top 10: {top10_text}",
            "",
            f"CA: {ca}",
        ]
    )


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
        edit_message(chat_id, message_id, format_dossier(dossier, ca), parse_mode=None)
        print(f"Dossier sent chat_id={chat_id} ca={ca}")
    except Exception as e:
        print(f"Dossier fetch/send failed chat_id={chat_id} ca={ca}: {e}")
        edit_message(chat_id, message_id, "Couldn't pull data on this one.", parse_mode=None)


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    configure_webhook()


if __name__ == "__main__":
    main()
