"""End-to-end dry-run engine. It never calls a broker write method."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from board_signals import analyze_board, board_skew
from discipline import analyze_trades
from garch import fit_from_bars
from mcp_bridge import Snapshot, rules_hash
from risk_score import compute_score
from trade_ideas import score_candidate


def _volatility_input(models: dict) -> float:
    average_ratio = sum(model.storm_ratio for model in models.values()) / len(models)
    return max(-1.0, min(1.0, 1.0 - average_ratio))


def run(snapshot: Snapshot, repo: str | Path = ".") -> dict:
    garch = {symbol: fit_from_bars(symbol, snapshot.daily_bars[symbol]) for symbol in ("SPY", "QQQ")}
    board = analyze_board(snapshot.board_items)
    conditions_score = float(snapshot.conditions["score"])
    sentiment_score = float(snapshot.sentiment["score"])
    score = compute_score(
        volatility=_volatility_input(garch),
        conditions=conditions_score,
        board=board_skew(board),
        sentiment=sentiment_score,
        index_regimes={symbol: model.regime for symbol, model in garch.items()},
    )
    candidates = [
        score_candidate(item, grade=score.grade, equity=snapshot.equity)
        for item in snapshot.conditions.get("candidates", [])
    ]
    return {
        "mode": "DRY_RUN",
        "live_trading_enabled": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "captured_at": snapshot.captured_at,
        "account_last4": snapshot.account_last4,
        "rules_hash": rules_hash(repo),
        "equity": snapshot.equity,
        "cash": snapshot.cash,
        "positions": snapshot.positions,
        "option_positions": snapshot.option_positions,
        "garch": {symbol: model.to_dict() for symbol, model in garch.items()},
        "score": score.to_dict(),
        "conditions": snapshot.conditions,
        "board": [item.to_dict() for item in board],
        "sentiment": snapshot.sentiment,
        "ideas": [idea.to_dict() for idea in sorted(candidates, key=lambda x: x.agreement_score, reverse=True)],
        "discipline": [flag.to_dict() for flag in analyze_trades(snapshot.realized_trades)],
        "orders": snapshot.orders,
        "realized_trades": snapshot.realized_trades,
    }


def write_result(result: dict, destination: str | Path) -> None:
    path = Path(destination)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
    temporary.replace(path)

