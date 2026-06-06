# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WebAppWsHub:
    """Minimal in-memory websocket hub for webapp scene clients."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._token_context: dict[str, dict[str, Any]] = {}
        self._conversation_index: dict[str, str] = {}

    def register_token_context(self, token: str, context: dict[str, Any]) -> None:
        self._token_context[token] = dict(context)
        conversation_id = str(context.get("conversation_id") or "").strip()
        if conversation_id:
            self._conversation_index[conversation_id] = token

    def get_token_context(self, token: str) -> dict[str, Any] | None:
        context = self._token_context.get(token)
        return dict(context) if context else None

    def get_context_by_conversation(
        self,
        conversation_id: str,
    ) -> dict[str, Any] | None:
        token = self._conversation_index.get(conversation_id)
        if not token:
            return None
        return self.get_token_context(token)

    async def connect(self, token: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[token].add(websocket)

    async def disconnect(self, token: str, websocket: WebSocket) -> None:
        self._connections.get(token, set()).discard(websocket)
        if token in self._connections and not self._connections[token]:
            self._connections.pop(token, None)

    async def send_hello(self, websocket: WebSocket) -> None:
        await websocket.send_json(
            {
                "type": "hello",
                "status": "connected",
            },
        )

    async def broadcast(self, token: str, payload: dict[str, Any]) -> None:
        for websocket in tuple(self._connections.get(token, set())):
            await websocket.send_json(payload)
