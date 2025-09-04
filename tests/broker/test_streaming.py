import asyncio
import json
from unittest.mock import patch

from src.data.streaming import stream_prices


class DummyWebSocket:
    def __init__(self, messages):
        self.messages = messages
        self.sent = []

    async def send(self, message):
        self.sent.append(message)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __aiter__(self):
        async def gen():
            for m in self.messages:
                yield m
        return gen()

def test_stream_prices_updates_state():
    messages = [json.dumps({"ticker": "AAPL", "price": 150}), json.dumps({"ticker": "TSLA", "price": 200})]
    state = {"messages": [], "data": {}, "metadata": {}}
    ws = DummyWebSocket(messages)

    async def run():
        with patch("src.data.streaming.websockets.connect", return_value=ws):
            await stream_prices(["AAPL", "TSLA"], state, url="ws://test")

    asyncio.run(run())

    assert state["data"]["prices"] == {"AAPL": 150, "TSLA": 200}
    assert json.loads(ws.sent[0]) == {"type": "subscribe", "tickers": ["AAPL", "TSLA"]}
