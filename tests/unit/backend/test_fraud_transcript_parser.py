# -*- coding: utf-8 -*-
"""Tests for fraud transcript structured-result parsing."""

from __future__ import annotations

import json

from agentscope.message import Msg

from backend.scenes.fraud_transcript.parsers.transcript_report import (
    inject_fraud_transcript_metadata,
)


def _fraud_structured_result() -> dict:
    return {
        "eventType": "structured_result",
        "version": "1.0",
        "title": "电诈笔录分析报告",
        "result": {
            "type": "business",
            "payload": {
                "title": "电诈笔录分析报告",
                "summary": "受害人通过微信群接触诈骗人员。",
                "scene": "fraud_transcript_report",
                "basicInfo": {"姓名": "张三", "涉案金额": "50000"},
                "productInfo": {"风险等级": "高", "质量评分": 82},
                "opportunities": [
                    {
                        "title": "问题：你是如何接触到对方的？",
                        "level": "已回答",
                        "type": "模板问答",
                        "summary": "通过微信群接触对方。",
                        "reason": "接触渠道已明确。",
                    },
                ],
                "attachments": [],
            },
        },
        "meta": {
            "bizModule": "fraud_transcript",
            "source": "skill",
            "timestamp": 0,
        },
    }


def test_inject_fraud_transcript_metadata_accepts_standard_event() -> None:
    msg = Msg(
        name="Assistant",
        role="assistant",
        content=f"```json\n{json.dumps(_fraud_structured_result(), ensure_ascii=False)}\n```",
    )

    inject_fraud_transcript_metadata(msg)

    assert msg.metadata["structured_result"]["title"] == "电诈笔录分析报告"
    assert msg.metadata["business_result"] == {
        "title": "电诈笔录分析报告",
        "summary": "受害人通过微信群接触诈骗人员。",
        "basic_info": {"姓名": "张三", "涉案金额": "50000"},
        "product_info": {"风险等级": "高", "质量评分": 82},
        "opportunities": [
            {
                "title": "问题：你是如何接触到对方的？",
                "level": "已回答",
                "type": "模板问答",
                "summary": "通过微信群接触对方。",
                "reason": "接触渠道已明确。",
            },
        ],
        "display_content": [],
    }


def test_inject_fraud_transcript_metadata_ignores_other_business_modules() -> None:
    event = _fraud_structured_result()
    event["meta"]["bizModule"] = "marketing"
    msg = Msg(
        name="Assistant",
        role="assistant",
        content=json.dumps(event, ensure_ascii=False),
    )

    inject_fraud_transcript_metadata(msg)

    assert msg.metadata == {}
