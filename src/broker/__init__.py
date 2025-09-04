"""Broker interfaces and implementations.

This module defines a simple broker abstraction used by the trading
agents.  It currently ships with an :class:`AlpacaBroker` implementation
that proxies requests to the helper functions in
``src.tools.alpaca_trading``.  The interface is intentionally small and
focused on order submission which keeps the tests light weight while
making the rest of the codebase agnostic to the underlying broker.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.tools import alpaca_trading


class Broker(ABC):
    """Abstract base class for brokers."""

    @abstractmethod
    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Submit an order and return the broker response."""


class AlpacaBroker(Broker):
    """Broker implementation using the Alpaca trading API."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return alpaca_trading.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url=self.base_url,
            **kwargs,
        )


__all__ = ["Broker", "AlpacaBroker"]

