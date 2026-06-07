# -*- coding: utf-8 -*-
"""Automatic persistence for fraud transcript structured results."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from backend.database.connection import BackendDatabase, get_backend_database
from backend.scenes.fraud_transcript.parsers.transcript_report import (
    FRAUD_TRANSCRIPT_BIZ_MODULE,
    FRAUD_TRANSCRIPT_SCENE,
    is_valid_fraud_transcript_structured_result,
)

from .service import FraudTranscriptResultService

logger = logging.getLogger(__name__)


class FraudTranscriptStructuredResultPersistence:
    """Persist structured fraud transcript reports into SQLite."""

    def __init__(self, database: BackendDatabase | None = None) -> None:
        self._service = FraudTranscriptResultService(
            database or get_backend_database(),
        )

    def persist_message(
        self,
        msg: Msg,
        *,
        session_id: str | None,
        agent_id: str | None,
    ) -> None:
        metadata = msg.metadata if isinstance(msg.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if not is_valid_fraud_transcript_structured_result(structured_result):
            logger.debug("Skip fraud transcript persist: invalid structured_result")
            return

        business_result = metadata.get("business_result")
        if not isinstance(business_result, dict):
            business_result = {}

        payload = structured_result["result"]["payload"]
        meta = structured_result.get("meta") or {}
        if (
            payload.get("scene") != FRAUD_TRANSCRIPT_SCENE
            or meta.get("bizModule") != FRAUD_TRANSCRIPT_BIZ_MODULE
        ):
            return

        self._service.create_result(
            title=_first_text(payload, "title")
            or _first_text(structured_result, "title")
            or "Fraud transcript report",
            result_type="business",
            scene=FRAUD_TRANSCRIPT_SCENE,
            summary=_first_text(payload, "summary")
            or _first_text(business_result, "summary"),
            basic_info=_as_dict(business_result.get("basic_info"))
            or _as_dict(payload.get("basicInfo")),
            product_info=_as_dict(business_result.get("product_info"))
            or _as_dict(payload.get("productInfo")),
            qa_records=_as_list_of_dicts(business_result.get("opportunities"))
            or _as_list_of_dicts(payload.get("opportunities")),
            structured_result=structured_result,
            session_id=session_id,
            agent_id=agent_id,
        )


def _first_text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

