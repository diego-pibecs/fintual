from decimal import Decimal

import pytest

from portfolio_rebalancer import Portfolio, Stock, Trade
from portfolio_rebalancer.__main__ import main


def test_example_runner_prints_proposed_trades(capsys) -> None:
    main()

    assert capsys.readouterr().out.splitlines() == [
        "Proposed trades:",
        "BUY  AAPL  0.5 shares ($100.00)",
        "SELL META  0.3333333333333333333333333333 shares ($100.00)",
    ]


def test_rebalance_proposes_buys_and_sells_with_fractional_shares() -> None:
    portfolio = Portfolio(
        stocks=[
            Stock("META", shares="2", price="300"),
            Stock("AAPL", shares="2", price="200"),
        ],
        target_allocations={"META": "0.5", "AAPL": "0.5"},
    )

    assert portfolio.rebalance() == [
        Trade("BUY", "AAPL", Decimal("0.5"), Decimal("100.0")),
        Trade("SELL", "META", Decimal("0.3333333333333333333333333333"), Decimal("100.0")),
    ]


def test_already_balanced_portfolio_requires_no_trades() -> None:
    portfolio = Portfolio(
        stocks=[
            Stock("META", shares="1", price="400"),
            Stock("AAPL", shares="4", price="150"),
        ],
        target_allocations={"META": "0.4", "AAPL": "0.6"},
    )

    assert portfolio.rebalance() == []


def test_zero_share_position_can_be_bought() -> None:
    portfolio = Portfolio(
        stocks=[
            Stock("META", shares="0", price="400"),
            Stock("AAPL", shares="4", price="150"),
        ],
        target_allocations={"META": "0.4", "AAPL": "0.6"},
    )

    assert portfolio.rebalance() == [
        Trade("SELL", "AAPL", Decimal("1.6"), Decimal("240.0")),
        Trade("BUY", "META", Decimal("0.6"), Decimal("240.0")),
    ]


def test_empty_portfolio_requires_no_trades() -> None:
    assert Portfolio([], {}).rebalance() == []


def test_portfolio_with_no_invested_value_requires_no_trades() -> None:
    portfolio = Portfolio(
        stocks=[Stock("META", shares="0", price="400")],
        target_allocations={"META": "1"},
    )

    assert portfolio.rebalance() == []


def test_zero_target_allocation_sells_the_entire_position() -> None:
    portfolio = Portfolio(
        stocks=[
            Stock("META", shares="1", price="100"),
            Stock("AAPL", shares="0", price="50"),
        ],
        target_allocations={"META": "0", "AAPL": "1"},
    )

    assert portfolio.rebalance() == [
        Trade("BUY", "AAPL", Decimal("2"), Decimal("100")),
        Trade("SELL", "META", Decimal("1"), Decimal("100")),
    ]


@pytest.mark.parametrize("price", ["0", "-1", "NaN", "Infinity", "not-a-price"])
def test_invalid_prices_are_rejected(price: str) -> None:
    with pytest.raises(ValueError):
        Stock("META", shares="1", price=price)


@pytest.mark.parametrize("shares", ["-1", "NaN", "Infinity", "not-a-quantity"])
def test_invalid_share_quantities_are_rejected(shares: str) -> None:
    with pytest.raises(ValueError):
        Stock("META", shares=shares, price="100")


@pytest.mark.parametrize(
    ("stocks", "allocations"),
    [
        ([Stock("META", "1", "100")], {"META": "0.9"}),
        ([Stock("META", "1", "100")], {"META": "-0.1"}),
        ([Stock("META", "1", "100")], {"META": "NaN"}),
        ([Stock("META", "1", "100")], {"AAPL": "1"}),
        ([], {"META": "1"}),
    ],
)
def test_invalid_allocations_are_rejected(stocks, allocations) -> None:
    with pytest.raises(ValueError):
        Portfolio(stocks, allocations)


def test_duplicate_stocks_are_rejected_after_ticker_normalization() -> None:
    with pytest.raises(ValueError, match="duplicate stock ticker"):
        Portfolio(
            [Stock("META", "1", "100"), Stock(" meta ", "1", "100")],
            {"META": "1"},
        )


def test_numeric_inputs_are_stored_as_decimals_and_ticker_is_normalized() -> None:
    stock = Stock(" meta ", shares=1.5, price=100)

    assert stock.ticker == "META"
    assert stock.shares == Decimal("1.5")
    assert stock.current_price() == Decimal("100")
