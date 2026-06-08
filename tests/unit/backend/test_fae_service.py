"""Tests for FAE opportunity and result persistence services."""

from __future__ import annotations

from pathlib import Path

from backend.database.connection import BackendDatabase
from backend.scenes.fae.service import FAEOpportunityService, FAEResultService


def test_fae_opportunity_service_initializes_table_and_crud_roundtrip(
    tmp_path: Path,
) -> None:
    """FAE opportunity service should work on a fresh backend database."""

    database = BackendDatabase(tmp_path / "fae.sqlite3")
    service = FAEOpportunityService(database)

    assert service.list_opportunities() == []

    created = service.create_opportunity(
        {
            "project_name": "Smart government cloud",
            "customer_name": "City data bureau",
            "city": "Guangzhou",
            "industry": "Government",
            "support_type": "Technical support",
            "requirement_desc": "Build a unified government cloud platform.",
            "opportunity_rating": "high",
            "opportunity_score": 91,
            "budget": {
                "min_yuan": 1000000,
                "max_yuan": 2000000,
                "note": "Initial estimate",
            },
            "display_content": [{"type": "text", "content": "Opportunity"}],
            "session_id": "session-fae",
        },
    )

    assert created["id"] > 0
    assert created["project_name"] == "Smart government cloud"
    assert created["budget_min_yuan"] == 1000000
    assert created["display_content"] == [{"type": "text", "content": "Opportunity"}]

    loaded = service.get_opportunity(created["id"])
    assert loaded["id"] == created["id"]

    updated = service.update_opportunity(
        created["id"],
        {
            "support_type": "Solution support",
            "display_content": [{"type": "text", "content": "Updated"}],
        },
    )
    assert updated["support_type"] == "Solution support"
    assert updated["display_content"] == [{"type": "text", "content": "Updated"}]

    assert len(service.list_opportunities(session_id="session-fae")) == 1

    service.delete_opportunity(created["id"])
    assert service.list_opportunities() == []


def test_fae_result_service_initializes_table_and_latest_roundtrip(
    tmp_path: Path,
) -> None:
    """FAE result service should work on a fresh backend database."""

    database = BackendDatabase(tmp_path / "fae-results.sqlite3")
    service = FAEResultService(database)

    assert service.list_results() == []

    created = service.create_result(
        title="FAE opportunity report",
        result_type="government_opportunity",
        scene="government",
        summary="A generated report.",
        detail_content=[{"type": "section", "title": "Summary"}],
        info={"opportunityId": 1},
        basic_info={"project_name": "Smart government cloud"},
        session_id="session-fae",
        agent_id="RA-agent",
    )

    assert created["id"] > 0
    assert created["save_status"] == "draft"
    assert created["info"]["opportunityId"] == 1

    latest = service.get_latest_result_by_session("session-fae")
    assert latest is not None
    assert latest["id"] == created["id"]

    saved = service.mark_result_as_saved(created["id"])
    assert saved["save_status"] == "saved"
    assert len(service.list_results(saved_only=True)) == 1
