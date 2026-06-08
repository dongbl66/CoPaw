from __future__ import annotations

from types import SimpleNamespace

import pytest
from agentscope.model import ChatModelBase

from qwenpaw.providers.model_capability_cache import get_capability_cache
from qwenpaw.providers.retry_chat_model import RetryChatModel


class _ToolChoiceRejectedError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.status_code = 400


class _FakeChatModel(ChatModelBase):
    def __init__(self) -> None:
        super().__init__(model_name="deepseek-v4-pro", stream=False)
        self._provider_id = "deepseek"
        self.calls: list[dict] = []
        self.reject_tool_choice_once = False

    async def __call__(self, *args, **kwargs):
        _ = args
        self.calls.append(
            {
                "messages": kwargs.get("messages"),
                "tools": kwargs.get("tools"),
                "tool_choice": kwargs.get("tool_choice"),
            },
        )
        if self.reject_tool_choice_once and kwargs.get("tool_choice") is not None:
            self.reject_tool_choice_once = False
            raise _ToolChoiceRejectedError(
                "Thinking mode does not support this tool_choice",
            )
        return SimpleNamespace(usage=None, content="ok")


@pytest.mark.asyncio
async def test_retry_chat_model_retries_without_tool_choice():
    cache = get_capability_cache()
    key = "deepseek:deepseek-v4-pro"
    cache.clear(key)

    inner = _FakeChatModel()
    inner.reject_tool_choice_once = True
    wrapper = RetryChatModel(inner)

    result = await wrapper(
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"type": "function", "function": {"name": "demo"}}],
        tool_choice="required",
    )

    assert result.content == "ok"
    assert [call["tool_choice"] for call in inner.calls] == ["required", None]
    assert inner.calls[1]["tools"] == [
        {"type": "function", "function": {"name": "demo"}},
    ]
    assert cache.get(key, "rejects_tool_choice", False) is True


@pytest.mark.asyncio
async def test_retry_chat_model_omits_tools_when_emulating_tool_choice_none():
    cache = get_capability_cache()
    key = "deepseek:deepseek-v4-pro"
    cache.clear(key)
    cache.learn(key, "rejects_tool_choice", True)

    inner = _FakeChatModel()
    wrapper = RetryChatModel(inner)

    await wrapper(
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"type": "function", "function": {"name": "demo"}}],
        tool_choice="none",
    )

    assert len(inner.calls) == 1
    assert inner.calls[0]["tool_choice"] is None
    assert inner.calls[0]["tools"] is None
