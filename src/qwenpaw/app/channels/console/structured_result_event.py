# -*- coding: utf-8 -*-
"""Helpers for pushing structured result events to console SSE clients."""

from __future__ import annotations

from typing import Any


class StructuredResultPushEventFactory:
    """Build dedicated SSE payloads for structured results."""

    def build_from_response_output(
        self,
        *,
        session_id: str,
        output_messages: list[Any] | None,
    ) -> list[dict[str, Any]]:
        """Extract structured_result events from response output messages."""

        events: list[dict[str, Any]] = []
        for message in output_messages or []:
            metadata = getattr(message, "metadata", None)
            if not isinstance(metadata, dict):
                continue
            structured_result = metadata.get("structured_result")
            if not isinstance(structured_result, dict):
                continue
            if structured_result.get("eventType") != "structured_result":
                continue
            events.append(
                {
                    "object": "structured_result_event",
                    "status": "completed",
                    "session_id": session_id,
                    "message_id": getattr(message, "id", None),
                    "structured_result": structured_result,
                },
            )
        return events
