"""Tests for backend structured result parsing."""

from agentscope.message import Msg

from backend.scenes.marketing.parsers.business_result import (
    inject_business_result_metadata,
)
from tests.unit.agents.test_react_agent_structured_model import (
    _build_business_result_text,
)


def test_inject_business_result_metadata_adds_structured_text_result() -> None:
    """带商机列表的 business_result 应转换成 business 工作台结果。"""

    msg = Msg(
        name="Assistant",
        role="assistant",
        content=_build_business_result_text(),
    )

    inject_business_result_metadata(msg)

    assert msg.content == "结构化摘要"
    assert msg.metadata["business_result_source"] == "agent_output"
    structured_result = msg.metadata["structured_result"]
    assert structured_result["eventType"] == "structured_result"
    assert structured_result["result"]["type"] == "product"
    assert structured_result["result"]["payload"]["summary"] == "结构化摘要"
    assert structured_result["result"]["payload"]["title"] == "方案标题"
    assert structured_result["result"]["payload"]["attachments"] == []


def test_inject_business_result_metadata_builds_business_result_when_opportunities_present() -> None:
    """当 business_result 中存在商机列表时，应构造 business 工作台结果。"""

    msg = Msg(
        name="Assistant",
        role="assistant",
        content="""
```json
{
  "output": "识别到 1 条高价值商机",
  "meta": {
    "business_result": {
      "title": "商机识别结果",
      "basic_info": "{\\"scene\\": \\"教育\\"}",
      "product_info": "{\\"scene\\": \\"政府采购\\"}",
      "opportunities": [
        {
          "title": "某市教育局 AI 采购项目",
          "region": "济南",
          "budget": 86.5,
          "reason": "采购意向明确"
        }
      ],
      "display_content": [
        {
          "type": "pdf",
          "file_path": "/reports/opportunities.pdf",
          "file_name": "opportunities.pdf"
        }
      ]
    }
  }
}
```
""".strip(),
    )

    inject_business_result_metadata(msg)

    payload = msg.metadata["structured_result"]["result"]["payload"]
    assert msg.metadata["structured_result"]["result"]["type"] == "business"
    assert payload["summary"] == "识别到 1 条高价值商机"
    assert payload["opportunities"][0]["title"] == "某市教育局 AI 采购项目"
    assert payload["attachments"][0]["filePath"] == "/reports/opportunities.pdf"


def test_inject_business_result_metadata_builds_product_result_when_display_content_present() -> None:
    """当 display_content 中带预览文件时，应返回 product 工作台结果。"""

    msg = Msg(
        name="Assistant",
        role="assistant",
        content="""
```json
{
  "output": "请查看右侧 PDF",
  "meta": {
    "business_result": {
      "title": "营销方案",
      "basic_info": "{}",
      "product_info": "{}",
      "display_content": [
        {
          "type": "pdf",
          "file_path": "/reports/marketing-plan.pdf",
          "file_name": "marketing-plan.pdf"
        }
      ]
    }
  }
}
```
""".strip(),
    )

    inject_business_result_metadata(msg)

    payload = msg.metadata["structured_result"]["result"]["payload"]
    assert msg.metadata["structured_result"]["result"]["type"] == "product"
    assert payload["summary"] == "请查看右侧 PDF"
    assert payload["attachments"][0]["filePath"] == "/reports/marketing-plan.pdf"
    assert payload["attachments"][0]["fileName"] == "marketing-plan.pdf"
