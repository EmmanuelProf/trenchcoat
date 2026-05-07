import logging
import time
from collections import defaultdict
from typing import Any

from app.models.dossier import BundleAnalysis
from app.services.birdeye import (
    BirdeyeBadRequestError,
    BirdeyeClient,
    BirdeyeError,
    BirdeyeRateLimitError,
)

logger = logging.getLogger(__name__)

SECONDS_IN_30_DAYS = 30 * 24 * 60 * 60
LAUNCH_WINDOW_SECONDS = 30


def _data(response: dict[str, Any]) -> Any:
    return response.get("data", response)


def _items(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = _data(response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "transactions", "txs", "tokens"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(*values: Any) -> float | None:
    for value in values:
        parsed = _number(value)
        if parsed is not None:
            return parsed
    return None


def _block_time(tx: dict[str, Any]) -> int | None:
    value = _first_number(tx.get("blockUnixTime"), tx.get("block_unix_time"), tx.get("blockTime"))
    return int(value) if value is not None else None


def _block_number(tx: dict[str, Any]) -> int | None:
    value = _first_number(tx.get("blockNumber"), tx.get("block"), tx.get("slot"))
    return int(value) if value is not None else _block_time(tx)


def _owner(tx: dict[str, Any]) -> str | None:
    for key in ("owner", "wallet", "address", "userAddress", "trader", "source"):
        value = tx.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _side(tx: dict[str, Any]) -> str:
    for key in ("side", "txType", "type", "tradeType", "transactionType"):
        value = tx.get(key)
        if isinstance(value, str):
            return value.lower()
    return ""


def _token_address(token: dict[str, Any]) -> str | None:
    for key in ("address", "mint", "tokenAddress", "token_address"):
        value = token.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _token_amount(token: dict[str, Any]) -> float | None:
    return _first_number(
        token.get("uiAmount"),
        token.get("ui_amount"),
        token.get("amount"),
        token.get("tokenAmount"),
        token.get("token_amount"),
        token.get("ui_amount_raw"),
    )


def _token_side(tx: dict[str, Any], ca: str) -> str:
    base = tx.get("base")
    quote = tx.get("quote")
    if isinstance(base, dict) and _token_address(base) == ca:
        return str(base.get("type_swap") or base.get("type") or "").lower()
    if isinstance(quote, dict) and _token_address(quote) == ca:
        return str(quote.get("type_swap") or quote.get("type") or "").lower()
    return ""


def _is_buy(tx: dict[str, Any], ca: str) -> bool:
    side = _side(tx)
    if side in {"buy", "bought"}:
        return True
    if side in {"sell", "sold"}:
        return False

    token_side = _token_side(tx, ca)
    if token_side in {"buy", "bought"}:
        return True
    if token_side in {"sell", "sold"}:
        return False

    to_token = tx.get("to") or tx.get("toToken") or tx.get("tokenTo") or {}
    if isinstance(to_token, dict):
        return ca in {
            to_token.get("address"),
            to_token.get("mint"),
            to_token.get("tokenAddress"),
        }
    return False


def _bought_amount(tx: dict[str, Any], ca: str) -> float:
    for key in ("base", "quote"):
        token = tx.get(key)
        if isinstance(token, dict) and _token_address(token) == ca:
            amount = _token_amount(token)
            if amount is not None:
                return amount

    to_token = tx.get("to") or tx.get("toToken") or tx.get("tokenTo") or {}
    if isinstance(to_token, dict) and ca in {
        to_token.get("address"),
        to_token.get("mint"),
        to_token.get("tokenAddress"),
    }:
        amount = _first_number(
            to_token.get("uiAmount"),
            to_token.get("ui_amount"),
            to_token.get("amount"),
            to_token.get("tokenAmount"),
        )
        if amount is not None:
            return amount

    amount = _first_number(
        tx.get("toUiAmount"),
        tx.get("to_ui_amount"),
        tx.get("uiAmount"),
        tx.get("ui_amount"),
        tx.get("amount"),
        tx.get("tokenAmount"),
    )
    return amount or 0


def _supply(overview: dict[str, Any]) -> float | None:
    data = _data(overview)
    if not isinstance(data, dict):
        return None
    return _first_number(
        data.get("supply"),
        data.get("circulatingSupply"),
        data.get("totalSupply"),
    )


def _created_at(creation_info: dict[str, Any]) -> int | None:
    data = _data(creation_info)
    if not isinstance(data, dict):
        return None
    value = _first_number(data.get("blockUnixTime"), data.get("block_unix_time"))
    return int(value) if value is not None else None


async def _fetch_transactions(
    ca: str,
    chain: str,
    birdeye: BirdeyeClient,
) -> list[dict[str, Any]]:
    first_page = _items(await birdeye.token_txs(ca, limit=50, sort="asc", chain=chain, offset=0))
    second_page = _items(await birdeye.token_txs(ca, limit=50, sort="asc", chain=chain, offset=50))
    return sorted(
        first_page + second_page,
        key=lambda tx: _block_time(tx) or 0,
    )[:100]


async def get_deployer_from_txs(
    ca: str,
    chain: str,
    birdeye: BirdeyeClient,
) -> str | None:
    try:
        transactions = _items(await birdeye.token_txs(ca, limit=5, sort="asc", chain=chain, offset=0))
    except BirdeyeError as exc:
        logger.warning("could not derive deployer from txs for %s: %s", ca, exc)
        return None

    if not transactions:
        return None

    wallet = _owner(sorted(transactions, key=lambda tx: _block_time(tx) or 0)[0])
    if wallet:
        logger.info(f"deployer derived from txs: {wallet} for {ca}")
    return wallet


def analyze_transactions(
    ca: str,
    transactions: list[dict[str, Any]],
    supply: float | None = None,
) -> tuple[BundleAnalysis | None, dict[str, Any]]:
    if not transactions:
        return None, {
            "launch_window_start": None,
            "launch_window_end": None,
            "launch_buy_count": 0,
            "top_buyers": [],
        }

    first_time = _block_time(transactions[0])
    if first_time is None:
        return None, {
            "launch_window_start": None,
            "launch_window_end": None,
            "launch_buy_count": 0,
            "top_buyers": [],
        }

    launch_window_end = first_time + LAUNCH_WINDOW_SECONDS
    launch_buys = [
        tx
        for tx in transactions
        if first_time <= (_block_time(tx) or 0) <= launch_window_end and _is_buy(tx, ca)
    ]

    bought_by_wallet: dict[str, float] = defaultdict(float)
    for tx in launch_buys:
        owner = _owner(tx)
        if not owner:
            continue
        bought_by_wallet[owner] += _bought_amount(tx, ca)

    top_buyers = sorted(bought_by_wallet.items(), key=lambda item: item[1], reverse=True)[:10]
    debug = {
        "launch_window_start": first_time,
        "launch_window_end": launch_window_end,
        "launch_buy_count": len(launch_buys),
        "top_buyers": top_buyers,
    }

    if not supply or supply <= 0:
        return BundleAnalysis(
            bundled=False,
            bundle_pct=0,
            suspect_wallet_count=len(top_buyers),
            earliest_block=_block_number(transactions[0]),
            confidence="low",
        ), debug

    top_buyer_amount = sum(amount for _, amount in top_buyers)
    bundle_pct = (top_buyer_amount / supply) * 100
    if bundle_pct > 25:
        bundled = True
        confidence = "high"
    elif bundle_pct >= 15:
        bundled = True
        confidence = "medium"
    elif bundle_pct >= 10:
        bundled = True
        confidence = "low"
    else:
        bundled = False
        confidence = "low"

    if len(launch_buys) < 10:
        confidence = "low"

    return BundleAnalysis(
        bundled=bundled,
        bundle_pct=round(bundle_pct, 4),
        suspect_wallet_count=len(top_buyers),
        earliest_block=_block_number(transactions[0]),
        confidence=confidence,
    ), debug


async def detect_bundle(
    ca: str,
    chain: str,
    birdeye: BirdeyeClient,
) -> BundleAnalysis | None:
    try:
        creation_info = await birdeye.token_creation_info(ca, chain=chain)
    except BirdeyeRateLimitError as exc:
        logger.warning("bundle detection continuing without creation info after rate limit ca=%s error=%s", ca, exc)
        creation_info = {}
    except BirdeyeBadRequestError as exc:
        logger.warning("bundle detection continuing without creation info after 401/403 ca=%s error=%s", ca, exc)
        creation_info = {}
    except BirdeyeError as exc:
        logger.warning("bundle detection continuing without creation info ca=%s error=%s", ca, exc)
        creation_info = {}

    created_at = _created_at(creation_info)
    if created_at is not None and time.time() - created_at > SECONDS_IN_30_DAYS:
        return BundleAnalysis(
            bundled=False,
            bundle_pct=0,
            suspect_wallet_count=0,
            earliest_block=created_at,
            confidence="low",
        )

    transactions = await _fetch_transactions(ca, chain, birdeye)

    if not transactions:
        logger.warning("bundle detection found no transactions ca=%s chain=%s", ca, chain)
        return None

    supply = _supply(await birdeye.token_overview(ca, chain=chain))
    analysis, _ = analyze_transactions(ca, transactions, supply)

    if analysis is None:
        logger.warning("bundle detection found transactions without block time ca=%s chain=%s", ca, chain)
        return None
    if not supply or supply <= 0:
        logger.warning("bundle detection missing supply ca=%s chain=%s", ca, chain)
    return analysis
