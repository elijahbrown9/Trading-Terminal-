"""Weighted five-grade market risk score with a dual-STORM veto."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping

WEIGHTS = {"volatility": 3, "conditions": 2, "board": 2, "sentiment": 1}


@dataclass(frozen=True)
class ScoreResult:
    composite: float
    grade: int
    label: str
    veto_applied: bool
    inputs: dict
    computed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def _bounded(value: float) -> float:
    value = float(value)
    if not -1.0 <= value <= 1.0:
        raise ValueError("Each score input must be between -1 and +1")
    return value


def grade_from_score(score: float) -> int:
    if score <= -0.70:
        return -2
    if score <= -0.15:
        return -1
    if score < 0.15:
        return 0
    if score < 0.70:
        return 1
    return 2


def compute_score(
    volatility: float,
    conditions: float,
    board: float,
    sentiment: float,
    index_regimes: Mapping[str, str],
) -> ScoreResult:
    values = {
        "volatility": _bounded(volatility),
        "conditions": _bounded(conditions),
        "board": _bounded(board),
        "sentiment": _bounded(sentiment),
    }
    composite = sum(values[key] * WEIGHTS[key] for key in WEIGHTS) / sum(WEIGHTS.values())
    grade = grade_from_score(composite)
    both_storm = all(index_regimes.get(symbol, "").upper() == "STORM" for symbol in ("SPY", "QQQ"))
    veto = both_storm and grade > -1
    if veto:
        grade = -1
    labels = {-2: "ULTRA RISK OFF", -1: "RISK OFF", 0: "MIXED", 1: "RISK ON", 2: "ULTRA RISK ON"}
    return ScoreResult(
        composite=composite,
        grade=grade,
        label=labels[grade],
        veto_applied=veto,
        inputs=values,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )

