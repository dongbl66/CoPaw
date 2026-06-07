# -*- coding: utf-8 -*-
"""API router for fraud transcript results."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import build_fraud_transcript_result_service
from .exceptions import FraudTranscriptResultNotFoundError
from .schemas.result import (
    FraudTranscriptResultLatestResponse,
    FraudTranscriptResultListResponse,
    FraudTranscriptResultRead,
)
from .service import FraudTranscriptResultService


def create_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/backend/fraud-transcript",
        tags=["backend", "fraud-transcript"],
    )

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/results", response_model=FraudTranscriptResultListResponse)
    def list_results(
        saved_only: bool = False,
        service: FraudTranscriptResultService = Depends(
            build_fraud_transcript_result_service,
        ),
    ) -> FraudTranscriptResultListResponse:
        items = service.list_saved_results() if saved_only else service.list_results()
        return FraudTranscriptResultListResponse(items=items)

    @router.get(
        "/results/latest",
        response_model=FraudTranscriptResultLatestResponse,
    )
    def get_latest_result(
        session_id: str,
        service: FraudTranscriptResultService = Depends(
            build_fraud_transcript_result_service,
        ),
    ) -> FraudTranscriptResultLatestResponse:
        return FraudTranscriptResultLatestResponse(
            item=service.get_latest_result_by_session(session_id),
        )

    @router.get("/results/{result_id}", response_model=FraudTranscriptResultRead)
    def get_result(
        result_id: int,
        service: FraudTranscriptResultService = Depends(
            build_fraud_transcript_result_service,
        ),
    ) -> FraudTranscriptResultRead:
        try:
            return service.get_result(result_id)
        except FraudTranscriptResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.post("/results/{result_id}/save", response_model=FraudTranscriptResultRead)
    def save_result(
        result_id: int,
        service: FraudTranscriptResultService = Depends(
            build_fraud_transcript_result_service,
        ),
    ) -> FraudTranscriptResultRead:
        try:
            return service.mark_result_as_saved(result_id)
        except FraudTranscriptResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    return router

