# -*- coding: utf-8 -*-
"""FAE scene router — government opportunity + result APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import build_fae_opportunity_service, build_fae_result_service
from .exceptions import FAEGovernmentOpportunityNotFoundError, FAEResultNotFoundError
from .schemas.fae_api import (
    GovernmentOpportunityCreate,
    GovernmentOpportunityDetailResponse,
    GovernmentOpportunityListResponse,
    GovernmentOpportunityRead,
    GovernmentOpportunityUpdate,
    FAEResultLatestResponse,
    FAEResultListResponse,
    FAEResultRead,
    FAEResultFromToolOutputRequest,
)
from .service import FAEOpportunityService, FAEResultService


def _normalize_tool_output_to_opportunity(
    tool_output: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert raw tool output JSON into (gov_opportunity, structured_result) dicts."""

    gov_opportunity: dict[str, Any] = {}
    structured_result: dict[str, Any] = {}

    # Case 1: tool_output already has government_opportunity + structured_result
    candidate_gov = tool_output.get("government_opportunity")
    if isinstance(candidate_gov, dict):
        gov_opportunity = dict(candidate_gov)
    candidate_sr = tool_output.get("structured_result")
    if isinstance(candidate_sr, dict):
        structured_result = dict(candidate_sr)

    # Case 2: tool_output is the structured result itself (e.g. has "result")
    if (
        not isinstance(structured_result.get("result"), dict)
        and isinstance(tool_output.get("result"), dict)
    ):
        structured_result = dict(tool_output)

    # Case 3: the payload inside result has project_name etc.
    result_payload = structured_result.get("result", {})
    if isinstance(result_payload, dict):
        payload = result_payload.get("payload") or result_payload
        if isinstance(payload, dict) and payload.get("project_name"):
            for key in (
                "project_name",
                "customer_name",
                "city",
                "industry",
                "support_type",
                "requirement_desc",
                "opportunity_rating",
                "opportunity_score",
                "budget_min_yuan",
                "budget_max_yuan",
                "budget_note",
                "display_content",
            ):
                if key in payload and key not in gov_opportunity:
                    gov_opportunity[key] = payload[key]
            if isinstance(payload.get("display_content"), list):
                gov_opportunity["display_content"] = payload["display_content"]

    # Case 4: tool_output top-level fields are opportunity fields
    if not gov_opportunity.get("project_name") and tool_output.get("project_name"):
        for key in (
            "project_name",
            "customer_name",
            "city",
            "industry",
            "support_type",
            "requirement_desc",
            "opportunity_rating",
            "opportunity_score",
            "budget_min_yuan",
            "budget_max_yuan",
            "budget_note",
            "display_content",
        ):
            if key in tool_output:
                gov_opportunity[key] = tool_output[key]

    if not isinstance(gov_opportunity.get("display_content"), list):
        gov_opportunity["display_content"] = []

    return gov_opportunity, structured_result


