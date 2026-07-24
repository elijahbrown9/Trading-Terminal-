"""End-to-end dry-run engine. It never calls a broker write method."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from board_signals import analyze_board, board_skew
from alerts import evaluate_alerts
from correlation import correlation_gate
from discipline import analyze_trades
from edge_validation import shadow_entry, summarize
from garch import fit_from_bars
from mcp_bridge import Snapshot, rules_hash
from risk_score import compute_score
from sentiment import validate_assessment
from trade_ideas import score_candidate


def _volatility_input(models: dict) -> float:
    average_ratio = sum(model.storm_ratio for model in models.values()) / len(models)
    return max(-1.0, min(1.0, 1.0 - average_ratio))


def run(snapshot: Snapshot, repo: str | Path = ".") -> dict:
    garch = {symbol: fit_from_bars(symbol, snapshot.daily_bars[symbol]) for symbol in ("SPY", "QQQ")}
    board = analyze_board(snapshot.board_items)
    conditions_score = float(snapshot.conditions["score"])
    sentiment = validate_assessment(snapshot.sentiment)
    sentiment_score = sentiment.score
    score = compute_score(
        volatility=_volatility_input(garch),
        conditions=conditions_score,
        board=board_skew(board),
        sentiment=sentiment_score,
        index_regimes={symbol: model.regime for symbol, model in garch.items()},
    )
    open_returns = snapshot.conditions.get("open_position_returns", {})
    raw_candidates = []
    for item in snapshot.conditions.get("candidates", []):
        enriched = dict(item)
        if item.get("daily_returns") is not None:
            enriched["correlation_gate"] = correlation_gate(
                str(item["ticker"]),
                list(item["daily_returns"]),
                open_returns,
            )
        elif open_returns:
            enriched["correlation_gate"] = {
                "blocked": True,
                "reason": "INSUFFICIENT_HISTORY",
                "unknown": list(open_returns),
            }
        raw_candidates.append(enriched)
    candidates = [score_candidate(item, grade=score.grade, equity=snapshot.equity) for item in raw_candidates]
    shadows = []
    for item, idea in zip(raw_candidates, candidates):
        classification = str(item.get("classification") or idea.strength).upper()
        if classification in {"WATCH-ONLY", "KNIFE CATCH"}:
            candidate = dict(item)
            candidate["classification"] = classification
            shadows.append(shadow_entry(candidate, snapshot.captured_at, ",".join(idea.blocked_reasons)))
    validation = summarize(snapshot.conditions.get("validation_history", []))
    alerts = evaluate_alerts(
        [*snapshot.positions, *snapshot.option_positions],
        snapshot.conditions.get("previous_grade"),
        score.grade,
    )
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
        "sentiment": sentiment.to_dict(),
        "ideas": [idea.to_dict() for idea in sorted(candidates, key=lambda x: x.agreement_score, reverse=True)],
        "shadow_candidates": shadows,
        "validation": validation.to_dict(),
        "alerts": alerts,
        "discipline": [flag.to_dict() for flag in analyze_trades(snapshot.realized_trades)],
        "orders": snapshot.orders,
        "realized_trades": snapshot.realized_trades,
    }


def write_result(result: dict, destination: str | Path) -> None:
    path = Path(destination)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
    temporary.replace(path)
