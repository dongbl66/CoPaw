# -*- coding: utf-8 -*-
"""Tests for agent output binding resolution."""

from __future__ import annotations

import pytest
from agentscope.message import Msg
from pydantic import BaseModel

from qwenpaw.config.config import AgentProfileConfig


class DemoStructuredModel(BaseModel):
    """Structured output schema used for binding resolution tests."""

    title: str


def demo_output_parser(msg: Msg) -> None:
    """Mutate the reply to prove the parser import path resolved."""

    msg.metadata["parsed"] = True


def demo_not_a_model() -> None:
    """Non-BaseModel symbol used to validate binding errors."""


def test_resolve_agent_output_binding_loads_import_paths() -> None:
    """Resolve both structured model and parser from import-path config."""

    from qwenpaw.agents.output_binding import resolve_agent_output_binding
    from qwenpaw.config.config import AgentOutputBindingConfig

    agent_config = AgentProfileConfig(
        id="business-agent",
        name="Business Agent",
        output_binding=AgentOutputBindingConfig(
            structured_model_import_path=(
                "tests.unit.agents.test_output_binding:"
                "DemoStructuredModel"
            ),
            final_output_parser_import_path=(
                "tests.unit.agents.test_output_binding:"
                "demo_output_parser"
            ),
        ),
    )

    binding = resolve_agent_output_binding(agent_config)

    assert binding.structured_model is DemoStructuredModel
    assert binding.final_output_parser is demo_output_parser


def test_resolve_agent_output_binding_loads_marketing_parser() -> None:
    """Built-in marketing parser should resolve from the scene path."""

    from qwenpaw.agents.output_binding import resolve_agent_output_binding
    from qwenpaw.config.config import AgentOutputBindingConfig

    agent_config = AgentProfileConfig(
        id="marketing-agent",
        name="Marketing Agent",
        output_binding=AgentOutputBindingConfig(
            final_output_parser_import_path=(
                "backend.scenes.marketing.parsers.business_result:"
                "inject_business_result_metadata"
            ),
        ),
    )

    binding = resolve_agent_output_binding(agent_config)

    assert callable(binding.final_output_parser)
    assert (
        binding.final_output_parser.__name__
        == "inject_business_result_metadata"
    )


def test_resolve_agent_output_binding_returns_empty_when_unconfigured() -> None:
    """Unconfigured agents should not get default output bindings."""

    from qwenpaw.agents.output_binding import resolve_agent_output_binding

    binding = resolve_agent_output_binding(
        AgentProfileConfig(id="default", name="Default Agent"),
    )

    assert binding.structured_model is None
    assert binding.final_output_parser is None


def test_resolve_agent_output_binding_uses_market_agent_default_parser() -> None:
    """market_agent 在未显式配置时应自动绑定营销结果解析器。"""

    from qwenpaw.agents.output_binding import resolve_agent_output_binding

    binding = resolve_agent_output_binding(
        AgentProfileConfig(id="market_agent", name="Market Agent"),
    )

    assert callable(binding.final_output_parser)
    assert (
        binding.final_output_parser.__name__
        == "inject_business_result_metadata"
    )


def test_resolve_agent_output_binding_uses_fraud_transcript_default_parser() -> None:
    """fraud_transcript_agent 未显式配置时也应自动绑定电诈笔录解析器。"""

    from qwenpaw.agents.output_binding import resolve_agent_output_binding

    binding = resolve_agent_output_binding(
        AgentProfileConfig(
            id="fraud_transcript_agent",
            name="电诈笔录智能辅助",
        ),
    )

    assert callable(binding.final_output_parser)
    assert (
        binding.final_output_parser.__name__
        == "inject_fraud_transcript_metadata"
    )


def test_resolve_agent_output_binding_rejects_non_basemodel_symbol() -> None:
    """Structured model import paths must point to BaseModel subclasses."""

    from qwenpaw.agents.output_binding import resolve_agent_output_binding
    from qwenpaw.config.config import AgentOutputBindingConfig

    agent_config = AgentProfileConfig(
        id="business-agent",
        name="Business Agent",
        output_binding=AgentOutputBindingConfig(
            structured_model_import_path=(
                "tests.unit.agents.test_output_binding:demo_not_a_model"
            ),
        ),
    )

    with pytest.raises(TypeError):
        resolve_agent_output_binding(agent_config)
