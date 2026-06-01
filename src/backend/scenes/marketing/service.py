# -*- coding: utf-8 -*-
"""Service layer for marketing result CRUD."""

from __future__ import annotations

from backend.database.connection import BackendDatabase

from .repository import (
    MarketingOpportunityRepository,
    MarketingResultRepository,
)
from .schemas.opportunity import (
    MarketingOpportunityCreate,
    MarketingOpportunityRead,
    MarketingOpportunityUpdate,
)
from .schemas.result import (
    MarketingResultCreate,
    MarketingResultFileCreate,
    MarketingResultRead,
    MarketingResultUpdate,
)


class MarketingResultService:
    """Orchestrate marketing result CRUD operations."""

    def __init__(self, database: BackendDatabase) -> None:
        self._database = database

    def list_results(self) -> list[MarketingResultRead]:
        """List all saved marketing results."""

        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.list_results()

    def get_result(self, result_id: int) -> MarketingResultRead:
        """Get one marketing result."""

        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.get_result(result_id)

    def get_latest_result_by_session(
        self,
        session_id: str,
    ) -> MarketingResultRead | None:
        """Get the latest marketing result under one session."""

        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.get_latest_result_by_session(
                session_id,
            )

    def create_result(
        self,
        *,
        title: str,
        result_type: str,
        save_status: str = "draft",
        scene: str | None = None,
        summary: str | None = None,
        detail_content: list[dict] | None = None,
        info: dict | None = None,
        basic_info: dict | None = None,
        product_info: dict | None = None,
        attachments: list[dict] | list[MarketingResultFileCreate] | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> MarketingResultRead:
        """Create one marketing result."""

        create_payload = MarketingResultCreate(
            title=title,
            result_type=result_type,
            save_status=save_status,
            scene=scene,
            summary=summary,
            detail_content=detail_content or [],
            info=info or {},
            basic_info=basic_info or {},
            product_info=product_info or {},
            attachments=[
                item
                if isinstance(item, MarketingResultFileCreate)
                else MarketingResultFileCreate(**item)
                for item in (attachments or [])
            ],
            session_id=session_id,
            agent_id=agent_id,
        )
        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.create_result(create_payload)

    def update_result(
        self,
        result_id: int,
        *,
        title: str | None = None,
        result_type: str | None = None,
        save_status: str | None = None,
        scene: str | None = None,
        summary: str | None = None,
        detail_content: list[dict] | None = None,
        info: dict | None = None,
        basic_info: dict | None = None,
        product_info: dict | None = None,
        attachments: list[dict] | list[MarketingResultFileCreate] | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> MarketingResultRead:
        """Update one marketing result."""

        update_payload = MarketingResultUpdate(
            title=title,
            result_type=result_type,
            save_status=save_status,
            scene=scene,
            summary=summary,
            detail_content=detail_content,
            info=info,
            basic_info=basic_info,
            product_info=product_info,
            attachments=(
                [
                    item
                    if isinstance(item, MarketingResultFileCreate)
                    else MarketingResultFileCreate(**item)
                    for item in attachments
                ]
                if attachments is not None
                else None
            ),
            session_id=session_id,
            agent_id=agent_id,
        )
        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.update_result(
                result_id,
                update_payload,
            )

    def delete_result(self, result_id: int) -> bool:
        """Delete one marketing result."""

        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.delete_result(result_id)

    def list_saved_results(self) -> list[MarketingResultRead]:
        """List manually saved marketing results."""

        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.list_saved_results()

    def mark_result_as_saved(self, result_id: int) -> MarketingResultRead:
        """Mark one marketing result as saved."""

        with self._database.transaction() as connection:
            marketing_result_repository = MarketingResultRepository(connection)
            return marketing_result_repository.mark_result_as_saved(result_id)


class MarketingOpportunityService:
    """Orchestrate marketing opportunity CRUD operations."""

    def __init__(self, database: BackendDatabase) -> None:
        self._database = database

    def list_opportunities(self) -> list[MarketingOpportunityRead]:
        """List all saved marketing opportunities."""

        with self._database.transaction() as connection:
            marketing_opportunity_repository = MarketingOpportunityRepository(
                connection,
            )
            return marketing_opportunity_repository.list_opportunities()

    def get_opportunity(self, opportunity_id: int) -> MarketingOpportunityRead:
        """Get one marketing opportunity."""

        with self._database.transaction() as connection:
            marketing_opportunity_repository = MarketingOpportunityRepository(
                connection,
            )
            return marketing_opportunity_repository.get_opportunity(opportunity_id)

    def create_opportunity(
        self,
        *,
        title: str,
        opportunity_type: str | None = None,
        region: str | None = None,
        source: str | None = None,
        publish_time: str | None = None,
        deadline: str | None = None,
        credibility: float | None = None,
        contact: str | None = None,
        budget: float | None = None,
        purchase_amount: float | None = None,
        link_status: str | None = None,
        reason: str | None = None,
        original_link: str | None = None,
        level: str | None = None,
        summary: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> MarketingOpportunityRead:
        """Create one marketing opportunity."""

        create_payload = MarketingOpportunityCreate(
            title=title,
            opportunity_type=opportunity_type,
            region=region,
            source=source,
            publish_time=publish_time,
            deadline=deadline,
            credibility=credibility,
            contact=contact,
            budget=budget,
            purchase_amount=purchase_amount,
            link_status=link_status,
            reason=reason,
            original_link=original_link,
            level=level,
            summary=summary,
            session_id=session_id,
            agent_id=agent_id,
        )
        with self._database.transaction() as connection:
            marketing_opportunity_repository = MarketingOpportunityRepository(
                connection,
            )
            return marketing_opportunity_repository.create_opportunity(
                create_payload,
            )

    def update_opportunity(
        self,
        opportunity_id: int,
        *,
        title: str | None = None,
        opportunity_type: str | None = None,
        region: str | None = None,
        source: str | None = None,
        publish_time: str | None = None,
        deadline: str | None = None,
        credibility: float | None = None,
        contact: str | None = None,
        budget: float | None = None,
        purchase_amount: float | None = None,
        link_status: str | None = None,
        reason: str | None = None,
        original_link: str | None = None,
        level: str | None = None,
        summary: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> MarketingOpportunityRead:
        """Update one marketing opportunity."""

        update_payload = MarketingOpportunityUpdate(
            title=title,
            opportunity_type=opportunity_type,
            region=region,
            source=source,
            publish_time=publish_time,
            deadline=deadline,
            credibility=credibility,
            contact=contact,
            budget=budget,
            purchase_amount=purchase_amount,
            link_status=link_status,
            reason=reason,
            original_link=original_link,
            level=level,
            summary=summary,
            session_id=session_id,
            agent_id=agent_id,
        )
        with self._database.transaction() as connection:
            marketing_opportunity_repository = MarketingOpportunityRepository(
                connection,
            )
            return marketing_opportunity_repository.update_opportunity(
                opportunity_id,
                update_payload,
            )

    def delete_opportunity(self, opportunity_id: int) -> bool:
        """Delete one marketing opportunity."""

        with self._database.transaction() as connection:
            marketing_opportunity_repository = MarketingOpportunityRepository(
                connection,
            )
            return marketing_opportunity_repository.delete_opportunity(
                opportunity_id,
            )
