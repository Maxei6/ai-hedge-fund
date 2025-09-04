"""Broker interface definitions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BrokerBase(ABC):
    """Abstract broker interface."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to broker API."""

    @abstractmethod
    def place_order(self, symbol: str, qty: int, side: str, order_type: str = "market") -> Any:
        """Place an order and return broker-specific response."""

    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """Return current positions."""
