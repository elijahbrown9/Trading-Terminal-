# ASCEND Hard Risk Limits

Version: 1.0.0  
Status: **NOT APPROVED — LIVE TRADING DISABLED**

These limits fail closed and never bend intraday. If a requested action would
exceed a limit, stop and ask before changing the rules. Approval of one trade is
not approval to change a rule.

## Account permissions

- **Writable only after system approval:** Robinhood Agentic cash account
  `••••0924`.
- **Read-only forever:** default individual `••••5308`, Roth IRA `••••0208`,
  Traditional IRA `••••7445`, and every account not explicitly added to this
  file by a reviewed version change.
- The system never requests, receives, logs, or stores credentials.

## Unit and exposure definitions

- `equity` = broker-reported account equity at the current run.
- `1 unit` = 10% of equity, rounded down to whole cents.
- An option position's at-risk amount is total premium paid plus fees.
- Contract quantity is the greatest whole number whose reviewed debit fits the
  permitted units. If one contract exceeds the cap, quantity is zero.
- Conviction, score magnitude, recent wins, or unrealized profit never increase
  size.

## Hard portfolio limits

| Grade | Max total positions | Max new entries/run | Max units/position | Max total premium at risk | Minimum cash after order |
|---|---:|---:|---:|---:|---:|
| `-2` | 2, exit management only | 0 | 0 | 10% equity | 90% equity |
| `-1` | 2 | 1 | 1 | 10% equity | 75% equity |
| `0` | 3 | 2 | 1 | 20% equity | 65% equity |
| `+1` | 4 | 2 | 1 | 30% equity | 55% equity |
| `+2` | 5 | 3 | 1 | 30% equity | 50% equity |

Additional limits:

- Maximum one open directional position per ticker.
- Pending opening orders count as positions and at-risk premium.
- Maximum reviewed debit per position is the lesser of one unit and $2,500.
- Maximum aggregate daily opening debit is two units.
- No margin, instant-deposit buying power, or unsettled proceeds may be relied on.

## Stops and exits

- Option stops use the premium levels in `strategy.md`, with the underlying
  thesis-invalidation level as an additional exit trigger.
- Stops can tighten but never widen.
- Profit scales are precommitted in `strategy.md`; remaining contracts trail
  using the reviewed exit plan.
- Exit management runs before entry evaluation on every intraday cycle.
- A missing quote, stale quote, crossed market, broker error, or uncertain
  position state blocks entries and escalates exit review.

### Manual desk

The manual desk is a separate share-sizing reference and does not authorize
share trading:

- 1 unit = 10% of equity.
- Grade `-2`: no new longs.
- Grade `-1`: one-unit probes.
- Grade `0`: up to two units.
- Grade `+1`: two to three units.
- Grade `+2`: three units maximum.
- Manual-desk share stop: -3% from entry, never widened.
- No margin at grades `-2`, `-1`, or `0`; this system uses no margin at any grade.

## Daily loss and behavioral limits

- Daily loss limit = lesser of 2% of start-of-day equity or $530.
- Count realized losses, fees, and open-position mark-to-market deterioration.
- At the daily limit: cancel unfilled opening orders, manage exits only, and
  disable entries through the next regular-session open.
- After three stop-outs in one ticker during five trading days, ban that ticker
  for five full trading days.
- A third round trip in one ticker within five sessions is blocked even before
  the stop-out threshold.
- Two consecutive losing exits within 60 minutes trigger a 90-minute
  entry-cooldown and `REVENGE_RISK` alert.
- No entries outside 09:30–16:00 America/New_York. Specifically, no overnight
  session, premarket, or after-hours entries.

## Earnings

- No position may be intentionally held through an earnings event.
- Positions must be closed by 15:45 ET on the last regular session before the
  event.
- Unknown or conflicting earnings dates fail closed.
- Earnings must be checked during candidate generation, review, and immediately
  before placement.

## Review-before-place protocol

An order is ineligible unless a review record, generated less than 60 seconds
earlier, contains:

- account, symbol, OCC contract, side, quantity, limit price, maximum debit;
- current grade and input freshness;
- underlying and option quote timestamps;
- expiry, delta, bid, ask, spread, volume, open interest;
- earnings date and source timestamp;
- entry, option stop, underlying invalidation, scale targets;
- positions, pending orders, cash, equity, daily P&L, ticker-ban state;
- every rule check with explicit pass/fail.

Placement must reproduce the reviewed order exactly. Any changed field requires
a new review.

## Idempotency and uncertain state

- Idempotency key:
  `account|trading_date|strategy_version|contract|side|entry_level|cycle_id`.
- Persist the key before placement. Reuse is forbidden.
- After timeout or ambiguous broker response, query orders by account and key
  context before any retry.
- Never retry blindly. Unknown placement state means stop and reconcile.
- Every decision, review, placement attempt, broker response, and rule conflict
  is appended to an audit log with UTC timestamp.

