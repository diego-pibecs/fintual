"""Run the README example with ``python -m portfolio_rebalancer``."""

from .core import Portfolio, Stock


def main() -> None:
    portfolio = Portfolio(
        stocks=[
            Stock("META", shares="2", price="300"),
            Stock("AAPL", shares="2", price="200"),
        ],
        target_allocations={"META": "0.5", "AAPL": "0.5"},
    )

    print("Proposed trades:")
    for trade in portfolio.rebalance():
        print(
            f"{trade.action:<4} {trade.ticker:<5} "
            f"{trade.quantity:f} shares (${trade.value:.2f})"
        )


if __name__ == "__main__":
    main()
