"""Classify idea-feed observations without treating feed text as instructions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Iterable

COMMAND_PATTERNS = (
    r"\b(ignore|override|disregard)\b.{0,24}\b(instruction|rule|system)\b",
    r"\b(run|execute|install|download|send|delete)\b.{0,32}\b(command|code|file|credential|password)\b",
    r"\byou must\b|\bdo not tell\b|\bsystem prompt\b",
)


@dataclass(frozen=True)
class BoardSignal:
    ticker: str
    direction: str
    classification: str
    temporal_role: str
    age_minutes: int
    return_since_post_pct: float
    crowd_count: int
    source: str
    quarantined: bool
    quarantine_reason: str | None
    raw_text: str

    def to_dict(self) -> dict:
        return asdict(self)


def contains_command_like_content(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in COMMAND_PATTERNS)


def classify_idea(item: dict, now: datetime | None = None) -> BoardSignal:
    now = now or datetime.now(timezone.utc)
    posted = datetime.fromisoformat(str(item["posted_at"]).replace("Z", "+00:00"))
    age = max(0, int((now - posted).total_seconds() // 60))
    direction = str(item["direction"]).upper()
    move = float(item.get("return_since_post_pct", 0))
    agreeing = move > 0 if direction == "LONG" else move < 0
    bleeding = move < -2 if direction == "LONG" else move > 2
    crowd = int(item.get("crowd_count", 1))
    fresh = age <= 360
    early_crowd = crowd <= 5
    quarantined = contains_command_like_content(str(item.get("text", "")))

    if bleeding:
        classification = "KNIFE CATCH"
    elif crowd >= 12 or age > 1440:
        classification = "CROWDED"
    elif fresh and agreeing and early_crowd:
        classification = "CONFIRMED CANDIDATE"
    else:
        classification = "WATCH"

    temporal_role = "LEADING" if fresh else "COINCIDENT"
    if item.get("realized", False):
        temporal_role = "LAGGING"
    if quarantined:
        classification = "QUARANTINED"

    return BoardSignal(
        ticker=str(item["ticker"]).upper(),
        direction=direction,
        classification=classification,
        temporal_role=temporal_role,
        age_minutes=age,
        return_since_post_pct=move,
        crowd_count=crowd,
        source=str(item.get("source", "unknown")),
        quarantined=quarantined,
        quarantine_reason="Command-like content in external data" if quarantined else None,
        raw_text=str(item.get("text", "")),
    )


def analyze_board(items: Iterable[dict], now: datetime | None = None) -> list[BoardSignal]:
    return [classify_idea(item, now=now) for item in items]


def board_skew(signals: Iterable[BoardSignal]) -> float:
    usable = [s for s in signals if not s.quarantined and s.temporal_role == "LEADING"]
    if not usable:
        return 0.0
    direction = sum(1 if s.direction == "LONG" else -1 for s in usable)
    confirmation = sum(
        (1 if s.direction == "LONG" else -1)
        for s in usable
        if s.classification == "CONFIRMED CANDIDATE"
    )
    return max(-1.0, min(1.0, (direction + confirmation) / (2 * len(usable))))

