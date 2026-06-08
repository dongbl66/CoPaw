# -*- coding: utf-8 -*-
"""Parse RA-agent government opportunity output into structured_result."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agentscope.message import Msg
from pydantic import ValidationError

from ..schemas.government_opportunity import GovernmentOpportunityAnalysis

logger = logging.getLogger(__name__)

FAE_BIZ_MODULE = "fae"
FAE_SCENE = "government_opportunity"


class GovernmentOpportunityResultBuilder:
    """Build frontend-compatible structured_result from RA-agent output."""

    def build(
        self,
        analysis: GovernmentOpportunityAnalysis,
    ) -> dict[str, Any]:
        """Convert GovernmentOpportunityAnalysis → StructuredResultEvent."""

        return {
            "eventType": "structured_result",
            "version": "1.0",
            "title": analysis.project_name,
            "subtitle": analysis.industry,
            "result": {
                "type": "government_opportunity",
                "payload": {
                    "scene": FAE_SCENE,
                    "title": analysis.project_name,
                    "summary": analysis.output,
                    "basicInfo": {
                        "projectName": analysis.project_name,
                        "customerName": analysis.customer_name,
                        "city": analysis.city,
                        "industry": analysis.industry,
                        "supportType": analysis.support_type.value,
                    },
                    "requirementDesc": analysis.requirement_desc,
                    "opportunityRating": analysis.opportunity_rating.value,
                    "opportunityScore": analysis.opportunity_score,
                    "budget": (
                        {
                            "minYuan": analysis.budget.min_yuan,
                            "maxYuan": analysis.budget.max_yuan,
                            "note": analysis.budget.note,
                        }
                        if analysis.budget
                        else None
                    ),
                    "attachments": [
                        {
                            "kind": item.type,
                            "fileName": item.file_name,
                            "filePath": item.file_path,
                            "fileUrl": item.file_url,
                        }
                        for item in analysis.display_content
                    ],
                },
            },
            "layout": {
                "autoOpen": True,
                "replace": True,
            },
            "meta": {
                "bizModule": FAE_BIZ_MODULE,
                "source": "agent_output",
            },
        }

    def build_text_event(self, output_text: str) -> dict[str, Any]:
        """Fallback: build a plain-text structured_result."""

        return {
            "eventType": "structured_result",
            "version": "1.0",
            "title": "商机分析",
            "result": {
                "type": "text",
                "payload": {
                    "text": output_text,
                    "markdown": True,
                },
            },
            "layout": {
                "autoOpen": True,
                "replace": True,
            },
            "meta": {
                "bizModule": FAE_BIZ_MODULE,
                "source": "agent_output",
            },
        }


def inject_government_opportunity_metadata(msg: Msg) -> None:
    """Parse RA-agent reply and inject government_opportunity metadata.

    Works with both structured_model output and free-text JSON.
    """

    logger.debug(
        "Starting government opportunity injection: msg_name=%s, msg_role=%s",
        msg.name,
        msg.role,
    )

    if not isinstance(msg.metadata, dict):
        msg.metadata = {}

    raw_text = _get_text_content(msg)
    if not raw_text:
        logger.debug("Skip government opportunity parse: no text content")
        return

    logger.debug("Parsing government opportunity from text (length=%d)", len(raw_text))

    builder = GovernmentOpportunityResultBuilder()
    structured_result = _extract_structured_result(raw_text)
    if is_valid_fae_structured_result(structured_result):
        msg.metadata["structured_result"] = structured_result
        gov_opportunity = government_opportunity_from_structured_result(
            structured_result,
        )
        if gov_opportunity:
            msg.metadata["government_opportunity"] = gov_opportunity
            msg.metadata["government_opportunity_source"] = "structured_result"
        logger.info(
            "Injected FAE structured result metadata: title=%s",
            structured_result.get("title"),
        )
        return

    analysis = _extract_analysis(raw_text)

    if analysis is not None:
        logger.info(
            "Found government opportunity analysis: project=%s, rating=%s",
            analysis.project_name,
            analysis.opportunity_rating.value,
        )
        msg.metadata["government_opportunity"] = analysis.model_dump()
        msg.metadata["government_opportunity_source"] = "agent_output"
        msg.metadata["structured_result"] = builder.build(analysis)
    else:
        logger.debug("No valid government opportunity JSON found; falling back to text")
        msg.metadata["structured_result"] = builder.build_text_event(raw_text)

    logger.info(
        "Injected structured result: type=%s, title=%s",
        msg.metadata["structured_result"].get("result", {}).get("type"),
        msg.metadata["structured_result"].get("title"),
    )


def is_valid_fae_structured_result(value: Any) -> bool:
    """Return True when value is a FAE structured-result event."""

    if not isinstance(value, dict):
        return False
    if value.get("eventType") != "structured_result":
        return False
    result = value.get("result")
    if not isinstance(result, dict):
        return False
    result_type = result.get("type")
    if result_type not in {"government_opportunity", "business"}:
        return False
    meta = value.get("meta")
    if isinstance(meta, dict) and meta.get("bizModule") == FAE_BIZ_MODULE:
        return True
    payload = result.get("payload")
    return isinstance(payload, dict) and payload.get("scene") == FAE_SCENE


def government_opportunity_from_structured_result(
    structured_result: dict[str, Any],
) -> dict[str, Any]:
    """Normalize a FAE structured result payload into persistence fields."""

    result = structured_result.get("result")
    if not isinstance(result, dict):
        return {}
    payload = result.get("payload")
    if not isinstance(payload, dict):
        return {}

    basic_info = payload.get("basicInfo")
    if not isinstance(basic_info, dict):
        basic_info = {}

    budget = payload.get("budget")
    if not isinstance(budget, dict):
        budget = {}

    attachments = payload.get("attachments")
    display_content = (
        [item for item in attachments if isinstance(item, dict)]
        if isinstance(attachments, list)
        else []
    )

    return {
        "output": _first_text(payload, "output")
        or _first_text(payload, "summary")
        or _first_text(structured_result, "subtitle"),
        "project_name": _first_text(payload, "project_name")
        or _first_text(payload, "projectName")
        or _first_text(basic_info, "projectName")
        or _first_text(structured_result, "title"),
        "customer_name": _first_text(payload, "customer_name")
        or _first_text(payload, "customerName")
        or _first_text(basic_info, "customerName"),
        "city": _first_text(payload, "city") or _first_text(basic_info, "city"),
        "industry": _first_text(payload, "industry")
        or _first_text(basic_info, "industry"),
        "support_type": _first_text(payload, "support_type")
        or _first_text(payload, "supportType")
        or _first_text(basic_info, "supportType"),
        "requirement_desc": _first_text(payload, "requirement_desc")
        or _first_text(payload, "requirementDesc"),
        "opportunity_rating": _first_text(payload, "opportunity_rating")
        or _first_text(payload, "opportunityRating")
        or "medium",
        "opportunity_score": payload.get("opportunity_score")
        if payload.get("opportunity_score") is not None
        else payload.get("opportunityScore"),
        "budget": {
            "min_yuan": budget.get("min_yuan", budget.get("minYuan")),
            "max_yuan": budget.get("max_yuan", budget.get("maxYuan")),
            "note": budget.get("note"),
        },
        "display_content": display_content,
    }


def _get_text_content(msg: Msg) -> str | None:
    """Extract concatenated text content from a Msg."""

    if isinstance(msg.content, str):
        return msg.content.strip() or None
    if isinstance(msg.content, list):
        parts: list[str] = []
        for block in msg.content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return "\n".join(parts).strip() or None
    return None


def _extract_analysis(text: str) -> GovernmentOpportunityAnalysis | None:
    """Extract GovernmentOpportunityAnalysis from free-form text."""

    candidates = _extract_json_candidates(text)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue

        try:
            return GovernmentOpportunityAnalysis.model_validate(parsed)
        except ValidationError as e:
            logger.debug(
                "JSON candidate did not match GovernmentOpportunityAnalysis: %s",
                e.errors(),
            )
            continue
    return None


def _extract_structured_result(text: str) -> dict[str, Any] | None:
    """Extract a structured_result JSON object from free-form text."""

    for candidate in _extract_json_candidates(text):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get("eventType") == "structured_result":
            return parsed
    return None


def _first_text(container: dict[str, Any], key: str) -> str:
    value = container.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _extract_json_candidates(text: str) -> list[str]:
    """Extract JSON candidate strings from text."""

    candidates: list[str] = []

    # 1. fenced code blocks
    for match in re.finditer(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
        flags=re.IGNORECASE,
    ):
        candidate = match.group(1).strip()
        if candidate:
            candidates.append(candidate)

    # 2. raw JSON (first { to last })
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])

    # 3. full text
    candidates.append(text)
    return candidates
