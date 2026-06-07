# -*- coding: utf-8 -*-
"""Tests for the unified business results router."""

from __future__ import annotations

from unittest.mock import Mock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.scenes.fae.dependencies import build_fae_result_service
from backend.scenes.fae.unified_router import create_router
from backend.scenes.fraud_transcript.dependencies import (
    build_fraud_transcript_result_service,
)
from backend.scenes.marketing.dependencies import build_marketing_result_service


async def test_latest_result_with_biz_module_queries_only_target_service() -> None:
    app = FastAPI()
    app.include_router(create_router())

    marketing_service = Mock()
    fae_service = Mock()
    fraud_service = Mock()
    fraud_service.get_latest_result_by_session.return_value = {
        "id": 7,
        "title": "Fraud transcript report",
        "result_type": "business",
        "save_status": "draft",
        "scene": "fraud_transcript_report",
        "summary": "summary",
        "basic_info": {},
        "product_info": {},
        "qa_records": [],
        "structured_result": {
            "eventType": "structured_result",
            "version": "1.0",
            "result": {
                "type": "business",
                "payload": {"scene": "fraud_transcript_report"},
            },
            "meta": {"bizModule": "fraud_transcript"},
        },
        "session_id": "session-1",
        "agent_id": "fraud_transcript_agent",
        "created_at": "2026-06-07T00:00:00",
        "updated_at": "2026-06-07T00:01:00",
    }

    app.dependency_overrides[build_marketing_result_service] = lambda: marketing_service
    app.dependency_overrides[build_fae_result_service] = lambda: fae_service
    app.dependency_overrides[build_fraud_transcript_result_service] = (
        lambda: fraud_service
    )

    client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )

    async with client:
        response = await client.get(
            "/api/backend/results/latest",
            params={
                "session_id": "session-1",
                "biz_module": "fraud_transcript",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["biz_module"] == "fraud_transcript"
    assert payload["item"]["id"] == 7
    fraud_service.get_latest_result_by_session.assert_called_once_with("session-1")
    marketing_service.get_latest_result_by_session.assert_not_called()
    fae_service.get_latest_result_by_session.assert_not_called()


async def test_latest_result_without_biz_module_returns_400() -> None:
    app = FastAPI()
    app.include_router(create_router())

    marketing_service = Mock()
    fae_service = Mock()
    fraud_service = Mock()
    marketing_service.get_latest_result_by_session.return_value = {
        "id": 99,
        "title": "Marketing",
        "updated_at": "2026-06-07T00:00:00",
    }
    fae_service.get_latest_result_by_session.return_value = None
    fraud_service.get_latest_result_by_session.return_value = {
        "id": 1,
        "title": "Fraud",
        "updated_at": "2026-06-07T00:02:00",
    }

    app.dependency_overrides[build_marketing_result_service] = lambda: marketing_service
    app.dependency_overrides[build_fae_result_service] = lambda: fae_service
    app.dependency_overrides[build_fraud_transcript_result_service] = (
        lambda: fraud_service
    )

    client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )

    async with client:
        response = await client.get(
            "/api/backend/results/latest",
            params={"session_id": "session-1"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "biz_module is required"
    marketing_service.get_latest_result_by_session.assert_not_called()
    fae_service.get_latest_result_by_session.assert_not_called()
    fraud_service.get_latest_result_by_session.assert_not_called()
