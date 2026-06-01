"""Tests for automatic marketing structured-result persistence."""

from __future__ import annotations

from pathlib import Path

from agentscope.message import Msg

from backend.database.connection import BackendDatabase
from backend.scenes.marketing.persistence import (
    MarketingStructuredResultPersistence,
)


def test_marketing_structured_result_persistence_saves_message(
    tmp_path: Path,
) -> None:
    """structured_result 应被拆成营销成果主表与附件表。"""

    database = BackendDatabase(tmp_path / "marketing-persist.sqlite3")
    persistence = MarketingStructuredResultPersistence(database=database)
    msg = Msg(name="Assistant", role="assistant", content="结构化摘要")
    msg.metadata = {
        "business_result": {
            "title": "方案标题",
            "basic_info": {"title": "方案标题"},
            "product_info": {"scene": "招投标"},
            "display_content": [
                {
                    "type": "pdf",
                    "file_name": "方案.pdf",
                    "fileUrl": "https://example.com/files/plan.pdf",
                    "previewUrl": "https://example.com/preview/plan",
                    "downloadUrl": "https://example.com/download/plan",
                    "filePath": "reports/plan.pdf",
                    "fileId": "file-1",
                },
            ],
        },
        "structured_result": {
            "title": "方案标题",
            "result": {
                "type": "product",
                "payload": {
                    "title": "方案标题",
                    "summary": "结构化摘要",
                    "attachments": [
                        {
                            "filePath": "reports/plan.pdf",
                            "fileName": "方案.pdf",
                        },
                    ],
                },
            },
        },
    }

    persistence.persist_message(
        msg,
        session_id="session-1",
        agent_id="market_agent",
    )

    with database.transaction() as connection:
        result_row = connection.execute(
            "SELECT title, result_type, scene, summary, session_id, agent_id "
            "FROM marketing_product_results",
        ).fetchone()
        file_row = connection.execute(
            "SELECT file_name, file_type, file_url, preview_url, "
            "download_url, file_path, file_id "
            "FROM marketing_result_files",
        ).fetchone()
        opportunity_row = connection.execute(
            "SELECT title, region, source, contact, budget, original_link, level "
            "FROM marketing_opportunities",
        ).fetchone()

    assert result_row is not None
    assert result_row["title"] == "方案标题"
    assert result_row["result_type"] == "product"
    assert result_row["scene"] == "招投标"
    assert result_row["summary"] == "结构化摘要"
    assert result_row["session_id"] == "session-1"
    assert result_row["agent_id"] == "market_agent"

    assert file_row is not None
    assert file_row["file_name"] == "方案.pdf"
    assert file_row["file_type"] == "pdf"
    assert file_row["file_url"] == "https://example.com/files/plan.pdf"
    assert file_row["preview_url"] == "https://example.com/preview/plan"
    assert file_row["download_url"] == "https://example.com/download/plan"
    assert file_row["file_path"] == "reports/plan.pdf"
    assert file_row["file_id"] == "file-1"
    assert opportunity_row is None


def test_marketing_structured_result_persistence_saves_opportunities(
    tmp_path: Path,
) -> None:
    """business_result 中的商机列表应被拆成独立商机记录。"""

    database = BackendDatabase(tmp_path / "marketing-opportunity-persist.sqlite3")
    persistence = MarketingStructuredResultPersistence(database=database)
    msg = Msg(name="Assistant", role="assistant", content="商机摘要")
    msg.metadata = {
        "business_result": {
            "title": "商机识别结果",
            "opportunities": [
                {
                    "title": "某市教育局 AI 采购项目",
                    "region": "济南",
                    "source": "政府采购网",
                    "publishTime": "2026-05-01",
                    "deadline": "2026-05-20",
                    "credibility": 0.95,
                    "contact": "李老师",
                    "budget": 86.5,
                    "purchaseAmount": 80,
                    "linkStatus": "有效",
                    "reason": "采购意向明确",
                    "originalLink": "https://example.com/bid/2",
                    "level": "A",
                    "summary": "建议重点跟进",
                },
            ],
        },
        "structured_result": {
            "title": "商机识别结果",
            "result": {
                "type": "business",
                "payload": {
                    "title": "商机识别结果",
                    "summary": "识别到 1 条高价值商机",
                    "opportunities": [
                        {
                            "title": "某市教育局 AI 采购项目",
                            "region": "济南",
                        },
                    ],
                },
            },
        },
    }

    persistence.persist_message(
        msg,
        session_id="session-2",
        agent_id="market_agent",
    )

    with database.transaction() as connection:
        opportunity_row = connection.execute(
            "SELECT title, region, source, contact, budget, purchase_amount, "
            "link_status, reason, original_link, level, summary, session_id, agent_id "
            "FROM marketing_opportunities",
        ).fetchone()

    assert opportunity_row is not None
    assert opportunity_row["title"] == "某市教育局 AI 采购项目"
    assert opportunity_row["region"] == "济南"
    assert opportunity_row["source"] == "政府采购网"
    assert opportunity_row["contact"] == "李老师"
    assert opportunity_row["budget"] == 86.5
    assert opportunity_row["purchase_amount"] == 80
    assert opportunity_row["link_status"] == "有效"
    assert opportunity_row["reason"] == "采购意向明确"
    assert opportunity_row["original_link"] == "https://example.com/bid/2"
    assert opportunity_row["level"] == "A"
    assert opportunity_row["summary"] == "建议重点跟进"
    assert opportunity_row["session_id"] == "session-2"
    assert opportunity_row["agent_id"] == "market_agent"
