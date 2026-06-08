"""Tests for the FAE structured-result persistence flow."""

from __future__ import annotations

import json
from pathlib import Path

from agentscope.message import Msg

from backend.database.connection import BackendDatabase
from backend.scenes.fae import persistence as fae_persistence
from backend.scenes.fae.parsers.government_opportunity_parser import (
    inject_government_opportunity_metadata,
    is_valid_fae_structured_result,
)
from backend.scenes.fae.persistence import FAEGovernmentOpportunityPersistence
from backend.scenes.fae.service import FAEOpportunityService, FAEResultService


def _structured_result() -> dict:
    return {
        "eventType": "structured_result",
        "version": "1.0",
        "title": "Smart government cloud",
        "result": {
            "type": "government_opportunity",
            "payload": {
            "scene": "government_opportunity",
            "title": "Smart government cloud",
            "output": "A high value FAE opportunity.",
            "basicInfo": {
                "projectName": "Smart government cloud",
                "customerName": "City data bureau",
                    "city": "Guangzhou",
                    "industry": "Government",
                    "supportType": "Technical support",
                },
                "requirementDesc": "Build a unified government cloud platform.",
                "opportunityRating": "high",
                "opportunityScore": 92,
                "budget": {
                    "minYuan": 1000000,
                    "maxYuan": 2000000,
                    "note": "Initial estimate",
                },
                "attachments": [
                    {
                        "type": "pdf",
                        "fileName": "proposal.pdf",
                        "filePath": "/reports/proposal.pdf",
                    },
                ],
            },
        },
        "meta": {
            "bizModule": "fae",
            "source": "agent_output",
        },
    }


def test_fae_parser_accepts_structured_result_json() -> None:
    """RA-agent can emit a fraud-transcript-style structured_result JSON."""

    event = _structured_result()
    msg = Msg(
        name="Assistant",
        role="assistant",
        content=f"```json\n{json.dumps(event)}\n```",
    )

    inject_government_opportunity_metadata(msg)

    assert is_valid_fae_structured_result(msg.metadata["structured_result"])
    assert msg.metadata["government_opportunity"]["project_name"] == (
        "Smart government cloud"
    )
    assert msg.metadata["government_opportunity"]["opportunity_score"] == 92


def test_fae_structured_result_persistence_creates_result_and_opportunity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """FAE structured_result should persist into both FAE tables."""

    database = BackendDatabase(tmp_path / "fae-flow.sqlite3")
    monkeypatch.setattr(
        fae_persistence,
        "get_backend_database",
        lambda: database,
    )

    event = _structured_result()
    msg = Msg(
        name="Assistant",
        role="assistant",
        content=json.dumps(event),
    )
    inject_government_opportunity_metadata(msg)

    FAEGovernmentOpportunityPersistence().persist_message(
        msg,
        session_id="session-fae",
        agent_id="ra-agentv1",
    )

    opportunities = FAEOpportunityService(database).list_opportunities()
    results = FAEResultService(database).list_results()

    assert len(opportunities) == 1
    assert opportunities[0]["project_name"] == "Smart government cloud"
    assert opportunities[0]["session_id"] == "session-fae"
    assert opportunities[0]["agent_id"] == "ra-agentv1"
    assert len(results) == 1
    assert results[0]["agent_id"] == "ra-agentv1"
    assert results[0]["info"]["opportunityId"] == opportunities[0]["id"]
    assert results[0]["info"]["structuredResult"]["meta"]["bizModule"] == "fae"
