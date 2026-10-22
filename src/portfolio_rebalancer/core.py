"""Core portfolio rebalancing types and calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Iterable, Literal, Mapping, TypeAlias


DecimalInput: TypeAlias = Decimal | int | float | str
TradeAction: TypeAlias = Literal["BUY", "SELL"]


def _to_decimal(value: DecimalInput, field_name: str) -> Decimal:
    """Convert user input without importing a float's binary representation."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number")

    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc

    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return result


def _normalize_ticker(ticker: str) -> str:
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("ticker must be a non-empty string")
    return ticker.strip().upper()


@dataclass(frozen=True, slots=True, init=False)
class Stock:
    """A position and the latest known price for one security."""

    ticker: str
    shares: Decimal
    price: Decimal

    def __init__(
        self,
        ticker: str,
        shares: DecimalInput,
        price: DecimalInput,
    ) -> None:
        normalized_ticker = _normalize_ticker(ticker)
        decimal_shares = _to_decimal(shares, "shares")
        decimal_price = _to_decimal(price, "price")

        if decimal_shares < 0:
            raise ValueError("shares cannot be negative")
        if decimal_price <= 0:
            raise ValueError("price must be greater than zero")

        object.__setattr__(self, "ticker", normalized_ticker)
        object.__setattr__(self, "shares", decimal_shares)
        object.__setattr__(self, "price", decimal_price)

    def current_price(self) -> Decimal:
        """Return the last available price supplied when the Stock was created."""
        return self.price


@dataclass(frozen=True, slots=True)
class Trade:
    """A proposed trade. Quantity and value are always positive."""

    action: TradeAction
    ticker: str
    quantity: Decimal
    value: Decimal


class Portfolio:
    """A collection of positions and their desired portfolio weights."""

    def __init__(
        self,
        stocks: Iterable[Stock],
        target_allocations: Mapping[str, DecimalInput],
    ) -> None:
        positions = tuple(stocks)
        if any(not isinstance(stock, Stock) for stock in positions):
            raise TypeError("stocks must contain only Stock instances")

        by_ticker: dict[str, Stock] = {}
        for stock in positions:
            if stock.ticker in by_ticker:
                raise ValueError(f"duplicate stock ticker: {stock.ticker}")
            by_ticker[stock.ticker] = stock

        allocations: dict[str, Decimal] = {}
        for ticker, allocation in target_allocations.items():
            normalized_ticker = _normalize_ticker(ticker)
            if normalized_ticker in allocations:
                raise ValueError(f"duplicate allocation ticker: {normalized_ticker}")

            weight = _to_decimal(allocation, f"allocation for {normalized_ticker}")
            if not Decimal("0") <= weight <= Decimal("1"):
                raise ValueError("allocations must be between 0 and 1")
            allocations[normalized_ticker] = weight

        if set(by_ticker) != set(allocations):
            raise ValueError("every stock must have exactly one target allocation")

        expected_total = Decimal("0") if not positions else Decimal("1")
        if sum(allocations.values(), Decimal("0")) != expected_total:
            raise ValueError(f"target allocations must sum to {expected_total}")

        # Copy inputs so later mutations by callers cannot change a rebalance.
        self._stocks = positions
        self._target_allocations = MappingProxyType(allocations)

    @property
    def stocks(self) -> tuple[Stock, ...]:
        return self._stocks

    @property
    def target_allocations(self) -> Mapping[str, Decimal]:
        return self._target_allocations

    def rebalance(self) -> list[Trade]:
        """Return trades that move current holdings to the target allocations."""
        if not self._stocks:
            return []

        current_values = {
            stock.ticker: stock.shares * stock.current_price()
            for stock in self._stocks
        }
        total_value = sum(current_values.values(), Decimal("0"))

        # With no invested value and no external cash, there is nothing to trade.
        if total_value == 0:
            return []

        trades: list[Trade] = []
        for stock in sorted(self._stocks, key=lambda position: position.ticker):
            target_value = total_value * self._target_allocations[stock.ticker]
            difference = target_value - current_values[stock.ticker]
            if difference == 0:
                continue

            trade_value = abs(difference)
            trades.append(
                Trade(
                    action="BUY" if difference > 0 else "SELL",
                    ticker=stock.ticker,
                    quantity=trade_value / stock.current_price(),
                    value=trade_value,
                )
            )

        return trades
