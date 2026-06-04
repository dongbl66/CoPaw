# -*- coding: utf-8 -*-
"""Unified results router — merges marketing + FAE results for the result panel."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import Any

from backend.scenes.marketing.dependencies import build_marketing_result_service
from backend.scenes.fae.dependencies import build_fae_result_service
from backend.scenes.marketing.service import MarketingResultService
from backend.scenes.fae.service import FAEResultService


def _get_record_id(record: Any) -> int:
    """Get id from either Pydantic model or dict."""
    if isinstance(record, dict):
        return record.get("id", 0)
    return getattr(record, "id", 0) or 0


def _to_dict_or_passthrough(record: Any) -> dict[str, Any]:
    """Convert Pydantic model to dict, passthrough dict."""
    if isinstance(record, dict):
        return record
    if hasattr(record, "model_dump"):
        return record.model_dump()
    return record


def create_router() -> APIRouter:
    """Return the unified results API router."""

    router = APIRouter(
        prefix="/api/backend/results",
        tags=["backend", "results"],
    )

    @router.get("/latest")
    def get_latest_result(
        session_id: str,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> dict[str, Any]:
        """Get the latest result from both marketing and FAE tables."""
        marketing_result = marketing_result_service.get_latest_result_by_session(
            session_id,
        )
        fae_result = fae_result_service.get_latest_result_by_session(session_id)

        if fae_result is None and marketing_result is None:
            return {"item": None}

        if marketing_result is None:
            return {"item": _to_dict_or_passthrough(fae_result)}
        if fae_result is None:
            return {"item": _to_dict_or_passthrough(marketing_result)}

        marketing_id = _get_record_id(marketing_result)
        fae_id = _get_record_id(fae_result)

        if fae_id > marketing_id:
            return {"item": _to_dict_or_passthrough(fae_result)}
        return {"item": _to_dict_or_passthrough(marketing_result)}

    return router
