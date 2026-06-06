# -*- coding: utf-8 -*-
"""Resolve agent output bindings from import-path based configuration."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from agentscope.message import Msg
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..config.config import AgentProfileConfig

logger = logging.getLogger("qwenpaw.agents.output_binding")

MARKET_AGENT_ID = "market_agent"
DEFAULT_MARKETING_PARSER_AGENT_IDS = frozenset({"market_agent", "RA-agent"})
MARKETING_FINAL_OUTPUT_PARSER_IMPORT_PATH = (
    "backend.scenes.marketing.parsers.business_result:"
    "inject_business_result_metadata"
)


@dataclass(frozen=True)
class AgentOutputBinding:
    """Resolved output binding objects for one agent instance."""

    structured_model: type[BaseModel] | None = None
    final_output_parser: Callable[[Msg], None] | None = None


def _import_from_path(import_path: str) -> Any:
    """Import and return the symbol referenced by an import path."""

    module_path: str
    attr_name: str
    if ":" in import_path:
        module_path, attr_name = import_path.split(":", 1)
    else:
        module_path, attr_name = import_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def resolve_agent_output_binding(
    agent_config: "AgentProfileConfig",
) -> AgentOutputBinding:
    """Resolve import-path configured output bindings for one agent."""

    agent_id = getattr(agent_config, "id", None)
    binding_config = getattr(agent_config, "output_binding", None)
    if binding_config is None:
        if agent_id not in DEFAULT_MARKETING_PARSER_AGENT_IDS:
            logger.info(
                "[output_binding] agent_id=%s → no default marketing parser, "
                "binding=empty",
                agent_id,
            )
            return AgentOutputBinding()
        logger.info(
            "[output_binding] agent_id=%s → using default marketing parser",
            agent_id,
        )
        structured_model = None
        final_output_parser = _import_from_path(
            MARKETING_FINAL_OUTPUT_PARSER_IMPORT_PATH,
        )
        return AgentOutputBinding(
            structured_model=structured_model,
            final_output_parser=final_output_parser,
        )

    logger.info(
        "[output_binding] agent_id=%s → explicit output_binding config used",
        agent_id,
    )
    structured_model = None
    if binding_config.structured_model_import_path:
        structured_model = _import_from_path(
            binding_config.structured_model_import_path,
        )
        if not (
            isinstance(structured_model, type)
            and issubclass(structured_model, BaseModel)
        ):
            raise TypeError(
                "structured_model_import_path must resolve to a "
                "BaseModel subclass",
            )

    final_output_parser = None
    if binding_config.final_output_parser_import_path:
        final_output_parser = _import_from_path(
            binding_config.final_output_parser_import_path,
        )
        if not callable(final_output_parser):
            raise TypeError(
                "final_output_parser_import_path must resolve to a callable",
            )

    return AgentOutputBinding(
        structured_model=structured_model,
        final_output_parser=final_output_parser,
    )
