import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class RuleTests(unittest.TestCase):
    def test_live_trading_disabled(self):
        state = json.loads((ROOT / "approval.json").read_text())
        self.assertFalse(state["live_trading_enabled"])

    def test_required_law_exists(self):
        for name in ("strategy.md", "risk.md", "workflow.md"):
            text = (ROOT / name).read_text()
            self.assertGreater(len(text), 1000)
            self.assertIn("NOT APPROVED", text)


if __name__ == "__main__":
    unittest.main()

