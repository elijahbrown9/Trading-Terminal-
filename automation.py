"""Scheduled job entrypoint. Live trading is intentionally impossible in v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import run, write_result
from mcp_bridge import read_snapshot
from terminal import write_terminal


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, help="Fresh normalized MCP snapshot JSON")
    parser.add_argument("--output", default="run.json")
    parser.add_argument("--terminal", default="terminal.html")
    parser.add_argument("--cycle", choices=("preopen", "intraday", "close"), required=True)
    args = parser.parse_args()

    snapshot = read_snapshot(args.snapshot)
    result = run(snapshot, repo=Path(__file__).parent)
    if "demo" in Path(args.snapshot).name.lower():
        result["mode"] = "DRY_RUN / SYNTHETIC DEMO"
    result["cycle"] = args.cycle
    result["report"] = {
        "did": ["read fresh MCP snapshot", "ran models", "published terminal"],
        "did_not": ["review broker order", "place order", "cancel order"],
    }
    write_result(result, args.output)
    write_terminal(result, args.terminal)
    print(json.dumps(result["report"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
