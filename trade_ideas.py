"""Candidate agreement scoring and deterministic risk-file sizing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import floor


@dataclass(frozen=True)
class TradeIdea:
    ticker: str
    direction: str
    option_symbol: str
    agreement_score: int
    strength: str
    entry: float
    stop: float
    target_1: float
    target_2: float
    contracts: int
    maximum_debit: float
    blocked_reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["blocked_reasons"] = list(self.blocked_reasons)
        return data


def score_candidate(candidate: dict, grade: int, equity: float) -> TradeIdea:
    direction = str(candidate["direction"]).upper()
    regime_agrees = (direction == "LONG" and grade > 0) or (direction == "SHORT" and grade < 0) or grade == 0
    score = (
        (2 if regime_agrees else -2)
        + (2 if candidate.get("price_confirmed") else 0)
        + (1 if candidate.get("board_confirmed") else 0)
        + (1 if candidate.get("sentiment_agrees") else 0)
        + (1 if candidate.get("cheap_iv") else 0)
        + (-2 if candidate.get("conflict") else 0)
        + (-1 if candidate.get("crowded") else 0)
    )
    strength = "STRONG" if score >= 5 else "MODERATE" if score >= 3 else "WATCH-ONLY"
    blocked: list[str] = []
    required = {
        "expiry_days": 14 <= int(candidate.get("expiry_days", 0)) <= 42,
        "delta": 0.30 <= abs(float(candidate.get("delta", 0))) <= 0.50,
        "open_interest": int(candidate.get("open_interest", 0)) >= 300,
        "volume": int(candidate.get("volume", 0)) >= 100,
        "earnings_clear": bool(candidate.get("earnings_clear")),
    }
    for name, passes in required.items():
        if not passes:
            blocked.append(name)
    bid = float(candidate.get("bid", 0))
    ask = float(candidate.get("ask", 0))
    midpoint = (bid + ask) / 2 if bid > 0 and ask > bid else 0
    if midpoint <= 0 or ask - bid > min(0.20, midpoint * 0.12):
        blocked.append("spread")
    if strength != "STRONG":
        blocked.append("strength")
    if grade == -2:
        blocked.append("grade")
    correlation = candidate.get("correlation_gate", {})
    if correlation.get("blocked"):
        blocked.append(str(correlation.get("reason") or "correlation"))
    premium_cap = min(equity * 0.10, 2500.0)
    entry = round(float(candidate.get("entry", midpoint)), 2)
    contracts = floor(premium_cap / (entry * 100)) if entry > 0 and not blocked else 0
    stop_pct = {-2: 0.20, -1: 0.25, 0: 0.30, 1: 0.35, 2: 0.35}[grade]
    return TradeIdea(
        ticker=str(candidate["ticker"]).upper(),
        direction=direction,
        option_symbol=str(candidate.get("option_symbol", "")),
        agreement_score=score,
        strength=strength,
        entry=entry,
        stop=round(entry * (1 - stop_pct), 2),
        target_1=round(entry * (1.25 if grade <= 0 else 1.30), 2),
        target_2=round(entry * (1.50 if grade <= 0 else 1.60), 2),
        contracts=contracts,
        maximum_debit=round(contracts * entry * 100, 2),
        blocked_reasons=tuple(blocked),
    )
