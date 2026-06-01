# -*- coding: utf-8 -*-
"""Marketing-specific post-reply business hook."""

from __future__ import annotations

from typing import Any

from agentscope.message import Msg

from qwenpaw.agents.hooks.post_reply_business import BaseBusinessPostReplyHook


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
        return callable(getattr(agent, "_final_output_parser", None))

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
            return output
        final_output_parser(output)
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
            return

        request_context = getattr(agent, "_request_context", {}) or {}
        agent_config = getattr(agent, "_agent_config", None)
        agent_id = request_context.get("agent_id") or getattr(
            agent_config,
            "id",
            None,
        )
        if agent_id not in MARKETING_RESULT_AGENT_IDS:
            return

        from backend.scenes.marketing.persistence import (
            MarketingStructuredResultPersistence,
        )

        MarketingStructuredResultPersistence().persist_message(
            output,
            session_id=request_context.get("session_id"),
            agent_id=agent_id,
        )
