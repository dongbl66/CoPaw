# -*- coding: utf-8 -*-
"""Tests for the fraud transcript backend router."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest

from backend.database.connection import BackendDatabase
from backend.scenes.fraud_transcript.router import create_router
from backend.scenes.fraud_transcript.service import FraudTranscriptResultService


@pytest.fixture
def fraud_transcript_result_service() -> Generator[FraudTranscriptResultService, None, None]:
    db_dir = Path.cwd() / ".pytest-tmp"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / f"fraud-transcript-router-{uuid4().hex}.sqlite3"
    database = BackendDatabase(db_path)
    yield FraudTranscriptResultService(database)
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass


def test_create_router_registers_fraud_transcript_routes() -> None:
    router = create_router()

    paths = {route.path for route in router.routes}

    assert "/api/backend/fraud-transcript/health" in paths
    assert "/api/backend/fraud-transcript/results" in paths
    assert "/api/backend/fraud-transcript/results/latest" in paths
    assert "/api/backend/fraud-transcript/results/{result_id}" in paths
    assert "/api/backend/fraud-transcript/results/{result_id}/save" in paths


def test_result_service_returns_latest_for_session(
    fraud_transcript_result_service: FraudTranscriptResultService,
) -> None:
    fraud_transcript_result_service.create_result(
        title="第一次报告",
        result_type="business",
        scene="fraud_transcript_report",
        summary="first",
        structured_result={"eventType": "structured_result"},
        session_id="session-1",
        agent_id="fraud_transcript_agent",
    )
    latest = fraud_transcript_result_service.create_result(
        title="最新报告",
        result_type="business",
        scene="fraud_transcript_report",
        summary="latest",
        structured_result={"eventType": "structured_result"},
        session_id="session-1",
        agent_id="fraud_transcript_agent",
    )

    result = fraud_transcript_result_service.get_latest_result_by_session("session-1")

    assert result is not None
    assert result.id == latest.id


def test_result_service_marks_item_saved(
    fraud_transcript_result_service: FraudTranscriptResultService,
) -> None:
    created = fraud_transcript_result_service.create_result(
        title="待保存报告",
        result_type="business",
        scene="fraud_transcript_report",
        summary="draft",
        structured_result={"eventType": "structured_result"},
        session_id="session-save",
        agent_id="fraud_transcript_agent",
    )

    result = fraud_transcript_result_service.mark_result_as_saved(created.id)

    assert result.save_status == "saved"


def test_result_service_lists_saved_results_only(
    fraud_transcript_result_service: FraudTranscriptResultService,
) -> None:
    fraud_transcript_result_service.create_result(
        title="草稿报告",
        result_type="business",
        scene="fraud_transcript_report",
        summary="draft",
        structured_result={"eventType": "structured_result"},
        session_id="session-1",
        agent_id="fraud_transcript_agent",
    )
    saved = fraud_transcript_result_service.create_result(
        title="正式报告",
        result_type="business",
        save_status="saved",
        scene="fraud_transcript_report",
        summary="saved",
        structured_result={"eventType": "structured_result"},
        session_id="session-1",
        agent_id="fraud_transcript_agent",
    )

    items = fraud_transcript_result_service.list_saved_results()

    assert len(items) == 1
    assert items[0].id == saved.id
