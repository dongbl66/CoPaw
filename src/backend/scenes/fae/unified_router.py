# -*- coding: utf-8 -*-
"""Unified results router for business result panels."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from qwenpaw.constant import WORKING_DIR

from backend.scenes.common.display_assets import resolve_display_asset_path
from backend.scenes.fae.dependencies import (
    build_fae_opportunity_service,
    build_fae_result_service,
)
from backend.scenes.fae.exceptions import (
    FAEGovernmentOpportunityNotFoundError,
    FAEResultNotFoundError,
)
from backend.scenes.fae.service import FAEOpportunityService, FAEResultService
from backend.scenes.fraud_transcript.dependencies import (
    build_fraud_transcript_result_service,
)
from backend.scenes.fraud_transcript.service import FraudTranscriptResultService
from backend.scenes.marketing.dependencies import build_marketing_result_service
from backend.scenes.marketing.service import MarketingResultService

BizModule = str
logger = logging.getLogger(__name__)


def _to_dict_or_passthrough(record: Any) -> dict[str, Any]:
    """Convert Pydantic model to dict, passthrough dict."""
    if isinstance(record, dict):
        return record
    if hasattr(record, "model_dump"):
        return record.model_dump()
    return record


def _normalize_biz_module(value: str | None) -> BizModule:
    if value is None or value == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="biz_module is required",
        )
    normalized = value.replace("-", "_")
    if normalized in {"marketing", "fae", "fraud_transcript"}:
        return normalized
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported biz_module: {value}",
    )


def _response(item: Any, biz_module: BizModule | None) -> dict[str, Any]:
    return {
        "item": None if item is None else _to_dict_or_passthrough(item),
        "biz_module": biz_module,
    }


def _get_latest_or_none(
    service: Any,
    session_id: str,
    biz_module: BizModule,
) -> Any | None:
    try:
        return service.get_latest_result_by_session(session_id)
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).lower():
            logger.info(
                "Skipping %s latest result lookup because its table is missing: %s",
                biz_module,
                exc,
            )
            return None
        raise


def _asset_response(
    *,
    record: dict[str, Any],
    display_content: list[dict[str, Any]],
    asset_id: str,
) -> FileResponse:
    path, media_type = resolve_display_asset_path(
        display_content,
        asset_id=asset_id,
        agent_id=record.get("agent_id") if isinstance(record, dict) else None,
        working_dir=WORKING_DIR,
    )
    return FileResponse(path, media_type=media_type, filename=path.name)


def _display_content_from_result(record: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("display_content", "detail_content", "attachments"):
        value = record.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def create_router() -> APIRouter:
    """Return the unified results API router."""

    router = APIRouter(
        prefix="/api/backend/results",
        tags=["backend", "results"],
    )

    @router.get("/latest")
    def get_latest_result(
        session_id: str,
        biz_module: str | None = None,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
        fraud_transcript_result_service: FraudTranscriptResultService = Depends(
            build_fraud_transcript_result_service,
        ),
    ) -> dict[str, Any]:
        """Get the latest result for one session.

        biz_module is required so the result panel never scans unrelated
        business tables.
        """
        target_module = _normalize_biz_module(biz_module)

        if target_module == "marketing":
            return _response(
                _get_latest_or_none(
                    marketing_result_service,
                    session_id,
                    "marketing",
                ),
                "marketing",
            )
        if target_module == "fae":
            return _response(
                _get_latest_or_none(fae_result_service, session_id, "fae"),
                "fae",
            )
        if target_module == "fraud_transcript":
            return _response(
                _get_latest_or_none(
                    fraud_transcript_result_service,
                    session_id,
                    "fraud_transcript",
                ),
                "fraud_transcript",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported biz_module: {biz_module}",
        )

    @router.get("/{biz_module}/{result_id}/assets/{asset_id}")
    def get_result_asset(
        biz_module: str,
        result_id: int,
        asset_id: str,
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> FileResponse:
        """Serve one registered display_content asset for a stored result."""

        target_module = _normalize_biz_module(biz_module)
        if target_module != "fae":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assets are not implemented for biz_module: {biz_module}",
            )

        try:
            record = fae_result_service.get_result(result_id)
        except FAEResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        return _asset_response(
            record=record,
            display_content=_display_content_from_result(record),
            asset_id=asset_id,
        )

    @router.get("/{biz_module}/opportunities/{opportunity_id}/assets/{asset_id}")
    def get_opportunity_asset(
        biz_module: str,
        opportunity_id: int,
        asset_id: str,
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
    ) -> FileResponse:
        """Serve one registered display_content asset for a FAE opportunity."""

        target_module = _normalize_biz_module(biz_module)
        if target_module != "fae":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Opportunity assets are only implemented for "
                    f"biz_module: fae, got {biz_module}"
                ),
            )

        try:
            record = fae_opportunity_service.get_opportunity(opportunity_id)
        except FAEGovernmentOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        display_content = record.get("display_content")
        return _asset_response(
            record=record,
            display_content=display_content if isinstance(display_content, list) else [],
            asset_id=asset_id,
        )

    return router
