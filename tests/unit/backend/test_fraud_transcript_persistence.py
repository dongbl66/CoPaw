# -*- coding: utf-8 -*-
"""Tests for automatic fraud transcript persistence."""

from __future__ import annotations

from pathlib import Path

from agentscope.message import Msg

from backend.database.connection import BackendDatabase
from backend.scenes.fraud_transcript.persistence import (
    FraudTranscriptStructuredResultPersistence,
)


def test_fraud_transcript_persistence_saves_valid_report(
    tmp_path: Path,
) -> None:
    database = BackendDatabase(tmp_path / "fraud-transcript.sqlite3")
    persistence = FraudTranscriptStructuredResultPersistence(database=database)
    msg = Msg(name="Assistant", role="assistant", content="结构化报告")
    msg.metadata = {
        "business_result": {
            "title": "电诈笔录分析报告",
            "summary": "受害人通过微信群接触诈骗人员。",
            "basic_info": {"姓名": "张三"},
            "product_info": {"风险等级": "高"},
            "opportunities": [{"title": "问题：如何接触？", "summary": "微信群"}],
            "display_content": [],
        },
        "structured_result": {
            "eventType": "structured_result",
            "title": "电诈笔录分析报告",
            "result": {
                "type": "business",
                "payload": {
                    "title": "电诈笔录分析报告",
                    "summary": "受害人通过微信群接触诈骗人员。",
                    "scene": "fraud_transcript_report",
                    "basicInfo": {"姓名": "张三"},
                    "productInfo": {"风险等级": "高"},
                    "opportunities": [
                        {"title": "问题：如何接触？", "summary": "微信群"},
                    ],
                    "attachments": [],
                },
            },
            "meta": {"bizModule": "fraud_transcript"},
        },
    }

    persistence.persist_message(
        msg,
        session_id="session-1",
        agent_id="fraud_transcript_agent",
    )

    with database.transaction() as connection:
        row = connection.execute(
            "SELECT title, result_type, save_status, scene, summary, "
            "basic_info_json, product_info_json, qa_records_json, "
            "session_id, agent_id FROM fraud_transcript_results",
        ).fetchone()

    assert row is not None
    assert row["title"] == "电诈笔录分析报告"
    assert row["result_type"] == "business"
    assert row["save_status"] == "draft"
    assert row["scene"] == "fraud_transcript_report"
    assert row["summary"] == "受害人通过微信群接触诈骗人员。"
    assert row["session_id"] == "session-1"
    assert row["agent_id"] == "fraud_transcript_agent"
    assert "张三" in row["basic_info_json"]
    assert "风险等级" in row["product_info_json"]
    assert "如何接触" in row["qa_records_json"]


def test_fraud_transcript_persistence_ignores_other_scenes(
    tmp_path: Path,
) -> None:
    database = BackendDatabase(tmp_path / "fraud-transcript-ignore.sqlite3")
    persistence = FraudTranscriptStructuredResultPersistence(database=database)
    msg = Msg(name="Assistant", role="assistant", content="结构化报告")
    msg.metadata = {
        "structured_result": {
            "eventType": "structured_result",
            "title": "营销报告",
            "result": {
                "type": "business",
                "payload": {"scene": "marketing_report"},
            },
            "meta": {"bizModule": "marketing"},
        },
    }

    persistence.persist_message(
        msg,
        session_id="session-1",
        agent_id="fraud_transcript_agent",
    )

    with database.transaction() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM fraud_transcript_results",
        ).fetchone()[0]

    assert count == 0
