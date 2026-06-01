# -*- coding: utf-8 -*-

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import (
    build_marketing_opportunity_service,
    build_marketing_result_service,
)
from .exceptions import (
    MarketingOpportunityNotFoundError,
    MarketingResultNotFoundError,
)
from .schemas.opportunity import (
    MarketingOpportunityCreate,
    MarketingOpportunityListResponse,
    MarketingOpportunityRead,
    MarketingOpportunityUpdate,
)
from .schemas.result import (
    MarketingResultCreate,
    MarketingResultLatestResponse,
    MarketingResultListResponse,
    MarketingResultRead,
    MarketingResultUpdate,
)
from .service import MarketingOpportunityService, MarketingResultService


def create_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/backend/marketing",
        tags=["backend", "marketing"],
    )

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/results", response_model=MarketingResultListResponse)
    def list_results(
        saved_only: bool = False,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> MarketingResultListResponse:
        items = (
            marketing_result_service.list_saved_results()
            if saved_only
            else marketing_result_service.list_results()
        )
        return MarketingResultListResponse(items=items)

    @router.get(
        "/results/latest",
        response_model=MarketingResultLatestResponse,
    )
    def get_latest_result(
        session_id: str,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> MarketingResultLatestResponse:
        return MarketingResultLatestResponse(
            item=marketing_result_service.get_latest_result_by_session(
                session_id,
            ),
        )

    @router.post("/results/{result_id}/save", response_model=MarketingResultRead)
    def save_result(
        result_id: int,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> MarketingResultRead:
        try:
            return marketing_result_service.mark_result_as_saved(result_id)
        except MarketingResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.get("/results/{result_id}", response_model=MarketingResultRead)
    def get_result(
        result_id: int,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> MarketingResultRead:
        try:
            return marketing_result_service.get_result(result_id)
        except MarketingResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.post(
        "/results",
        response_model=MarketingResultRead,
        status_code=status.HTTP_201_CREATED,
    )
    def create_result(
        body: MarketingResultCreate,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> MarketingResultRead:
        return marketing_result_service.create_result(
            title=body.title,
            result_type=body.result_type,
            save_status=body.save_status,
            scene=body.scene,
            summary=body.summary,
            detail_content=body.detail_content,
            info=body.info,
            basic_info=body.basic_info,
            product_info=body.product_info,
            attachments=body.attachments,
            session_id=body.session_id,
            agent_id=body.agent_id,
        )

    @router.put("/results/{result_id}", response_model=MarketingResultRead)
    def update_result(
        result_id: int,
        body: MarketingResultUpdate,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> MarketingResultRead:
        try:
            return marketing_result_service.update_result(
                result_id,
                title=body.title,
                result_type=body.result_type,
                save_status=body.save_status,
                scene=body.scene,
                summary=body.summary,
                detail_content=body.detail_content,
                info=body.info,
                basic_info=body.basic_info,
                product_info=body.product_info,
                attachments=body.attachments,
                session_id=body.session_id,
                agent_id=body.agent_id,
            )
        except MarketingResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.get(
        "/opportunities",
        response_model=MarketingOpportunityListResponse,
    )
    def list_opportunities(
        marketing_opportunity_service: MarketingOpportunityService = Depends(
            build_marketing_opportunity_service,
        ),
    ) -> MarketingOpportunityListResponse:
        return MarketingOpportunityListResponse(
            items=marketing_opportunity_service.list_opportunities(),
        )

    @router.get(
        "/opportunities/{opportunity_id}",
        response_model=MarketingOpportunityRead,
    )
    def get_opportunity(
        opportunity_id: int,
        marketing_opportunity_service: MarketingOpportunityService = Depends(
            build_marketing_opportunity_service,
        ),
    ) -> MarketingOpportunityRead:
        try:
            return marketing_opportunity_service.get_opportunity(opportunity_id)
        except MarketingOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.post(
        "/opportunities",
        response_model=MarketingOpportunityRead,
        status_code=status.HTTP_201_CREATED,
    )
    def create_opportunity(
        body: MarketingOpportunityCreate,
        marketing_opportunity_service: MarketingOpportunityService = Depends(
            build_marketing_opportunity_service,
        ),
    ) -> MarketingOpportunityRead:
        return marketing_opportunity_service.create_opportunity(
            title=body.title,
            opportunity_type=body.opportunity_type,
            region=body.region,
            source=body.source,
            publish_time=body.publish_time,
            deadline=body.deadline,
            credibility=body.credibility,
            contact=body.contact,
            budget=body.budget,
            purchase_amount=body.purchase_amount,
            link_status=body.link_status,
            reason=body.reason,
            original_link=body.original_link,
            level=body.level,
            summary=body.summary,
            session_id=body.session_id,
            agent_id=body.agent_id,
        )

    @router.put(
        "/opportunities/{opportunity_id}",
        response_model=MarketingOpportunityRead,
    )
    def update_opportunity(
        opportunity_id: int,
        body: MarketingOpportunityUpdate,
        marketing_opportunity_service: MarketingOpportunityService = Depends(
            build_marketing_opportunity_service,
        ),
    ) -> MarketingOpportunityRead:
        try:
            return marketing_opportunity_service.update_opportunity(
                opportunity_id,
                title=body.title,
                opportunity_type=body.opportunity_type,
                region=body.region,
                source=body.source,
                publish_time=body.publish_time,
                deadline=body.deadline,
                credibility=body.credibility,
                contact=body.contact,
                budget=body.budget,
                purchase_amount=body.purchase_amount,
                link_status=body.link_status,
                reason=body.reason,
                original_link=body.original_link,
                level=body.level,
                summary=body.summary,
                session_id=body.session_id,
                agent_id=body.agent_id,
            )
        except MarketingOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.delete(
        "/opportunities/{opportunity_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_opportunity(
        opportunity_id: int,
        marketing_opportunity_service: MarketingOpportunityService = Depends(
            build_marketing_opportunity_service,
        ),
    ) -> None:
        try:
            marketing_opportunity_service.delete_opportunity(opportunity_id)
        except MarketingOpportunityNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_result(
        result_id: int,
        marketing_result_service: MarketingResultService = Depends(
            build_marketing_result_service,
        ),
    ) -> None:
        try:
            marketing_result_service.delete_result(result_id)
        except MarketingResultNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    return router
