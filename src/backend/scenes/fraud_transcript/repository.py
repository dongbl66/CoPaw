# -*- coding: utf-8 -*-
"""Repository for fraud transcript result persistence."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3
from typing import Any

from .exceptions import FraudTranscriptResultNotFoundError
from .schemas.result import (
    FraudTranscriptResultCreate,
    FraudTranscriptResultRead,
    FraudTranscriptResultUpdate,
)


class FraudTranscriptResultRepository:
    """Persist and load fraud transcript result records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_results(self) -> list[FraudTranscriptResultRead]:
        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                basic_info_json,
                product_info_json,
                qa_records_json,
                structured_result_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM fraud_transcript_results
            ORDER BY id DESC
            """,
        )
        return [self._row_to_read_model(row) for row in cursor.fetchall()]

    def list_saved_results(self) -> list[FraudTranscriptResultRead]:
        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                basic_info_json,
                product_info_json,
                qa_records_json,
                structured_result_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM fraud_transcript_results
            WHERE save_status = 'saved'
            ORDER BY id DESC
            """,
        )
        return [self._row_to_read_model(row) for row in cursor.fetchall()]

    def get_result(self, result_id: int) -> FraudTranscriptResultRead:
        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                basic_info_json,
                product_info_json,
                qa_records_json,
                structured_result_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM fraud_transcript_results
            WHERE id = ?
            """,
            (result_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise FraudTranscriptResultNotFoundError(
                f"Fraud transcript result {result_id} was not found.",
            )
        return self._row_to_read_model(row)

    def get_latest_result_by_session(
        self,
        session_id: str,
    ) -> FraudTranscriptResultRead | None:
        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                basic_info_json,
                product_info_json,
                qa_records_json,
                structured_result_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM fraud_transcript_results
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        return self._row_to_read_model(row) if row is not None else None

    def create_result(
        self,
        payload: FraudTranscriptResultCreate,
    ) -> FraudTranscriptResultRead:
        now = datetime.utcnow().isoformat()
        cursor = self._connection.execute(
            """
            INSERT INTO fraud_transcript_results (
                title,
                result_type,
                save_status,
                scene,
                summary,
                basic_info_json,
                product_info_json,
                qa_records_json,
                structured_result_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.result_type,
                payload.save_status,
                payload.scene,
                payload.summary,
                json.dumps(payload.basic_info, ensure_ascii=False),
                json.dumps(payload.product_info, ensure_ascii=False),
                json.dumps(payload.qa_records, ensure_ascii=False),
                json.dumps(payload.structured_result, ensure_ascii=False),
                payload.session_id,
                payload.agent_id,
                now,
                now,
            ),
        )
        return self.get_result(int(cursor.lastrowid))

    def update_result(
        self,
        result_id: int,
        payload: FraudTranscriptResultUpdate,
    ) -> FraudTranscriptResultRead:
        current = self.get_result(result_id)
        self._connection.execute(
            """
            UPDATE fraud_transcript_results
            SET
                title = ?,
                result_type = ?,
                save_status = ?,
                scene = ?,
                summary = ?,
                basic_info_json = ?,
                product_info_json = ?,
                qa_records_json = ?,
                structured_result_json = ?,
                session_id = ?,
                agent_id = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                payload.title if payload.title is not None else current.title,
                (
                    payload.result_type
                    if payload.result_type is not None
                    else current.result_type
                ),
                (
                    payload.save_status
                    if payload.save_status is not None
                    else current.save_status
                ),
                payload.scene if payload.scene is not None else current.scene,
                payload.summary if payload.summary is not None else current.summary,
                json.dumps(
                    payload.basic_info
                    if payload.basic_info is not None
                    else current.basic_info,
                    ensure_ascii=False,
                ),
                json.dumps(
                    payload.product_info
                    if payload.product_info is not None
                    else current.product_info,
                    ensure_ascii=False,
                ),
                json.dumps(
                    payload.qa_records
                    if payload.qa_records is not None
                    else current.qa_records,
                    ensure_ascii=False,
                ),
                json.dumps(
                    payload.structured_result
                    if payload.structured_result is not None
                    else current.structured_result,
                    ensure_ascii=False,
                ),
                payload.session_id
                if payload.session_id is not None
                else current.session_id,
                payload.agent_id if payload.agent_id is not None else current.agent_id,
                datetime.utcnow().isoformat(),
                result_id,
            ),
        )
        return self.get_result(result_id)

    def mark_result_as_saved(self, result_id: int) -> FraudTranscriptResultRead:
        return self.update_result(
            result_id,
            FraudTranscriptResultUpdate(save_status="saved"),
        )

    @staticmethod
    def _json_dict(value: str) -> dict[str, Any]:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _json_list(value: str) -> list[dict[str, Any]]:
        parsed = json.loads(value)
        return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []

    @classmethod
    def _row_to_read_model(cls, row: sqlite3.Row) -> FraudTranscriptResultRead:
        return FraudTranscriptResultRead(
            id=int(row["id"]),
            title=str(row["title"]),
            result_type=str(row["result_type"]),
            save_status=str(row["save_status"] or "draft"),
            scene=row["scene"],
            summary=row["summary"],
            basic_info=cls._json_dict(row["basic_info_json"]),
            product_info=cls._json_dict(row["product_info_json"]),
            qa_records=cls._json_list(row["qa_records_json"]),
            structured_result=cls._json_dict(row["structured_result_json"]),
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

