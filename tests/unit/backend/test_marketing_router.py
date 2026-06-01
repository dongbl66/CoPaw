"""Tests for the marketing backend router."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.database.connection import BackendDatabase
from backend.scenes.marketing.dependencies import build_marketing_result_service
from backend.scenes.marketing.router import create_router
from backend.scenes.marketing.service import MarketingResultService


@pytest.fixture
def marketing_result_service(tmp_path: Path) -> MarketingResultService:
    """Create an isolated marketing result service for route tests."""

    database = BackendDatabase(tmp_path / "marketing-router.sqlite3")
    return MarketingResultService(database)


@pytest.fixture
def api_client(marketing_result_service: MarketingResultService) -> AsyncClient:
    """Create a test client with the marketing router mounted."""

    app = FastAPI()
    app.include_router(create_router())
    app.dependency_overrides[build_marketing_result_service] = (
        lambda: marketing_result_service
    )
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_get_latest_result_returns_null_when_session_has_no_result(
    api_client: AsyncClient,
) -> None:
    """Should return an empty latest item for sessions without saved results."""

    async with api_client:
        response = await api_client.get(
            "/api/backend/marketing/results/latest",
            params={"session_id": "missing-session"},
        )

    assert response.status_code == 200
    assert response.json() == {"item": None}


async def test_get_latest_result_returns_latest_saved_result(
    api_client: AsyncClient,
    marketing_result_service: MarketingResultService,
) -> None:
    """Should return the newest result under the requested session."""

    marketing_result_service.create_result(
        title="第一次结果",
        result_type="text",
        summary="first",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-1",
        agent_id="market_agent",
    )
    latest = marketing_result_service.create_result(
        title="最新结果",
        result_type="pdf",
        summary="latest",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-1",
        agent_id="market_agent",
    )

    async with api_client:
        response = await api_client.get(
            "/api/backend/marketing/results/latest",
            params={"session_id": "session-1"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["item"]["id"] == latest.id
    assert payload["item"]["title"] == "最新结果"


async def test_save_result_marks_item_as_saved(
    api_client: AsyncClient,
    marketing_result_service: MarketingResultService,
) -> None:
    """Should mark one result as saved through the save endpoint."""

    created = marketing_result_service.create_result(
        title="待保存成果",
        result_type="text",
        summary="draft",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-save",
        agent_id="market_agent",
    )

    async with api_client:
        response = await api_client.post(
            f"/api/backend/marketing/results/{created.id}/save",
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created.id
    assert payload["save_status"] == "saved"


async def test_list_results_supports_saved_only_filter(
    api_client: AsyncClient,
    marketing_result_service: MarketingResultService,
) -> None:
    """Should return only manually saved results when saved_only is enabled."""

    draft = marketing_result_service.create_result(
        title="草稿成果",
        result_type="text",
        summary="draft",
        info={"structuredResult": {"eventType": "structured_result"}},
        session_id="session-1",
        agent_id="market_agent",
    )
    saved = marketing_result_service.create_result(
        title="正式成果",
        result_type="text",
        summary="saved",
        info={"structuredResult": {"eventType": "structured_result"}},
        save_status="saved",
        session_id="session-1",
        agent_id="market_agent",
    )

    assert draft.save_status == "draft"
    assert saved.save_status == "saved"

    async with api_client:
        response = await api_client.get(
            "/api/backend/marketing/results",
            params={"saved_only": "true"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == saved.id
