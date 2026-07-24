"""Forward validation, shadow-book tracking, and append-only trade journals."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from statistics import fmean

MIN_SETTLED_DAYS = 40


@dataclass(frozen=True)
class ValidationSummary:
    status: str
    settled_days: int
    minimum_days: int
    grade_return_correlation: float | None
    grade_buckets: dict
    component_correlations: dict
    strategy_mean_return_pct: float | None
    warning: str

    def to_dict(self) -> dict:
        return asdict(self)


def _correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    xm, ym = fmean(xs), fmean(ys)
    numerator = sum((x - xm) * (y - ym) for x, y in zip(xs, ys))
    denominator = (
        sum((x - xm) ** 2 for x in xs) * sum((y - ym) ** 2 for y in ys)
    ) ** 0.5
    return numerator / denominator if denominator else None


def append_csv(path: str | Path, record: dict, fieldnames: list[str]) -> None:
    """Append one immutable observation; reject duplicate idempotency keys."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    key = str(record.get("idempotency_key", ""))
    if target.exists() and key:
        with target.open(newline="", encoding="utf-8") as handle:
            if any(row.get("idempotency_key") == key for row in csv.DictReader(handle)):
                return
    write_header = not target.exists()
    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(record)


def summarize(records: list[dict]) -> ValidationSummary:
    settled = [
        row for row in records
        if row.get("spy_next_return_pct") is not None
        and row.get("qqq_next_return_pct") is not None
    ]
    grades = [float(row["grade"]) for row in settled]
    benchmark = [
        (float(row["spy_next_return_pct"]) + float(row["qqq_next_return_pct"])) / 2
        for row in settled
    ]
    buckets: dict[str, dict] = {}
    for grade in range(-2, 3):
        values = [ret for row, ret in zip(settled, benchmark) if int(row["grade"]) == grade]
        buckets[str(grade)] = {
            "count": len(values),
            "mean_next_return_pct": fmean(values) if values else None,
            "win_rate": sum(value > 0 for value in values) / len(values) if values else None,
        }
    components = {}
    for name in ("volatility", "conditions", "board", "sentiment"):
        xs = [float(row[name]) for row in settled if row.get(name) is not None]
        ys = [benchmark[index] for index, row in enumerate(settled) if row.get(name) is not None]
        components[name] = _correlation(xs, ys)
    pnl = [float(row["strategy_return_pct"]) for row in settled if row.get("strategy_return_pct") is not None]
    enough = len(settled) >= MIN_SETTLED_DAYS
    return ValidationSummary(
        status="VALIDATION_WINDOW_COMPLETE" if enough else "UNVALIDATED",
        settled_days=len(settled),
        minimum_days=MIN_SETTLED_DAYS,
        grade_return_correlation=_correlation(grades, benchmark),
        grade_buckets=buckets,
        component_correlations=components,
        strategy_mean_return_pct=fmean(pnl) if pnl else None,
        warning=(
            "Exploratory evidence only; do not change risk or enable trading from this sample."
            if not enough else
            "Forty days permits a first review, not proof of durable edge; inspect uncertainty and out-of-sample behavior."
        ),
    )


def journal_entry(
    ticker: str,
    thesis: str,
    grade: int,
    invalidation: str,
    entered_at: str,
    idempotency_key: str,
) -> dict:
    if not thesis.strip() or not invalidation.strip():
        raise ValueError("Thesis and falsifiable invalidation are required")
    return {
        "idempotency_key": idempotency_key,
        "entered_at": entered_at,
        "ticker": ticker.upper(),
        "grade": grade,
        "thesis": thesis.strip(),
        "invalidation": invalidation.strip(),
        "outcome": "",
        "review_notes": "",
    }


def shadow_entry(candidate: dict, observed_at: str, reason: str) -> dict:
    classification = str(candidate.get("classification") or candidate.get("strength", "")).upper()
    if classification not in {"WATCH-ONLY", "KNIFE CATCH"}:
        raise ValueError("Only WATCH-ONLY and KNIFE CATCH candidates belong in the shadow book")
    return {
        "idempotency_key": f"{observed_at}|{candidate['ticker']}|{classification}",
        "observed_at": observed_at,
        "ticker": str(candidate["ticker"]).upper(),
        "direction": str(candidate["direction"]).upper(),
        "classification": classification,
        "reason": reason,
        "reference_price": candidate.get("underlying_price", ""),
        "return_1d_pct": "",
        "return_5d_pct": "",
        "return_21d_pct": "",
    }
