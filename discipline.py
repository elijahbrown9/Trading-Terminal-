"""Detect churn, overnight fills, and revenge-trading patterns."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class DisciplineFlag:
    kind: str
    ticker: str | None
    severity: str
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(NEW_YORK)


def analyze_trades(trades: list[dict]) -> list[DisciplineFlag]:
    flags: list[DisciplineFlag] = []
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for trade in sorted(trades, key=lambda row: row["filled_at"]):
        ticker = str(trade["ticker"]).upper()
        by_ticker[ticker].append(trade)
        filled = _time(str(trade["filled_at"]))
        if filled.hour < 9 or (filled.hour == 9 and filled.minute < 30) or filled.hour >= 16:
            flags.append(DisciplineFlag("OVERNIGHT_FILL", ticker, "HIGH", f"Fill at {filled.isoformat()} outside 09:30–16:00 ET"))

    for ticker, rows in by_ticker.items():
        closed = [row for row in rows if row.get("realized_pnl") is not None]
        if len(closed) >= 3 and sum(float(row["realized_pnl"]) for row in closed) < 0:
            flags.append(DisciplineFlag("CHURN", ticker, "HIGH", f"{len(closed)} round trips net red"))

    exits = sorted(
        [row for row in trades if row.get("realized_pnl") is not None],
        key=lambda row: row["filled_at"],
    )
    for first, second in zip(exits, exits[1:]):
        minutes = (_time(second["filled_at"]) - _time(first["filled_at"])).total_seconds() / 60
        if float(first["realized_pnl"]) < 0 and float(second["realized_pnl"]) < 0 and 0 <= minutes <= 60:
            flags.append(DisciplineFlag("REVENGE_STREAK", str(second["ticker"]).upper(), "HIGH", "Two losing exits within 60 minutes; 90-minute cooldown"))
    return flags

