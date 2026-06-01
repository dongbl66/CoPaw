# -*- coding: utf-8 -*-
"""Tests for business post-reply hook orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from agentscope.message import Msg

from backend.scenes.marketing.hooks import MarketingPostReplyHook
from backend.scenes.marketing.parsers.business_result import (
    inject_business_result_metadata,
)
from qwenpaw.agents.hooks.post_reply_business import (
    BaseBusinessPostReplyHook,
    BusinessPostReplyHookManager,
)


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


@pytest.mark.asyncio
@pytest.mark.parametrize("agent_id", ["market_agent", "RA-agent"])
async def test_business_post_reply_hook_manager_parses_then_persists(
    monkeypatch: pytest.MonkeyPatch,
    agent_id: str,
) -> None:
    """marketing 业务 hook 应按模板流程先解析结果，再触发持久化。"""

    captured: dict[str, str] = {}

    class FakePersistence:
        """Fake persistence implementation used to capture writes."""

        def persist_message(
            self,
            msg: Msg,
            *,
            session_id: str | None,
            agent_id: str | None,
        ) -> None:
            captured["title"] = msg.metadata["structured_result"]["title"]
            captured["session_id"] = session_id or ""
            captured["agent_id"] = agent_id or ""

    monkeypatch.setattr(
        "backend.scenes.marketing.persistence."
        "MarketingStructuredResultPersistence",
        FakePersistence,
    )

    hook_manager = BusinessPostReplyHookManager(
        handlers=[
            MarketingPostReplyHook(),
        ],
    )
    agent = SimpleNamespace(
        _final_output_parser=inject_business_result_metadata,
        _request_context={
            "session_id": "session-1",
            "agent_id": agent_id,
        },
        _agent_config=SimpleNamespace(id=agent_id),
    )
    output = Msg(
        name="Assistant",
        role="assistant",
        content=_build_business_result_text(),
    )

    result = await hook_manager(agent, {"msg": None}, output)

    assert result is output
    assert output.metadata["structured_result"]["title"] == "方案标题"
    assert captured["title"] == "方案标题"
    assert captured["session_id"] == "session-1"
    assert captured["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_base_business_post_reply_hook_template_method() -> None:
    """抽象基类应按 should -> parse -> apply -> persist 顺序执行。"""

    executed: list[str] = []

    class DemoHook(BaseBusinessPostReplyHook):
        def should_handle(self, *, agent, kwargs, output) -> bool:
            del agent, kwargs, output
            executed.append("should")
            return True

        async def parse_output(self, *, agent, kwargs, output) -> Msg | None:
            del agent, kwargs
            executed.append("parse")
            output.metadata = {"phase": "parsed"}
            return output

        async def apply_metadata(self, *, agent, kwargs, output) -> Msg | None:
            del agent, kwargs
            executed.append("apply")
            output.metadata["phase"] = "applied"
            return output

        async def persist(self, *, agent, kwargs, output) -> None:
            del agent, kwargs, output
            executed.append("persist")

    output = Msg(name="Assistant", role="assistant", content="demo")
    result = await DemoHook().handle(
        agent=SimpleNamespace(),
        kwargs={},
        output=output,
    )

    assert result is output
    assert output.metadata["phase"] == "applied"
    assert executed == ["should", "parse", "apply", "persist"]
