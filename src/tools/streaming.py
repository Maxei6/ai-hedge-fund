"""Simple websocket streaming client.

The client connects to a websocket endpoint and forwards any received
JSON messages to a user provided handler.  The handler can mutate
application state, execute trades or perform any other side effect.  The
client is intentionally tiny but fully asynchronous which makes it easy
to test using the ``websockets`` library.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, Optional

import websockets

MessageHandler = Callable[[Dict[str, Any]], None]


class WebSocketStreamClient:
    """Connect to a websocket and stream messages to a handler."""

    def __init__(
        self,
        url: str,
        handler: MessageHandler,
        max_messages: Optional[int] = None,
    ) -> None:
        self.url = url
        self.handler = handler
        self.max_messages = max_messages

    async def listen(self) -> None:
        """Listen for messages until ``max_messages`` is reached."""

        count = 0
        async with websockets.connect(self.url) as websocket:
            async for message in websocket:
                data = json.loads(message)
                self.handler(data)
                count += 1
                if self.max_messages and count >= self.max_messages:
                    break

    def start(self) -> None:
        """Synchronously start listening to the websocket."""

        asyncio.run(self.listen())


__all__ = ["WebSocketStreamClient"]

