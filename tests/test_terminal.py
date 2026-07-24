import json
from pathlib import Path
import unittest

from demo_snapshot import build
from engine import run
from mcp_bridge import Snapshot
from terminal import render


ROOT = Path(__file__).parents[1]


class TerminalTests(unittest.TestCase):
    def test_self_contained_terminal(self):
        raw = build()
        snapshot = Snapshot(**raw)
        result = run(snapshot, repo=ROOT)
        result["mode"] = "DRY_RUN / SYNTHETIC DEMO"
        page = render(result)
        self.assertIn("<!doctype html>", page.lower())
        self.assertIn("STORM GAUGE", page)
        self.assertIn("DRY_RUN / SYNTHETIC DEMO", page)
        self.assertNotIn("<script src=", page)
        self.assertNotIn("<link rel=", page)

    def test_repository_has_no_order_placement_call(self):
        forbidden = ("place_option_order(", "place_equity_order(", "cancel_option_order(")
        for path in ROOT.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, f"{phrase} found in {path.name}")


if __name__ == "__main__":
    unittest.main()
