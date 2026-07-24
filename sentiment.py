"""Validate a structured LLM reading of the digest; no keyword scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SentimentAssessment:
    score: float
    lean: str
    conviction: str
    tickers: tuple[str, ...]
    rationale: str
    model: str
    assessed_at: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tickers"] = list(self.tickers)
        return data


def validate_assessment(value: dict) -> SentimentAssessment:
    """The host LLM produces this record after reading the entire digest."""
    required = ("score", "lean", "conviction", "rationale", "model", "assessed_at")
    missing = [key for key in required if not value.get(key) and value.get(key) != 0]
    if missing:
        raise ValueError(f"Missing LLM sentiment fields: {', '.join(missing)}")
    score = float(value["score"])
    if not -1 <= score <= 1:
        raise ValueError("Sentiment score must be between -1 and +1")
    lean = str(value["lean"]).upper()
    conviction = str(value["conviction"]).upper()
    if lean not in {"BEARISH", "MIXED", "BULLISH"}:
        raise ValueError("lean must be BEARISH, MIXED, or BULLISH")
    if conviction not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("conviction must be LOW, MEDIUM, or HIGH")
    return SentimentAssessment(
        score=score,
        lean=lean,
        conviction=conviction,
        tickers=tuple(str(x).upper() for x in value.get("tickers", [])),
        rationale=str(value["rationale"]).strip(),
        model=str(value["model"]),
        assessed_at=str(value["assessed_at"]),
    )
