# -*- coding: utf-8 -*-
"""FAE-specific post-reply business hook for RA-agent."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from qwenpaw.agents.hooks.post_reply_business import BaseBusinessPostReplyHook

logger = logging.getLogger(__name__)
FAE_AGENT_IDS = frozenset({"RA-agent"})


class FAEPostReplyHook(BaseBusinessPostReplyHook):
    """Apply FAE output parsing and persistence after an RA-agent reply."""

    def should_handle(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> bool:
        """Handle RA-agent replies that carry government opportunity data."""

        del kwargs
        agent_id = self._resolve_agent_id(agent)
        if agent_id not in FAE_AGENT_IDS:
            logger.debug(
                "FAEPostReplyHook: agent_id=%s not in FAE list, skipping",
                agent_id,
            )
            return False

        has_parser = callable(getattr(agent, "_final_output_parser", None))
        logger.debug(
            "FAEPostReplyHook.should_handle: agent_id=%s, has_parser=%s",
            agent_id,
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
        """Parse government opportunity metadata from the RA-agent reply."""

        del kwargs
        logger.debug("FAEPostReplyHook.apply_metadata: starting")

        final_output_parser = getattr(agent, "_final_output_parser", None)
        if final_output_parser is None:
            logger.debug("FAEPostReplyHook.apply_metadata: no parser configured")
            return output

        final_output_parser(output)
        logger.debug(
            "FAEPostReplyHook.apply_metadata: done, metadata keys=%s",
            list(output.metadata.keys()) if isinstance(output.metadata, dict) else "N/A",
        )
        return output

    async def persist(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> None:
        """Persist FAE government opportunity data."""

        del kwargs
        logger.debug("FAEPostReplyHook.persist: starting")

        metadata = output.metadata if isinstance(output.metadata, dict) else {}
        if not isinstance(metadata.get("government_opportunity"), dict):
            logger.debug("FAEPostReplyHook.persist: no government_opportunity in metadata")
            return

        # Structured result 持久化委托给通用 persistence
        if not isinstance(metadata.get("structured_result"), dict):
            logger.debug("FAEPostReplyHook.persist: no structured_result in metadata")
            return

        request_context = getattr(agent, "_request_context", {}) or {}
        session_id = request_context.get("session_id")

        from backend.scenes.fae.persistence import (
            FAEGovernmentOpportunityPersistence,
        )

        FAEGovernmentOpportunityPersistence().persist_message(
            output,
            session_id=session_id,
        )
        logger.info("FAEPostReplyHook.persist: done")

    @staticmethod
    def _resolve_agent_id(agent: Any) -> str | None:
        """Resolve agent ID from request context or config."""

        request_context = getattr(agent, "_request_context", {}) or {}
        agent_id = request_context.get("agent_id")
        if agent_id:
            return agent_id
        agent_config = getattr(agent, "_agent_config", None)
        return getattr(agent_config, "id", None) if agent_config else None
