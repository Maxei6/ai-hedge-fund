"""Simple Alpaca broker adapter."""
from __future__ import annotations

from typing import Any, Dict

from .base import BrokerBase


class AlpacaBroker(BrokerBase):
    """Adapter around an Alpaca client instance."""

    def __init__(self, client):
        self.client = client

    def connect(self) -> None:  # pragma: no cover - simple delegation
        self.client.get_account()

    def place_order(self, symbol: str, qty: int, side: str, order_type: str = "market") -> Any:
        return self.client.submit_order(symbol=symbol, qty=qty, side=side, type=order_type)

    def get_positions(self) -> Dict[str, Any]:  # pragma: no cover - simple delegation
        positions = self.client.list_positions()
        return {p.symbol: p for p in positions}
