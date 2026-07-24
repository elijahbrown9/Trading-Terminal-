"""Pure alert evaluation for an external hourly-or-better monitor."""

from __future__ import annotations


def evaluate_alerts(
    positions: list[dict],
    previous_grade: int | None,
    current_grade: int,
    movement_threshold_pct: float = 25.0,
) -> list[dict]:
    alerts = []
    for position in positions:
        symbol = str(position.get("symbol") or position.get("chain_symbol", "")).upper()
        mark = float(position.get("mark", 0))
        stop = float(position.get("stop", 0))
        move = float(position.get("move_pct", 0))
        if stop and mark <= stop:
            alerts.append({"severity": "CRITICAL", "kind": "STOP_BREACH", "symbol": symbol, "value": mark})
        if abs(move) >= movement_threshold_pct:
            alerts.append({"severity": "HIGH", "kind": "POSITION_MOVE", "symbol": symbol, "value": move})
    if previous_grade is not None and previous_grade != current_grade:
        alerts.append({
            "severity": "HIGH",
            "kind": "GRADE_FLIP",
            "from_grade": previous_grade,
            "to_grade": current_grade,
        })
    return alerts
