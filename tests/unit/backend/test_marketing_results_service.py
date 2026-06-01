"""Tests for marketing result persistence service."""

from __future__ import annotations

from pathlib import Path

from backend.database.connection import BackendDatabase
from backend.scenes.marketing.service import MarketingResultService


def test_marketing_result_service_crud_roundtrip(tmp_path: Path) -> None:
    """营销成果服务应支持主对象与附件的增删改查。"""

    database = BackendDatabase(tmp_path / "marketing-results.sqlite3")
    service = MarketingResultService(database)

    created = service.create_result(
        title="产品方案",
        result_type="ppt",
        scene="招投标",
        summary="分析摘要",
        detail_content=[{"type": "text", "value": "分析摘要"}],
        info={"structuredResult": {"eventType": "structured_result"}},
        basic_info={"title": "产品方案"},
        product_info={"scene": "招投标"},
        attachments=[
            {
                "file_name": "方案.pdf",
                "file_type": "pdf",
                "file_url": "https://example.com/files/plan.pdf",
                "preview_url": "https://example.com/preview/plan",
                "download_url": "https://example.com/download/plan",
                "file_path": "reports/plan.pdf",
                "file_id": "file-1",
                "source_type": "generated",
            },
        ],
        session_id="session-1",
        agent_id="market_agent",
    )

    assert created.id > 0
    assert created.result_type == "ppt"
    assert created.scene == "招投标"
    assert created.summary == "分析摘要"
    assert created.attachments[0].file_name == "方案.pdf"
    assert created.attachments[0].file_type == "pdf"

    loaded = service.get_result(created.id)
    assert loaded.id == created.id
    assert loaded.session_id == "session-1"
    assert loaded.attachments[0].file_url == "https://example.com/files/plan.pdf"

    updated = service.update_result(
        created.id,
        title="更新后的产品方案",
        summary="更新后的摘要",
        attachments=[
            {
                "file_name": "方案.html",
                "file_type": "html",
                "file_url": "https://example.com/files/plan.html",
                "preview_url": "https://example.com/preview/plan-html",
                "download_url": "https://example.com/download/plan-html",
                "file_path": "reports/plan.html",
                "file_id": "file-2",
                "source_type": "generated",
            },
        ],
    )
    assert updated.title == "更新后的产品方案"
    assert updated.summary == "更新后的摘要"
    assert updated.attachments[0].file_name == "方案.html"

    items = service.list_results()
    assert len(items) == 1
    assert items[0].id == created.id
    assert items[0].attachments[0].file_name == "方案.html"

    deleted = service.delete_result(created.id)
    assert deleted is True
    assert service.list_results() == []


def test_marketing_result_service_returns_latest_result_by_session(
    tmp_path: Path,
) -> None:
    """营销成果服务应按会话返回最新一条结果。"""

    database = BackendDatabase(tmp_path / "marketing-results-latest.sqlite3")
    service = MarketingResultService(database)

    service.create_result(
        title="旧结果",
        result_type="text",
        summary="first",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-a",
        agent_id="market_agent",
    )
    latest = service.create_result(
        title="新结果",
        result_type="pdf",
        summary="second",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-a",
        agent_id="market_agent",
    )
    service.create_result(
        title="其他会话结果",
        result_type="text",
        summary="other",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-b",
        agent_id="market_agent",
    )

    loaded = service.get_latest_result_by_session("session-a")

    assert loaded.id == latest.id
    assert loaded.title == "新结果"
    assert loaded.result_type == "pdf"


def test_marketing_result_service_supports_manual_save_status(
    tmp_path: Path,
) -> None:
    """营销成果服务应支持手动确认保存，并仅返回已保存结果。"""

    database = BackendDatabase(tmp_path / "marketing-results-saved.sqlite3")
    service = MarketingResultService(database)

    created = service.create_result(
        title="待保存方案",
        result_type="text",
        summary="draft",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-save",
        agent_id="market_agent",
    )

    assert created.save_status == "draft"
    assert service.list_saved_results() == []

    saved = service.mark_result_as_saved(created.id)

    assert saved.save_status == "saved"
    saved_items = service.list_saved_results()
    assert len(saved_items) == 1
    assert saved_items[0].id == created.id
