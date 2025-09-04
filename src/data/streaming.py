"""Utilities for streaming market data into application state."""
from __future__ import annotations

import json
from typing import Iterable
from types import SimpleNamespace

from src.graph.state import AgentState

try:  # pragma: no cover - handled in tests via mocking
    import websockets as _websockets  # type: ignore
except Exception:  # pragma: no cover
    _websockets = SimpleNamespace()

websockets = _websockets


async def stream_prices(tickers: Iterable[str], state: AgentState, url: str = "ws://localhost"):
    """Connect to a WebSocket feed and push price updates into ``state``.

    The function subscribes to ``tickers`` and stores the latest price for
    each ticker under ``state['data']['prices']``.
    """
    if not hasattr(websockets, "connect"):
        raise ImportError("websockets package is required for streaming")

    async with websockets.connect(url) as ws:  # type: ignore[attr-defined]
        await ws.send(json.dumps({"type": "subscribe", "tickers": list(tickers)}))
        async for message in ws:
            data = json.loads(message)
            ticker = data.get("ticker")
            price = data.get("price")
            if ticker is None or price is None:
                continue
            state.setdefault("data", {}).setdefault("prices", {})[ticker] = price
