"""Tests for marketing opportunity persistence service."""

from __future__ import annotations

from pathlib import Path

from backend.database.connection import BackendDatabase
from backend.scenes.marketing.service import MarketingOpportunityService


def test_marketing_opportunity_service_crud_roundtrip(tmp_path: Path) -> None:
    """营销商机服务应支持基础增删改查。"""

    database = BackendDatabase(tmp_path / "marketing-opportunities.sqlite3")
    service = MarketingOpportunityService(database)

    created = service.create_opportunity(
        title="某市算力中心采购项目",
        opportunity_type="招标公告",
        region="山东",
        source="政府采购网",
        publish_time="2026-05-01",
        deadline="2026-05-20",
        credibility=0.92,
        contact="张老师",
        budget=120.5,
        purchase_amount=100.0,
        link_status="有效",
        reason="预算明确，客户画像匹配",
        original_link="https://example.com/bid/1",
        level="A",
        summary="重点跟进商机",
        session_id="session-1",
        agent_id="market_agent",
    )

    assert created.id > 0
    assert created.title == "某市算力中心采购项目"
    assert created.region == "山东"
    assert created.budget == 120.5

    loaded = service.get_opportunity(created.id)
    assert loaded.id == created.id
    assert loaded.original_link == "https://example.com/bid/1"

    updated = service.update_opportunity(
        created.id,
        level="S",
        summary="高优先级推进",
    )
    assert updated.level == "S"
    assert updated.summary == "高优先级推进"

    items = service.list_opportunities()
    assert len(items) == 1
    assert items[0].id == created.id

    deleted = service.delete_opportunity(created.id)
    assert deleted is True
    assert service.list_opportunities() == []
