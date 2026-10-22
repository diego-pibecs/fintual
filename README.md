# Portfolio Rebalancer

A small Python module for the portfolio-rebalancing exercise in Fintual's
[Software Engineer application](https://jobs.lever.co/fintual/9c863695-5fdd-40f3-a907-fc8db1227036).
It models stock positions and proposes the trades needed to reach a target
allocation.

## Quick start

Run the included META/AAPL example directly:

```bash
./run.sh
```

This prints each proposed action, ticker, fractional quantity, and monetary
value. The same example can also be launched with
`PYTHONPATH=src python3 -m portfolio_rebalancer`.

## Design decisions and assumptions

- `Stock` holds a ticker, a non-negative number of shares, and the latest known
  positive price. `current_price()` returns that supplied price.
- `Portfolio` requires exactly one target allocation per stock. Allocations are
  fractions between `0` and `1`, may be zero, and must sum exactly to `1` for a
  non-empty portfolio. An empty portfolio must have no allocations.
- The rebalance is self-financing: it reallocates the current holdings and does
  not add or withdraw cash. Therefore a portfolio whose positions are all zero
  produces no trades.
- Fractional shares are supported. Trade quantities are not rounded because no
  exchange precision was specified; a real order layer would apply its own lot
  size and rounding policy.
- Financial values are converted to and calculated with `Decimal`. Numeric
  strings and integers are preferred, but floats are accepted by converting
  their display form (`str(value)`) instead of their binary representation.
- Short positions, duplicate tickers, missing allocations, non-finite numbers,
  and zero or negative prices are rejected. Tickers are trimmed and uppercased.
- Returned trades are sorted by ticker so results are deterministic.

## Algorithm

For each stock, the module calculates:

```text
current value = shares * current price
target value  = total portfolio value * target allocation
difference    = target value - current value
```

A positive difference becomes a `BUY`; a negative difference becomes a `SELL`.
The monetary trade value is the absolute difference, and the quantity is that
value divided by the current price. A zero difference emits no trade.

## Installation and tests

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest
```

The runtime package has no third-party dependencies.

## Worked example: META and AAPL

```python
from portfolio_rebalancer import Portfolio, Stock

portfolio = Portfolio(
    stocks=[
        Stock("META", shares="2", price="300"),  # $600
        Stock("AAPL", shares="2", price="200"),  # $400
    ],
    target_allocations={"META": "0.5", "AAPL": "0.5"},
)

for trade in portfolio.rebalance():
    print(trade)
```

The portfolio is worth `$1,000`, so each target position is worth `$500`. The
result proposes buying `0.5` AAPL for `$100` and selling one third of a META
share for `$100` (subject to the active `Decimal` context precision).

## Complexity

For `n` stocks, construction uses `O(n)` time and space. Rebalancing computes
values in `O(n)` time, then sorts the proposed processing order in `O(n log n)`
time. It uses `O(n)` additional space.

## AI assistance disclosure

Codex was used to help interpret the requirements, draft the implementation,
tests, and documentation, and run the verification checks. As requested by
Fintual, the complete Codex conversation that contributed to this submission
is shared with the application reviewers:

https://chatgpt.com/s/cx_6ad9842dda0c8191993ce86f2177b2b7
