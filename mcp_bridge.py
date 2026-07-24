"""File boundary between MCP reads and the deterministic local models.

The standalone repository does not contain credentials or an MCP client. An
authorized host reads Robinhood through MCP, normalizes the responses, and
writes a snapshot with this schema. Trading calls remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

WRITABLE_ACCOUNT_LAST4 = "0924"
READ_ONLY_ACCOUNT_LAST4 = {"5308", "0208", "7445"}


@dataclass(frozen=True)
class Snapshot:
    captured_at: str
    account_last4: str
    equity: float
    cash: float
    positions: list[dict]
    option_positions: list[dict]
    orders: list[dict]
    realized_trades: list[dict]
    daily_bars: dict[str, list[dict]]
    conditions: dict[str, Any]
    board_items: list[dict]
    sentiment: dict[str, Any]


def read_snapshot(path: str | Path) -> Snapshot:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {field for field in Snapshot.__dataclass_fields__}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Snapshot missing fields: {sorted(missing)}")
    if str(raw["account_last4"]) != WRITABLE_ACCOUNT_LAST4:
        raise PermissionError("Only the masked Agentic account snapshot is accepted")
    captured = datetime.fromisoformat(str(raw["captured_at"]).replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - captured).total_seconds()
    if age > 900:
        raise ValueError("Snapshot is stale (>15 minutes)")
    return Snapshot(**{key: raw[key] for key in required})


def rules_hash(repo: str | Path = ".") -> str:
    root = Path(repo)
    digest = hashlib.sha256()
    for name in ("strategy.md", "risk.md", "workflow.md"):
        digest.update(name.encode())
        digest.update(root.joinpath(name).read_bytes())
    return digest.hexdigest()


def safe_public_account(account_number: str) -> str:
    value = str(account_number)
    return f"••••{value[-4:]}"

