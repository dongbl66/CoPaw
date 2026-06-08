# -*- coding: utf-8 -*-
"""Persistence for FAE government opportunity analysis results."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from backend.database.connection import get_backend_database

from .parsers.government_opportunity_parser import (
    government_opportunity_from_structured_result,
)
from .service import FAEOpportunityService, FAEResultService

logger = logging.getLogger(__name__)


class FAEGovernmentOpportunityPersistence:
    """Persist FAE government opportunity structured results."""

    def __init__(self) -> None:
        backend_database = get_backend_database()
        self._opportunity_service = FAEOpportunityService(backend_database)
        self._result_service = FAEResultService(backend_database)

    def persist_message(
        self,
        msg: Msg,
        *,
        session_id: str | None,
        agent_id: str | None = None,
    ) -> None:
        """Persist government opportunity data into opportunity/result tables."""

        metadata = msg.metadata if isinstance(msg.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if not isinstance(structured_result, dict):
            logger.debug("FAEPersistence: no structured_result, skipping")
            return

        gov_opportunity = metadata.get("government_opportunity")
        if not isinstance(gov_opportunity, dict):
            gov_opportunity = government_opportunity_from_structured_result(
                structured_result,
            )
        if not gov_opportunity:
            logger.debug("FAEPersistence: no government opportunity data")
            return

        try:
            opportunity = self._opportunity_service.create_opportunity(
                {
                    **gov_opportunity,
                    "session_id": session_id,
                    "agent_id": agent_id or "RA-agent",
                },
            )
            opportunity_id = int(opportunity["id"])
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("FAEPersistence: failed to create opportunity: %s", exc)
            return

        result = structured_result.get("result")
        if not isinstance(result, dict):
            return
        payload = result.get("payload")
        if not isinstance(payload, dict):
            payload = {}

        title = (
            gov_opportunity.get("project_name")
            or structured_result.get("title")
            or "FAE Opportunity Analysis"
        )
        summary = (
            gov_opportunity.get("output")
            or payload.get("summary")
            or _message_text(msg)
        )

        try:
            result_record = self._result_service.create_result(
                title=str(title).strip(),
                result_type=str(result.get("type", "government_opportunity")),
                scene=str(payload.get("scene") or "government_opportunity"),
                summary=str(summary).strip() if summary else None,
                detail_content=self._build_detail_content(gov_opportunity),
                info={
                    "messageContent": getattr(msg, "content", None),
                    "structuredResult": structured_result,
                    "payload": payload,
                    "opportunityId": opportunity_id,
                },
                basic_info=gov_opportunity,
                session_id=session_id,
                agent_id=agent_id or "RA-agent",
            )
            logger.info(
                "FAEPersistence: created result id=%s opportunity_id=%s",
                result_record["id"],
                opportunity_id,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("FAEPersistence: failed to create result: %s", exc)

    @staticmethod
    def _build_detail_content(
        gov_opportunity: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build display_content list from attachment data."""

        display_content = gov_opportunity.get("display_content")
        if isinstance(display_content, list):
            return [item for item in display_content if isinstance(item, dict)]
        return []


def _message_text(msg: Msg) -> str:
    if isinstance(msg.content, str):
        return msg.content
    if isinstance(msg.content, list):
        return "\n".join(
            block.get("text", "")
            for block in msg.content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
    return ""
