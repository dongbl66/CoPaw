# -*- coding: utf-8 -*-
"""Business post-reply hook orchestration for agent replies."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any, Protocol, runtime_checkable

from agentscope.message import Msg

logger = logging.getLogger(__name__)


@runtime_checkable
class PostReplyBusinessHandler(Protocol):
    """Protocol for one business post-reply handler."""

    async def handle(
        self,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Handle one post-reply action and optionally replace output."""


class BaseBusinessPostReplyHook(ABC):
    """Template-method base class for one business post-reply hook."""

    async def handle(
        self,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Run the shared business post-reply flow."""

        if not self.should_handle(agent=agent, kwargs=kwargs, output=output):
            return None

        current_output = await self.parse_output(
            agent=agent,
            kwargs=kwargs,
            output=output,
        )
        parsed_output = current_output or output

        updated_output = await self.apply_metadata(
            agent=agent,
            kwargs=kwargs,
            output=parsed_output,
        )
        final_output = updated_output or parsed_output

        await self.persist(
            agent=agent,
            kwargs=kwargs,
            output=final_output,
        )
        return final_output

    @abstractmethod
    def should_handle(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> bool:
        """Return True when this hook should process the reply."""

    async def parse_output(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Parse business output before metadata or persistence."""

        del agent, kwargs
        return None

    async def apply_metadata(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Apply metadata or mutate the output after parsing."""

        del agent, kwargs
        return output

    async def persist(
        self,
        *,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> None:
        """Persist business side effects after metadata is ready."""

        del agent, kwargs, output


class BusinessPostReplyHookManager:
    """Run business post-reply handlers sequentially."""

    def __init__(
        self,
        handlers: list[PostReplyBusinessHandler] | None = None,
    ) -> None:
        self._handlers = list(handlers or [])

    async def __call__(
        self,
        agent: Any,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg:
        """Execute all handlers and return the latest output."""

        current_output = output
        for handler in self._handlers:
            try:
                updated_output = await handler.handle(
                    agent,
                    kwargs,
                    current_output,
                )
                if isinstance(updated_output, Msg):
                    current_output = updated_output
            except Exception:
                logger.warning(
                    "Business post-reply handler failed: %s",
                    handler.__class__.__name__,
                    exc_info=True,
                )
        return current_output
