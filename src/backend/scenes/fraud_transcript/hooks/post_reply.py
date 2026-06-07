# -*- coding: utf-8 -*-
"""Fraud transcript-specific post-reply business hook."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from backend.scenes.fraud_transcript.parsers.transcript_report import (
    FRAUD_TRANSCRIPT_BIZ_MODULE,
    is_valid_fraud_transcript_structured_result,
)
from qwenpaw.agents.hooks.post_reply_business import BaseBusinessPostReplyHook

logger = logging.getLogger(__name__)
FRAUD_TRANSCRIPT_AGENT_IDS = frozenset({"fraud_transcript_agent"})


class FraudTranscriptPostReplyHook(BaseBusinessPostReplyHook):
    """Apply fraud transcript output parsing and persistence after a reply."""

    def should_handle(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> bool:
        del kwargs
        if self._agent_id(agent) in FRAUD_TRANSCRIPT_AGENT_IDS:
            return True
        metadata = output.metadata if isinstance(output.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if is_valid_fraud_transcript_structured_result(structured_result):
            return True
        parser = getattr(agent, "_final_output_parser", None)
        return callable(parser) and "fraud_transcript" in getattr(
            parser,
            "__module__",
            "",
        )

    async def apply_metadata(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        del kwargs
        parser = getattr(agent, "_final_output_parser", None)
        if callable(parser):
            parser(output)
        return output

    async def persist(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> None:
        del kwargs
        metadata = output.metadata if isinstance(output.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if not is_valid_fraud_transcript_structured_result(structured_result):
            logger.debug("Skip fraud transcript hook persist: invalid payload")
            return

        request_context = getattr(agent, "_request_context", {}) or {}
        agent_config = getattr(agent, "_agent_config", None)
        agent_id = request_context.get("agent_id") or getattr(
            agent_config,
            "id",
            None,
        )
        meta = structured_result.get("meta") if isinstance(structured_result, dict) else {}
        if (
            agent_id not in FRAUD_TRANSCRIPT_AGENT_IDS
            and meta.get("bizModule") != FRAUD_TRANSCRIPT_BIZ_MODULE
        ):
            return

        from backend.scenes.fraud_transcript.persistence import (
            FraudTranscriptStructuredResultPersistence,
        )

        FraudTranscriptStructuredResultPersistence().persist_message(
            output,
            session_id=request_context.get("session_id"),
            agent_id=agent_id,
        )
