"""Correlation guard preventing multiple costumes of the same macro bet."""

from __future__ import annotations

from statistics import fmean

DEFAULT_LIMIT = 0.70


def pearson(left: list[float], right: list[float]) -> float | None:
    size = min(len(left), len(right))
    if size < 20:
        return None
    xs, ys = left[-size:], right[-size:]
    xm, ym = fmean(xs), fmean(ys)
    numerator = sum((x - xm) * (y - ym) for x, y in zip(xs, ys))
    denominator = (sum((x - xm) ** 2 for x in xs) * sum((y - ym) ** 2 for y in ys)) ** 0.5
    return numerator / denominator if denominator else None


def correlation_gate(
    candidate: str,
    candidate_returns: list[float],
    open_position_returns: dict[str, list[float]],
    limit: float = DEFAULT_LIMIT,
) -> dict:
    comparisons = {
        symbol: pearson(candidate_returns, returns)
        for symbol, returns in open_position_returns.items()
    }
    breaches = {
        symbol: value for symbol, value in comparisons.items()
        if value is not None and abs(value) >= limit
    }
    unknown = [symbol for symbol, value in comparisons.items() if value is None]
    return {
        "candidate": candidate.upper(),
        "limit": limit,
        "correlations": comparisons,
        "blocked": bool(breaches) or bool(unknown),
        "breaches": breaches,
        "unknown": unknown,
        "reason": "CORRELATED_EXPOSURE" if breaches else "INSUFFICIENT_HISTORY" if unknown else None,
    }
