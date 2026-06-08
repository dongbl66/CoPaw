# -*- coding: utf-8 -*-
"""FAE-specific post-reply business hook for RA-agent."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from backend.scenes.fae.parsers.government_opportunity_parser import (
    FAE_BIZ_MODULE,
    is_valid_fae_structured_result,
)
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
        metadata = output.metadata if isinstance(output.metadata, dict) else {}
        if is_valid_fae_structured_result(metadata.get("structured_result")):
            return True

        agent_id = self._resolve_agent_id(agent)
        if agent_id not in FAE_AGENT_IDS:
            logger.debug(
                "FAEPostReplyHook: agent_id=%s not in FAE list, skipping",
                agent_id,
            )
            return False

        return callable(getattr(agent, "_final_output_parser", None))

    async def apply_metadata(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Parse government opportunity metadata from the RA-agent reply."""

        del kwargs
        final_output_parser = getattr(agent, "_final_output_parser", None)
        if callable(final_output_parser):
            final_output_parser(output)
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
        metadata = output.metadata if isinstance(output.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if not is_valid_fae_structured_result(structured_result):
            logger.debug("FAEPostReplyHook.persist: invalid structured_result")
            return

        request_context = getattr(agent, "_request_context", {}) or {}
        agent_config = getattr(agent, "_agent_config", None)
        agent_id = request_context.get("agent_id") or getattr(
            agent_config,
            "id",
            None,
        )
        meta = (
            structured_result.get("meta")
            if isinstance(structured_result, dict)
            else {}
        )
        if agent_id not in FAE_AGENT_IDS and meta.get("bizModule") != FAE_BIZ_MODULE:
            return

        from backend.scenes.fae.persistence import (
            FAEGovernmentOpportunityPersistence,
        )

        FAEGovernmentOpportunityPersistence().persist_message(
            output,
            session_id=request_context.get("session_id"),
            agent_id=agent_id,
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
