import asyncio
import json
import sys
import types

import pytest
import websockets

# Stub out heavy optional LLM dependencies before importing portfolio manager
sys.modules.setdefault("langchain_anthropic", types.SimpleNamespace(ChatAnthropic=object))
sys.modules.setdefault("langchain_deepseek", types.SimpleNamespace(ChatDeepSeek=object))
sys.modules.setdefault(
    "langchain_google_genai", types.SimpleNamespace(ChatGoogleGenerativeAI=object)
)
sys.modules.setdefault("langchain_groq", types.SimpleNamespace(ChatGroq=object))
sys.modules.setdefault("langchain_xai", types.SimpleNamespace(ChatXAI=object))
sys.modules.setdefault(
    "langchain_openai", types.SimpleNamespace(ChatOpenAI=object, AzureChatOpenAI=object)
)
sys.modules.setdefault("langchain_gigachat", types.SimpleNamespace(GigaChat=object))
sys.modules.setdefault("langchain_ollama", types.SimpleNamespace(ChatOllama=object))

from src.agents.portfolio_manager import (
    PortfolioDecision,
    PortfolioManagerOutput,
    portfolio_management_agent,
)
from src.broker import Broker
from src.tools.streaming import WebSocketStreamClient


class DummyBroker(Broker):
    def __init__(self) -> None:
        self.orders: list[tuple[str, int, str]] = []

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        **kwargs,
    ) -> dict:
        self.orders.append((symbol, qty, side))
        return {"symbol": symbol, "qty": qty, "side": side}


def test_websocket_streaming_and_execution():
    broker = DummyBroker()
    state: dict[str, int] = {}

    def handler(message: dict):
        state.update(message)
        if "order" in message:
            broker.submit_order(**message["order"])

    async def ws_handler(websocket):
        await websocket.send(json.dumps({"price": 100}))
        await websocket.send(
            json.dumps({"order": {"symbol": "AAPL", "qty": 5, "side": "buy"}})
        )
        await asyncio.sleep(0.1)

    async def runner():
        server = await websockets.serve(ws_handler, "localhost", 0)
        port = server.sockets[0].getsockname()[1]

        client = WebSocketStreamClient(f"ws://localhost:{port}", handler, max_messages=2)
        await client.listen()

        server.close()
        await server.wait_closed()

    asyncio.run(runner())

    assert state["price"] == 100
    assert broker.orders == [("AAPL", 5, "buy")]


def test_portfolio_manager_executes_via_broker(monkeypatch):
    broker = DummyBroker()

    state = {
        "messages": [],
        "data": {
            "portfolio": {},
            "analyst_signals": {
                "risk_management_agent": {
                    "AAPL": {
                        "remaining_position_limit": 1000,
                        "current_price": 10,
                    }
                }
            },
            "tickers": ["AAPL"],
        },
        "metadata": {
            "show_reasoning": False,
            "live_trading": True,
            "broker": broker,
        },
    }

    decisions = PortfolioManagerOutput(
        decisions={
            "AAPL": PortfolioDecision(
                action="buy", quantity=1, confidence=1.0, reasoning="test"
            )
        }
    )

    monkeypatch.setattr(
        "src.agents.portfolio_manager.generate_trading_decision", lambda **_: decisions
    )

    portfolio_management_agent(state)

    assert broker.orders == [("AAPL", 1, "buy")]

