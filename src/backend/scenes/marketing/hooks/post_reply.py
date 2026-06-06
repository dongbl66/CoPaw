# -*- coding: utf-8 -*-
"""Marketing-specific post-reply business hook."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from qwenpaw.agents.hooks.post_reply_business import BaseBusinessPostReplyHook

logger = logging.getLogger(__name__)

MARKETING_RESULT_AGENT_IDS = frozenset({"market_agent", "RA-agent"})


class MarketingPostReplyHook(BaseBusinessPostReplyHook):
    """Apply marketing output parsing and persistence after a reply."""

    def should_handle(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> bool:
        """Handle replies whenever a final output parser is configured."""

        del kwargs, output
        has_parser = callable(getattr(agent, "_final_output_parser", None))
        agent_id = BaseBusinessPostReplyHook._agent_id(agent)
        logger.info(
            "[hook:marketing] agent_id=%s should_handle=%s (has parser=%s)",
            agent_id,
            has_parser,
            has_parser,
        )
        return has_parser

    async def apply_metadata(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Apply the configured final output parser to the marketing reply."""

        del kwargs
        final_output_parser = getattr(agent, "_final_output_parser", None)
        if final_output_parser is None:
            logger.info(
                "[hook:marketing] apply_metadata: final_output_parser is None, skip"
            )
            return output
        logger.info(
            "[hook:marketing] apply_metadata: calling final_output_parser (%s)",
            final_output_parser.__name__,
        )
        final_output_parser(output)
        has_structured = isinstance(
            output.metadata.get("structured_result") if isinstance(output.metadata, dict) else None,
            dict,
        )
        logger.info(
            "[hook:marketing] apply_metadata: done, has_structured_result=%s",
            has_structured,
        )
        return output

    async def persist(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> None:
        """Persist structured marketing results after parsing succeeds."""

        del kwargs
        metadata = output.metadata if isinstance(output.metadata, dict) else {}
        if not isinstance(metadata.get("structured_result"), dict):
            logger.info(
                "[hook:marketing] persist: no structured_result in metadata, skip"
            )
            return

        request_context = getattr(agent, "_request_context", {}) or {}
        agent_config = getattr(agent, "_agent_config", None)
        agent_id = request_context.get("agent_id") or getattr(
            agent_config,
            "id",
            None,
        )
        if agent_id not in MARKETING_RESULT_AGENT_IDS:
            logger.info(
                "[hook:marketing] persist: agent_id=%s not in allowed set %s, skip",
                agent_id,
                set(MARKETING_RESULT_AGENT_IDS),
            )
            return

        logger.info(
            "[hook:marketing] persist: persisting for agent_id=%s session_id=%s",
            agent_id,
            request_context.get("session_id"),
        )

        from backend.scenes.marketing.persistence import (
            MarketingStructuredResultPersistence,
        )

        MarketingStructuredResultPersistence().persist_message(
            output,
            session_id=request_context.get("session_id"),
            agent_id=agent_id,
        )
