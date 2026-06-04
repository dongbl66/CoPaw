# -*- coding: utf-8 -*-
"""Persistence for FAE government opportunity analysis results."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from backend.database.connection import get_backend_database

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
    ) -> None:
        """Persist government opportunity data into both opportunity and result tables."""

        logger.debug(
            "FAEPersistence.persist_message: session_id=%s",
            session_id,
        )

        metadata = msg.metadata if isinstance(msg.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if not isinstance(structured_result, dict):
            logger.debug("FAEPersistence: no structured_result, skipping")
            return

        gov_opportunity = metadata.get("government_opportunity")
        if not isinstance(gov_opportunity, dict):
            logger.debug("FAEPersistence: no government_opportunity, skipping")
            return

        # ── 1. Persist to opportunity table ──
        try:
            opportunity_id = self._opportunity_service.create_opportunity(
                {**gov_opportunity, "session_id": session_id}
            )["id"]
            logger.info(
                "FAEPersistence: created opportunity id=%s, project=%s",
                opportunity_id,
                gov_opportunity.get("project_name"),
            )
        except Exception as e:
            logger.error("FAEPersistence: failed to create opportunity: %s", e)

        # ── 2. Persist to result table (for result panel polling) ──
        result = structured_result.get("result")
        if not isinstance(result, dict):
            return

        result_type = result.get("type", "government_opportunity")
        payload = result.get("payload")
        if not isinstance(payload, dict):
            payload = {}

        title = (
            gov_opportunity.get("project_name")
            or structured_result.get("title")
            or "商机分析"
        )

        try:
            result_record = self._result_service.create_result(
                title=str(title).strip(),
                result_type=str(result_type),
                scene=gov_opportunity.get("industry"),
                summary=gov_opportunity.get("output", str(msg.content)),
                detail_content=self._build_detail_content(gov_opportunity),
                info={
                    "messageContent": getattr(msg, "content", None),
                    "structuredResult": structured_result,
                    "payload": payload,
                    "opportunityId": opportunity_id,
                },
                basic_info=gov_opportunity,
                session_id=session_id,
                agent_id="RA-agent",
            )
            logger.info(
                "FAEPersistence: created result id=%s, title=%s",
                result_record["id"],
                title,
            )
        except Exception as e:
            logger.error("FAEPersistence: failed to create result: %s", e)

    @staticmethod
    def _build_detail_content(
        gov_opportunity: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build display_content list from attachment data."""

        display_content = gov_opportunity.get("display_content")
        if isinstance(display_content, list):
            return [item for item in display_content if isinstance(item, dict)]
        return []
