"""Create deterministic synthetic data for tests and terminal preview only."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sin
import json
from pathlib import Path
import random


def bars(symbol: str, seed: int, start: float) -> list[dict]:
    random.seed(seed)
    value = start
    output = []
    day = datetime.now(timezone.utc) - timedelta(days=700)
    for index in range(501):
        shock = random.gauss(0, 0.009 + 0.004 * abs(sin(index / 31)))
        value *= 1 + shock
        output.append({"begins_at": day.isoformat(), "symbol": symbol, "close_price": round(value, 4)})
        day += timedelta(days=1)
    return output


def build() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "captured_at": now.isoformat(),
        "account_last4": "0924",
        "equity": 26500.0,
        "cash": 19400.0,
        "positions": [],
        "option_positions": [
            {"chain_symbol": "RIG", "quantity": "1", "average_price": "0.28"},
            {"chain_symbol": "OPEN", "quantity": "1", "average_price": "0.55"},
        ],
        "orders": [],
        "realized_trades": [
            {"ticker": "ONDS", "filled_at": (now - timedelta(days=2, hours=2)).isoformat(), "realized_pnl": 35},
            {"ticker": "CLOV", "filled_at": (now - timedelta(days=1, hours=3)).isoformat(), "realized_pnl": -16},
        ],
        "daily_bars": {"SPY": bars("SPY", 7, 620), "QQQ": bars("QQQ", 11, 550)},
        "conditions": {
            "score": -0.45,
            "summary": "VIX neutral; Brent and Korea are risk-off; geopolitical risk elevated.",
            "candidates": [
                {
                    "ticker": "MU", "direction": "LONG", "option_symbol": "MU260821C00150000",
                    "price_confirmed": True, "board_confirmed": True, "sentiment_agrees": True,
                    "cheap_iv": True, "conflict": False, "crowded": False, "expiry_days": 28,
                    "delta": 0.42, "open_interest": 1800, "volume": 450, "earnings_clear": True,
                    "bid": 2.35, "ask": 2.50, "entry": 2.42
                }
            ],
        },
        "board_items": [
            {"ticker": "INTC", "direction": "SHORT", "source": "@research", "text": "dilution risk", "posted_at": (now - timedelta(hours=2)).isoformat(), "return_since_post_pct": -7.8, "crowd_count": 3},
            {"ticker": "MU", "direction": "LONG", "source": "@memory", "text": "DRAM pricing", "posted_at": (now - timedelta(hours=1)).isoformat(), "return_since_post_pct": 1.4, "crowd_count": 4},
        ],
        "sentiment": {"score": -0.13, "summary": "Desk sentiment remains mixed/cautious."},
    }


if __name__ == "__main__":
    Path("snapshot.demo.json").write_text(json.dumps(build(), indent=2), encoding="utf-8")

