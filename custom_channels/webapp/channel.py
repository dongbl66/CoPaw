# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Optional

from agentscope_runtime.engine.schemas.agent_schemas import (
    ContentType,
    RunStatus,
    TextContent,
)

from qwenpaw.app.channels.base import BaseChannel, OnReplySent, ProcessHandler
from qwenpaw.app.channels.schema import ChannelType

from .session_resolver import build_session_id


class WebAppChannel(BaseChannel):
    channel: ChannelType = "webapp"

    def __init__(
        self,
        process: ProcessHandler,
        enabled: bool = True,
        bot_prefix: str = "",
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
        **_kwargs: Any,
    ) -> None:
        super().__init__(
            process,
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
        )
        self.enabled = enabled
        self.bot_prefix = bot_prefix

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: Any,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
        **kwargs: Any,
    ) -> "WebAppChannel":
        return cls(
            process=process,
            enabled=getattr(config, "enabled", True),
            bot_prefix=getattr(config, "bot_prefix", ""),
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
            **kwargs,
        )

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
        **kwargs: Any,
    ) -> "WebAppChannel":
        return cls(
            process=process,
            on_reply_sent=on_reply_sent,
            **kwargs,
        )

    def resolve_session_id(
        self,
        sender_id: str,
        channel_meta: Optional[dict[str, Any]] = None,
    ) -> str:
        meta = channel_meta or {}
        explicit = str(meta.get("session_id") or "").strip()
        if explicit:
            return explicit
        return build_session_id(
            scene=str(meta.get("scene") or "default"),
            user_id=sender_id,
            conversation_id=str(meta.get("conversation_id") or "default"),
        )

    def build_agent_request_from_native(self, native_payload: Any):
        payload = native_payload if isinstance(native_payload, dict) else {}
        channel_id = str(payload.get("channel_id") or self.channel)
        sender_id = str(payload.get("sender_id") or "")
        meta = dict(payload.get("meta") or {})
        text = str(payload.get("text") or "")
        session_id = self.resolve_session_id(sender_id, meta)
        content_parts = [TextContent(type=ContentType.TEXT, text=text or " ")]
        request = self.build_agent_request_from_user_content(
            channel_id=channel_id,
            sender_id=sender_id,
            session_id=session_id,
            content_parts=content_parts,
            channel_meta=meta,
        )
        request.channel_meta = meta
        return request

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        return None

    async def stream_one(self, payload: Any) -> AsyncGenerator[str, None]:
        request = self.build_agent_request_from_native(payload)
        meta = getattr(request, "channel_meta", None) or {}
        conversation_id = str(meta.get("conversation_id") or "")
        msg_id_to_stream_type: dict[str, str] = {}
        buffers: dict[str, str] = {}
        try:
            async for event in self._process(request):
                obj = getattr(event, "object", None)
                status = getattr(event, "status", None)
                if obj == "message" and status == RunStatus.InProgress:
                    stream_type = self._resolve_stream_type(event)
                    msg_id = str(getattr(event, "id", "") or "")
                    if stream_type in {"message", "reasoning"} and msg_id:
                        msg_id_to_stream_type[msg_id] = stream_type
                        buffers[stream_type] = ""
                    continue
                if obj == "content" and status == RunStatus.InProgress:
                    if not getattr(event, "delta", False):
                        continue
                    msg_id = str(getattr(event, "msg_id", "") or "")
                    stream_type = msg_id_to_stream_type.get(msg_id, "")
                    if not stream_type:
                        continue
                    delta_text = str(getattr(event, "text", "") or "")
                    buffers[stream_type] = buffers.get(stream_type, "") + delta_text
                    yield (
                        "data: "
                        + json.dumps(
                            {
                                "type": "assistant_delta",
                                "conversation_id": conversation_id,
                                "message_id": msg_id,
                                "stream_type": stream_type,
                                "delta": delta_text,
                                "accumulated_text": buffers[stream_type],
                            },
                            ensure_ascii=False,
                        )
                        + "\n\n"
                    )
                    continue
                if obj == "message" and status == RunStatus.Completed:
                    msg_id = str(getattr(event, "id", "") or "")
                    msg_id_to_stream_type.pop(msg_id, None)
                if (
                    obj == "response"
                    and status == RunStatus.Completed
                ):
                    yield (
                        "data: "
                        + json.dumps(
                            {
                                "type": "assistant_final",
                                "conversation_id": conversation_id,
                                "message_id": _extract_message_id(event),
                                "text": self._response_to_text(event),
                            },
                            ensure_ascii=False,
                        )
                        + "\n\n"
                    )
        except Exception as exc:  # pragma: no cover - defensive fallback
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "assistant_error",
                        "conversation_id": conversation_id,
                        "error": str(exc).strip() or "internal server error",
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )


def build_config_namespace(scene: str) -> SimpleNamespace:
    return SimpleNamespace(
        enabled=True,
        bot_prefix="",
        scene=scene,
    )


def _extract_message_id(event: Any) -> str:
    output = getattr(event, "output", None) or []
    if not output:
        return ""
    return str(getattr(output[0], "id", "") or "")