def create_router() -> APIRouter:
    """Return the FAE API router."""

    router = APIRouter(
        prefix="/api/backend/fae",
        tags=["backend", "fae"],
    )

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # ── Government Opportunities ──

    @router.get(
        "/opportunities",
        response_model=GovernmentOpportunityListResponse,
    )
    def list_opportunities(
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
    ) -> GovernmentOpportunityListResponse:
        items = fae_opportunity_service.list_opportunities()
        parsed: list[GovernmentOpportunityRead] = []
        for item in items:
            parsed.append(GovernmentOpportunityRead.model_validate(item))
        return GovernmentOpportunityListResponse(items=parsed)

    @router.get(
        "/opportunities/{opportunity_id}",
        response_model=GovernmentOpportunityDetailResponse,
    )
    def get_opportunity(
        opportunity_id: int,
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
    ) -> GovernmentOpportunityDetailResponse:
        try:
            data = fae_opportunity_service.get_opportunity(opportunity_id)
        except FAEGovernmentOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        return GovernmentOpportunityDetailResponse.model_validate(data)

    @router.post(
        "/opportunities",
        response_model=GovernmentOpportunityRead,
        status_code=status.HTTP_201_CREATED,
    )
    def create_opportunity(
        body: GovernmentOpportunityCreate,
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
    ) -> GovernmentOpportunityRead:
        payload = body.model_dump()
        data = fae_opportunity_service.create_opportunity(payload)
        return GovernmentOpportunityRead.model_validate(data)

    @router.put(
        "/opportunities/{opportunity_id}",
        response_model=GovernmentOpportunityRead,
    )
    def update_opportunity(
        opportunity_id: int,
        body: GovernmentOpportunityUpdate,
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
    ) -> GovernmentOpportunityRead:
        try:
            data = fae_opportunity_service.update_opportunity(
                opportunity_id, body.model_dump(exclude_unset=True)
            )
        except FAEGovernmentOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        return GovernmentOpportunityRead.model_validate(data)

    @router.delete(
        "/opportunities/{opportunity_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_opportunity(
        opportunity_id: int,
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
    ) -> None:
        try:
            fae_opportunity_service.delete_opportunity(opportunity_id)
        except FAEGovernmentOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    # ── FAE Results (for result panel) ──

    @router.get(
        "/results",
        response_model=FAEResultListResponse,
    )
    def list_results(
        saved_only: bool = False,
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> FAEResultListResponse:
        items = fae_result_service.list_results(saved_only=saved_only)
        parsed: list[FAEResultRead] = []
        for item in items:
            parsed.append(FAEResultRead.model_validate(item))
        return FAEResultListResponse(items=parsed)

    @router.get(
        "/results/latest",
        response_model=FAEResultLatestResponse,
    )
    def get_latest_result(
        session_id: str,
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> FAEResultLatestResponse:
        data = fae_result_service.get_latest_result_by_session(session_id)
        if data is None:
            return FAEResultLatestResponse(item=None)
        return FAEResultLatestResponse(
            item=FAEResultRead.model_validate(data),
        )

    # ── Fallback: create result from raw tool output ──
    @router.post("/results/from-tool-output", response_model=FAEResultRead)
    def create_result_from_tool_output(
        body: FAEResultFromToolOutputRequest,
        fae_opportunity_service: FAEOpportunityService = Depends(
            build_fae_opportunity_service,
        ),
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> FAEResultRead:
        gov_opportunity, structured_result = _normalize_tool_output_to_opportunity(
            body.tool_output,
        )

        # 1. Persist opportunity
        opportunity = fae_opportunity_service.create_opportunity(
            {**gov_opportunity, "session_id": body.session_id}
        )
        opportunity_id: int = opportunity["id"]

        # 2. Persist result
        result = structured_result.get("result", {}) if isinstance(structured_result, dict) else {}
        payload = result.get("payload") if isinstance(result, dict) else {}
        if not isinstance(payload, dict):
            payload = gov_opportunity

        title = str(
            gov_opportunity.get("project_name")
            or structured_result.get("title")
            or "商机分析"
        ).strip()

        result_record = fae_result_service.create_result(
            title=title,
            result_type=str(result.get("type", "government_opportunity") if isinstance(result, dict) else "government_opportunity"),
            scene=gov_opportunity.get("industry"),
            summary=gov_opportunity.get("output"),
            detail_content=gov_opportunity.get("display_content")
            if isinstance(gov_opportunity.get("display_content"), list)
            else [],
            info={
                "toolName": body.tool_name,
                "structuredResult": structured_result,
                "payload": payload,
                "opportunityId": opportunity_id,
            },
            basic_info=gov_opportunity,
            session_id=body.session_id,
            agent_id=body.agent_id or "RA-agent",
        )

        return FAEResultRead.model_validate(result_record)

    @router.get("/results/{result_id}", response_model=FAEResultRead)
    def get_result(
        result_id: int,
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> FAEResultRead:
        try:
            data = fae_result_service.get_result(result_id)
        except FAEResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        return FAEResultRead.model_validate(data)

    @router.post("/results/{result_id}/save", response_model=FAEResultRead)
    def save_result(
        result_id: int,
        fae_result_service: FAEResultService = Depends(
            build_fae_result_service,
        ),
    ) -> FAEResultRead:
        try:
            data = fae_result_service.mark_result_as_saved(result_id)
        except FAEResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        return FAEResultRead.model_validate(data)

    return router
