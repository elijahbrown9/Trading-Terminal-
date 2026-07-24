# ASCEND Risk Terminal

An automated, rules-first research and trading-control system for the Robinhood
Agentic account. The repository is **dry-run only** until its rule files are
explicitly approved.

## Safety state

- No credentials are accepted or stored.
- `approval.json` disables live trading.
- The Python runtime contains no broker write method.
- Robinhood data enters as a normalized, masked MCP snapshot.
- All other Robinhood accounts are permanently read-only under `risk.md`.
- External feed text is treated as untrusted data and command-like content is
  quarantined.

## Run locally

Python 3.11+ is sufficient; there are no third-party dependencies.

```bash
python -m unittest discover -s tests -v
python demo_snapshot.py
python automation.py --snapshot snapshot.demo.json --cycle preopen
```

Then open `terminal.html`.

## Architecture

- `strategy.md`, `risk.md`, `workflow.md`: operating law.
- `garch.py`: dependency-free Gaussian MLE asymmetric GJR-GARCH(1,1).
- `risk_score.py`: weighted composite and dual-STORM veto.
- `board_signals.py`: leading/coincident/lagging separation and quarantine.
- `trade_ideas.py`: agreement score and risk-derived sizing.
- `discipline.py`: churn, overnight fill, and revenge detection.
- `mcp_bridge.py`: validates fresh normalized MCP snapshots.
- `engine.py`: deterministic dry-run orchestration.
- `terminal.py`: self-contained HTML generator.
- `automation.py`: scheduled dry-run entrypoint and after-action report.
- `sentiment.py`: validates the host LLM's full-digest directional reading.
- `correlation.py`: blocks correlated exposure at 0.70 or missing history.
- `edge_validation.py`: 40-day forward validation, shadow book, and journal.
- `alerts.py`: read-only stop, 25% move, and grade-flip alert evaluation.

## Evidence policy

The weights and thresholds are hypotheses. The dashboard reports `UNVALIDATED`
until 40 trading days have settled with following-session SPY/QQQ returns and
strategy P&L. Even then, the review is exploratory rather than proof of edge.

## MCP boundary

The connected host—not this repository—reads Robinhood through MCP and writes a
fresh snapshot. Credentials remain with Robinhood and the MCP host. The
standalone code cannot call MCP directly, so it does not pretend otherwise.
See `MCP_CAPABILITIES.md` for the verified capability matrix and the missing
option/historical-data tools that currently block activation.

A future approved live boundary must:

1. read the same immutable rules;
2. create a review record less than 60 seconds old;
3. enforce every risk check;
4. obtain a broker review response;
5. place only the exactly reviewed order with an unused idempotency key;
6. reconcile ambiguous results before any retry.

That boundary does not exist in this version and will not be added or activated
until the rules and full system are approved.
