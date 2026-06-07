# -*- coding: utf-8 -*-
"""Parser for fraud transcript structured-result events."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agentscope.message import Msg

logger = logging.getLogger(__name__)

FRAUD_TRANSCRIPT_SCENE = "fraud_transcript_report"
FRAUD_TRANSCRIPT_BIZ_MODULE = "fraud_transcript"


def inject_fraud_transcript_metadata(msg: Msg) -> None:
    """Extract and validate one fraud transcript StructuredResultEvent."""

    if not isinstance(msg.metadata, dict):
        msg.metadata = {}
    event = _extract_structured_result(_message_text(msg))
    if not _is_valid_fraud_transcript_event(event):
        return

    payload = event["result"]["payload"]
    msg.metadata["structured_result"] = event
    msg.metadata["business_result"] = {
        "title": payload.get("title"),
        "summary": payload.get("summary"),
        "basic_info": _as_dict(payload.get("basicInfo")),
        "product_info": _as_dict(payload.get("productInfo")),
        "opportunities": _as_list_of_dicts(payload.get("opportunities")),
        "display_content": _as_list_of_dicts(payload.get("attachments")),
    }
    logger.info("Injected fraud transcript structured result metadata")


def is_valid_fraud_transcript_structured_result(value: Any) -> bool:
    """Return True when value is a valid fraud transcript structured result."""

    return _is_valid_fraud_transcript_event(value)


def _message_text(msg: Msg) -> str:
    if isinstance(msg.content, str):
        return msg.content.strip()
    if isinstance(msg.content, list):
        blocks = [
            block.get("text", "")
            for block in msg.content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
        return "\n".join(blocks).strip()
    return ""


def _extract_structured_result(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    candidates = [
        match.group(1).strip()
        for match in re.finditer(
            r"```(?:json)?\s*([\s\S]*?)\s*```",
            text,
            flags=re.IGNORECASE,
        )
        if match.group(1).strip()
    ]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    candidates.append(text)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _is_valid_fraud_transcript_event(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("eventType") != "structured_result":
        return False
    result = value.get("result")
    if not isinstance(result, dict) or result.get("type") != "business":
        return False
    payload = result.get("payload")
    if not isinstance(payload, dict):
        return False
    if payload.get("scene") != FRAUD_TRANSCRIPT_SCENE:
        return False
    meta = value.get("meta")
    return isinstance(meta, dict) and meta.get("bizModule") == FRAUD_TRANSCRIPT_BIZ_MODULE


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
