# -*- coding: utf-8 -*-
"""Unified results router for business result panels."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.scenes.fae.dependencies import build_fae_result_service
from backend.scenes.fae.service import FAEResultService
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

    return router
