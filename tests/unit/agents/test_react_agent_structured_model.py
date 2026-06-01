# -*- coding: utf-8 -*-
"""Tests for QwenPawAgent structured output model selection."""

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from pydantic import BaseModel

from backend.scenes.marketing.parsers.business_result import (
    inject_business_result_metadata,
)
from qwenpaw.agents.react_agent import QwenPawAgent


class DefaultStructuredModel(BaseModel):
    """Default structured output schema used by the agent instance."""

    value: str


class OverrideStructuredModel(BaseModel):
    """Per-call structured output schema that overrides the default."""

    other: str


def _build_business_result_text() -> str:
    """Return a normalized business result payload encoded as JSON text."""

    return """
```json
{
  "output": "结构化摘要",
  "meta": {
    "business_result": {
      "title": "方案标题",
      "name": "demo",
      "basic_info": "{\\"creator_name\\": \\"assistant\\"}",
      "product_info": "{\\"industry\\": \\"retail\\"}",
      "display_content": []
    }
  }
}
```
""".strip()


def _build_agent(tmp_path: Path) -> QwenPawAgent:
    """Create a minimal agent instance for reply() behavior tests."""

    agent = QwenPawAgent.__new__(QwenPawAgent)
    agent._instance_pre_reply_hooks = {}
    agent._instance_post_reply_hooks = {}
    agent.__class__._class_pre_reply_hooks = {}
    agent.__class__._class_post_reply_hooks = {}
    agent._workspace_dir = tmp_path
    agent._request_context = {}
    agent._agent_config = SimpleNamespace(
        id="default",
        running=SimpleNamespace(
            light_context_config=SimpleNamespace(
                tool_result_pruning_config=SimpleNamespace(
                    pruning_recent_msg_max_bytes=1024,
                ),
            ),
            shell_command_timeout=None,
            shell_command_executable=None,
        ),
    )
    agent.command_handler = SimpleNamespace(is_command=lambda _query: False)
    agent.max_iters = 3
    agent._default_structured_model = DefaultStructuredModel
    agent._final_output_parser = None
    return agent


@pytest.mark.asyncio
async def test_reply_uses_default_structured_model_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """reply() falls back to the instance default structured model."""

    agent = _build_agent(tmp_path)
    captured: dict[str, type[BaseModel] | None] = {}

    async def fake_process(_msg: Msg) -> None:
        return None

    async def fake_reply(self, msg=None, structured_model=None):
        captured["structured_model"] = structured_model
        return Msg(name="Assistant", role="assistant", content="ok")

    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.process_file_and_media_blocks_in_message",
        fake_process,
    )
    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.apply_skill_config_env_overrides",
        lambda _workspace_dir, _channel_name: nullcontext(),
    )
    monkeypatch.setattr(ReActAgent, "reply", fake_reply)

    await QwenPawAgent.reply(
        agent,
        msg=Msg(name="User", role="user", content="hello"),
    )

    assert captured["structured_model"] is DefaultStructuredModel


@pytest.mark.asyncio
async def test_reply_prefers_explicit_structured_model_over_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """reply() uses the per-call structured model when it is provided."""

    agent = _build_agent(tmp_path)
    captured: dict[str, type[BaseModel] | None] = {}

    async def fake_process(_msg: Msg) -> None:
        return None

    async def fake_reply(self, msg=None, structured_model=None):
        captured["structured_model"] = structured_model
        return Msg(name="Assistant", role="assistant", content="ok")

    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.process_file_and_media_blocks_in_message",
        fake_process,
    )
    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.apply_skill_config_env_overrides",
        lambda _workspace_dir, _channel_name: nullcontext(),
    )
    monkeypatch.setattr(ReActAgent, "reply", fake_reply)

    await QwenPawAgent.reply(
        agent,
        msg=Msg(name="User", role="user", content="hello"),
        structured_model=OverrideStructuredModel,
    )

    assert captured["structured_model"] is OverrideStructuredModel


@pytest.mark.asyncio
async def test_reply_injects_business_result_metadata_from_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """reply() parses final business JSON output into message metadata."""

    agent = _build_agent(tmp_path)
    agent._final_output_parser = inject_business_result_metadata

    async def fake_process(_msg: Msg) -> None:
        return None

    async def fake_reply(self, msg=None, structured_model=None):
        return Msg(
            name="Assistant",
            role="assistant",
            content=_build_business_result_text(),
        )

    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.process_file_and_media_blocks_in_message",
        fake_process,
    )
    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.apply_skill_config_env_overrides",
        lambda _workspace_dir, _channel_name: nullcontext(),
    )
    monkeypatch.setattr(ReActAgent, "reply", fake_reply)

    result = await QwenPawAgent.reply(
        agent,
        msg=Msg(name="User", role="user", content="hello"),
    )

    assert result.content == "结构化摘要"
    assert result.metadata["business_result_source"] == "agent_output"
    assert result.metadata["business_result"]["basic_info"] == {
        "creator_name": "assistant",
    }
    assert result.metadata["business_result"]["product_info"] == {
        "industry": "retail",
    }
    assert result.metadata["structured_result"]["eventType"] == "structured_result"
    assert result.metadata["structured_result"]["result"]["type"] == "product"
    assert (
        result.metadata["structured_result"]["result"]["payload"]["summary"]
        == "结构化摘要"
    )


@pytest.mark.asyncio
async def test_reply_persists_structured_result_for_market_agent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """market_agent 在产生 structured_result 后应触发自动持久化。"""

    agent = _build_agent(tmp_path)
    agent._agent_config.id = "market_agent"
    agent._request_context = {
        "session_id": "session-1",
        "agent_id": "market_agent",
    }
    agent._final_output_parser = inject_business_result_metadata
    captured: dict[str, object] = {}

    async def fake_process(_msg: Msg) -> None:
        return None

    async def fake_reply(self, msg=None, structured_model=None):
        return Msg(
            name="Assistant",
            role="assistant",
            content=_build_business_result_text(),
        )

    class FakePersistence:
        def persist_message(
            self,
            msg: Msg,
            *,
            session_id: str | None,
            agent_id: str | None,
        ) -> None:
            captured["title"] = msg.metadata["structured_result"]["title"]
            captured["session_id"] = session_id
            captured["agent_id"] = agent_id

    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.process_file_and_media_blocks_in_message",
        fake_process,
    )
    monkeypatch.setattr(
        "qwenpaw.agents.react_agent.apply_skill_config_env_overrides",
        lambda _workspace_dir, _channel_name: nullcontext(),
    )
    monkeypatch.setattr(ReActAgent, "reply", fake_reply)
    monkeypatch.setattr(
        "backend.scenes.marketing.persistence."
        "MarketingStructuredResultPersistence",
        FakePersistence,
    )

    await QwenPawAgent.reply(
        agent,
        msg=Msg(name="User", role="user", content="hello"),
    )

    assert captured["title"] == "方案标题"
    assert captured["session_id"] == "session-1"
    assert captured["agent_id"] == "market_agent"
