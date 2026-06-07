# -*- coding: utf-8 -*-
"""Service layer for fraud transcript result CRUD."""

from __future__ import annotations

from backend.database.connection import BackendDatabase

from .repository import FraudTranscriptResultRepository
from .schemas.result import (
    FraudTranscriptResultCreate,
    FraudTranscriptResultRead,
    FraudTranscriptResultUpdate,
)


class FraudTranscriptResultService:
    """Orchestrate fraud transcript result CRUD operations."""

    def __init__(self, database: BackendDatabase) -> None:
        self._database = database

    def list_results(self) -> list[FraudTranscriptResultRead]:
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(connection).list_results()

    def list_saved_results(self) -> list[FraudTranscriptResultRead]:
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(connection).list_saved_results()

    def get_result(self, result_id: int) -> FraudTranscriptResultRead:
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(connection).get_result(result_id)

    def get_latest_result_by_session(
        self,
        session_id: str,
    ) -> FraudTranscriptResultRead | None:
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(
                connection,
            ).get_latest_result_by_session(session_id)

    def create_result(
        self,
        *,
        title: str,
        result_type: str,
        save_status: str = "draft",
        scene: str | None = "fraud_transcript_report",
        summary: str | None = None,
        basic_info: dict | None = None,
        product_info: dict | None = None,
        qa_records: list[dict] | None = None,
        structured_result: dict | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> FraudTranscriptResultRead:
        payload = FraudTranscriptResultCreate(
            title=title,
            result_type=result_type,
            save_status=save_status,
            scene=scene,
            summary=summary,
            basic_info=basic_info or {},
            product_info=product_info or {},
            qa_records=qa_records or [],
            structured_result=structured_result or {},
            session_id=session_id,
            agent_id=agent_id,
        )
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(connection).create_result(payload)

    def mark_result_as_saved(self, result_id: int) -> FraudTranscriptResultRead:
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(connection).mark_result_as_saved(
                result_id,
            )

    def update_result(
        self,
        result_id: int,
        *,
        title: str | None = None,
        result_type: str | None = None,
        save_status: str | None = None,
        scene: str | None = None,
        summary: str | None = None,
        basic_info: dict | None = None,
        product_info: dict | None = None,
        qa_records: list[dict] | None = None,
        structured_result: dict | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> FraudTranscriptResultRead:
        payload = FraudTranscriptResultUpdate(
            title=title,
            result_type=result_type,
            save_status=save_status,
            scene=scene,
            summary=summary,
            basic_info=basic_info,
            product_info=product_info,
            qa_records=qa_records,
            structured_result=structured_result,
            session_id=session_id,
            agent_id=agent_id,
        )
        with self._database.transaction() as connection:
            return FraudTranscriptResultRepository(connection).update_result(
                result_id,
                payload,
            )

