# -*- coding: utf-8 -*-
"""Repository for marketing result persistence."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from .exceptions import (
    MarketingOpportunityNotFoundError,
    MarketingResultNotFoundError,
)
from .schemas.opportunity import (
    MarketingOpportunityCreate,
    MarketingOpportunityRead,
    MarketingOpportunityUpdate,
)
from .schemas.result import (
    MarketingResultCreate,
    MarketingResultFileCreate,
    MarketingResultFileRead,
    MarketingResultRead,
    MarketingResultUpdate,
)


class MarketingResultRepository:
    """Persist and load marketing result records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_results(self) -> list[MarketingResultRead]:
        """Return all marketing results ordered by newest first."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                detail_content_json,
                info_json,
                basic_info_json,
                product_info_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM marketing_product_results
            ORDER BY id DESC
            """,
        )
        rows = cursor.fetchall()
        items: list[MarketingResultRead] = []
        for row in rows:
            result = self._row_to_read_model(row)
            result.attachments = self._load_attachments(result.id)
            items.append(result)
        return items

    def get_result(self, result_id: int) -> MarketingResultRead:
        """Return one marketing result by ID."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                detail_content_json,
                info_json,
                basic_info_json,
                product_info_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM marketing_product_results
            WHERE id = ?
            """,
            (result_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise MarketingResultNotFoundError(
                f"Marketing result {result_id} was not found.",
            )
        result = self._row_to_read_model(row)
        result.attachments = self._load_attachments(result.id)
        return result

    def get_latest_result_by_session(
        self,
        session_id: str,
    ) -> MarketingResultRead | None:
        """Return the newest marketing result under one session."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                detail_content_json,
                info_json,
                basic_info_json,
                product_info_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM marketing_product_results
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        result = self._row_to_read_model(row)
        result.attachments = self._load_attachments(result.id)
        return result

    def create_result(
        self,
        payload: MarketingResultCreate,
    ) -> MarketingResultRead:
        """Create one marketing result."""

        now = datetime.utcnow().isoformat()
        cursor = self._connection.execute(
            """
            INSERT INTO marketing_product_results (
                title,
                result_type,
                save_status,
                scene,
                summary,
                detail_content_json,
                info_json,
                basic_info_json,
                product_info_json,
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
                json.dumps(payload.detail_content, ensure_ascii=False),
                json.dumps(payload.info, ensure_ascii=False),
                json.dumps(payload.basic_info, ensure_ascii=False),
                json.dumps(payload.product_info, ensure_ascii=False),
                payload.session_id,
                payload.agent_id,
                now,
                now,
            ),
        )
        result_id = int(cursor.lastrowid)
        self._replace_attachments(result_id, payload.attachments, now)
        return self.get_result(result_id)

    def update_result(
        self,
        result_id: int,
        payload: MarketingResultUpdate,
    ) -> MarketingResultRead:
        """Update a marketing result."""

        current = self.get_result(result_id)
        updated_title = payload.title if payload.title is not None else current.title
        updated_result_type = (
            payload.result_type
            if payload.result_type is not None
            else current.result_type
        )
        updated_save_status = (
            payload.save_status
            if payload.save_status is not None
            else current.save_status
        )
        updated_scene = payload.scene if payload.scene is not None else current.scene
        updated_summary = (
            payload.summary if payload.summary is not None else current.summary
        )
        updated_detail_content = (
            payload.detail_content
            if payload.detail_content is not None
            else current.detail_content
        )
        updated_info = (
            payload.info if payload.info is not None else current.info
        )
        updated_basic_info = (
            payload.basic_info
            if payload.basic_info is not None
            else current.basic_info
        )
        updated_product_info = (
            payload.product_info
            if payload.product_info is not None
            else current.product_info
        )
        updated_session_id = (
            payload.session_id
            if payload.session_id is not None
            else current.session_id
        )
        updated_agent_id = (
            payload.agent_id if payload.agent_id is not None else current.agent_id
        )

        self._connection.execute(
            """
            UPDATE marketing_product_results
            SET
                title = ?,
                result_type = ?,
                save_status = ?,
                scene = ?,
                summary = ?,
                detail_content_json = ?,
                info_json = ?,
                basic_info_json = ?,
                product_info_json = ?,
                session_id = ?,
                agent_id = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                updated_title,
                updated_result_type,
                updated_save_status,
                updated_scene,
                updated_summary,
                json.dumps(updated_detail_content, ensure_ascii=False),
                json.dumps(updated_info, ensure_ascii=False),
                json.dumps(updated_basic_info, ensure_ascii=False),
                json.dumps(updated_product_info, ensure_ascii=False),
                updated_session_id,
                updated_agent_id,
                datetime.utcnow().isoformat(),
                result_id,
            ),
        )
        if payload.attachments is not None:
            self._replace_attachments(
                result_id,
                payload.attachments,
                datetime.utcnow().isoformat(),
            )
        return self.get_result(result_id)

    def list_saved_results(self) -> list[MarketingResultRead]:
        """Return manually saved marketing results ordered by newest first."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                result_type,
                save_status,
                scene,
                summary,
                detail_content_json,
                info_json,
                basic_info_json,
                product_info_json,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM marketing_product_results
            WHERE save_status = 'saved'
            ORDER BY id DESC
            """,
        )
        rows = cursor.fetchall()
        items: list[MarketingResultRead] = []
        for row in rows:
            result = self._row_to_read_model(row)
            result.attachments = self._load_attachments(result.id)
            items.append(result)
        return items

    def mark_result_as_saved(self, result_id: int) -> MarketingResultRead:
        """Mark one marketing result as manually saved."""

        return self.update_result(
            result_id,
            MarketingResultUpdate(save_status="saved"),
        )

    def delete_result(self, result_id: int) -> bool:
        """Delete a marketing result by ID."""

        cursor = self._connection.execute(
            "DELETE FROM marketing_product_results WHERE id = ?",
            (result_id,),
        )
        if cursor.rowcount == 0:
            raise MarketingResultNotFoundError(
                f"Marketing result {result_id} was not found.",
            )
        return True

    @staticmethod
    def _row_to_read_model(row: sqlite3.Row) -> MarketingResultRead:
        """Convert a SQLite row into a read DTO."""

        detail_content = json.loads(row["detail_content_json"])
        info = json.loads(row["info_json"])
        basic_info = json.loads(row["basic_info_json"])
        product_info = json.loads(row["product_info_json"])
        return MarketingResultRead(
            id=int(row["id"]),
            title=str(row["title"]),
            result_type=str(row["result_type"]),
            save_status=str(row["save_status"] or "draft"),
            scene=row["scene"],
            summary=row["summary"],
            detail_content=detail_content if isinstance(detail_content, list) else [],
            info=info if isinstance(info, dict) else {},
            basic_info=basic_info if isinstance(basic_info, dict) else {},
            product_info=product_info if isinstance(product_info, dict) else {},
            attachments=[],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    def _replace_attachments(
        self,
        result_id: int,
        attachments: list[MarketingResultFileCreate],
        now: str,
    ) -> None:
        """Replace all attachments under one product result."""

        self._connection.execute(
            "DELETE FROM marketing_result_files WHERE result_id = ?",
            (result_id,),
        )
        for attachment in attachments:
            self._connection.execute(
                """
                INSERT INTO marketing_result_files (
                    result_id,
                    file_name,
                    file_type,
                    mime_type,
                    file_url,
                    preview_url,
                    download_url,
                    file_path,
                    file_id,
                    file_size,
                    page_index,
                    sort_order,
                    source_type,
                    extra_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    attachment.file_name,
                    attachment.file_type,
                    attachment.mime_type,
                    attachment.file_url,
                    attachment.preview_url,
                    attachment.download_url,
                    attachment.file_path,
                    attachment.file_id,
                    attachment.file_size,
                    attachment.page_index,
                    attachment.sort_order,
                    attachment.source_type,
                    json.dumps(attachment.extra, ensure_ascii=False),
                    now,
                    now,
                ),
            )

    def _load_attachments(self, result_id: int) -> list[MarketingResultFileRead]:
        """Load attachments under one product result."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                result_id,
                file_name,
                file_type,
                mime_type,
                file_url,
                preview_url,
                download_url,
                file_path,
                file_id,
                file_size,
                page_index,
                sort_order,
                source_type,
                extra_json,
                created_at,
                updated_at
            FROM marketing_result_files
            WHERE result_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (result_id,),
        )
        attachments: list[MarketingResultFileRead] = []
        for row in cursor.fetchall():
            extra = json.loads(row["extra_json"])
            attachments.append(
                MarketingResultFileRead(
                    id=int(row["id"]),
                    result_id=int(row["result_id"]),
                    file_name=str(row["file_name"]),
                    file_type=str(row["file_type"]),
                    mime_type=row["mime_type"],
                    file_url=row["file_url"],
                    preview_url=row["preview_url"],
                    download_url=row["download_url"],
                    file_path=row["file_path"],
                    file_id=row["file_id"],
                    file_size=row["file_size"],
                    page_index=row["page_index"],
                    sort_order=int(row["sort_order"]),
                    source_type=row["source_type"],
                    extra=extra if isinstance(extra, dict) else {},
                    created_at=datetime.fromisoformat(str(row["created_at"])),
                    updated_at=datetime.fromisoformat(str(row["updated_at"])),
                ),
            )
        return attachments


class MarketingOpportunityRepository:
    """Persist and load marketing opportunity records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_opportunities(self) -> list[MarketingOpportunityRead]:
        """Return all opportunities ordered by newest first."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                opportunity_type,
                region,
                source,
                publish_time,
                deadline,
                credibility,
                contact,
                budget,
                purchase_amount,
                link_status,
                reason,
                original_link,
                level,
                summary,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM marketing_opportunities
            ORDER BY id DESC
            """,
        )
        return [self._row_to_opportunity_model(row) for row in cursor.fetchall()]

    def get_opportunity(self, opportunity_id: int) -> MarketingOpportunityRead:
        """Return one opportunity by ID."""

        cursor = self._connection.execute(
            """
            SELECT
                id,
                title,
                opportunity_type,
                region,
                source,
                publish_time,
                deadline,
                credibility,
                contact,
                budget,
                purchase_amount,
                link_status,
                reason,
                original_link,
                level,
                summary,
                session_id,
                agent_id,
                created_at,
                updated_at
            FROM marketing_opportunities
            WHERE id = ?
            """,
            (opportunity_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise MarketingOpportunityNotFoundError(
                f"Marketing opportunity {opportunity_id} was not found.",
            )
        return self._row_to_opportunity_model(row)

    def create_opportunity(
        self,
        payload: MarketingOpportunityCreate,
    ) -> MarketingOpportunityRead:
        """Create one opportunity."""

        now = datetime.utcnow().isoformat()
        cursor = self._connection.execute(
            """
            INSERT INTO marketing_opportunities (
                title,
                opportunity_type,
                region,
                source,
                publish_time,
                deadline,
                credibility,
                contact,
                budget,
                purchase_amount,
                link_status,
                reason,
                original_link,
                level,
                summary,
                session_id,
                agent_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.opportunity_type,
                payload.region,
                payload.source,
                payload.publish_time,
                payload.deadline,
                payload.credibility,
                payload.contact,
                payload.budget,
                payload.purchase_amount,
                payload.link_status,
                payload.reason,
                payload.original_link,
                payload.level,
                payload.summary,
                payload.session_id,
                payload.agent_id,
                now,
                now,
            ),
        )
        return self.get_opportunity(int(cursor.lastrowid))

    def update_opportunity(
        self,
        opportunity_id: int,
        payload: MarketingOpportunityUpdate,
    ) -> MarketingOpportunityRead:
        """Update one opportunity."""

        current = self.get_opportunity(opportunity_id)
        self._connection.execute(
            """
            UPDATE marketing_opportunities
            SET
                title = ?,
                opportunity_type = ?,
                region = ?,
                source = ?,
                publish_time = ?,
                deadline = ?,
                credibility = ?,
                contact = ?,
                budget = ?,
                purchase_amount = ?,
                link_status = ?,
                reason = ?,
                original_link = ?,
                level = ?,
                summary = ?,
                session_id = ?,
                agent_id = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                payload.title if payload.title is not None else current.title,
                (
                    payload.opportunity_type
                    if payload.opportunity_type is not None
                    else current.opportunity_type
                ),
                payload.region if payload.region is not None else current.region,
                payload.source if payload.source is not None else current.source,
                (
                    payload.publish_time
                    if payload.publish_time is not None
                    else current.publish_time
                ),
                payload.deadline if payload.deadline is not None else current.deadline,
                (
                    payload.credibility
                    if payload.credibility is not None
                    else current.credibility
                ),
                payload.contact if payload.contact is not None else current.contact,
                payload.budget if payload.budget is not None else current.budget,
                (
                    payload.purchase_amount
                    if payload.purchase_amount is not None
                    else current.purchase_amount
                ),
                (
                    payload.link_status
                    if payload.link_status is not None
                    else current.link_status
                ),
                payload.reason if payload.reason is not None else current.reason,
                (
                    payload.original_link
                    if payload.original_link is not None
                    else current.original_link
                ),
                payload.level if payload.level is not None else current.level,
                payload.summary if payload.summary is not None else current.summary,
                (
                    payload.session_id
                    if payload.session_id is not None
                    else current.session_id
                ),
                payload.agent_id if payload.agent_id is not None else current.agent_id,
                datetime.utcnow().isoformat(),
                opportunity_id,
            ),
        )
        return self.get_opportunity(opportunity_id)

    def delete_opportunity(self, opportunity_id: int) -> bool:
        """Delete one opportunity by ID."""

        cursor = self._connection.execute(
            "DELETE FROM marketing_opportunities WHERE id = ?",
            (opportunity_id,),
        )
        if cursor.rowcount == 0:
            raise MarketingOpportunityNotFoundError(
                f"Marketing opportunity {opportunity_id} was not found.",
            )
        return True

    @staticmethod
    def _row_to_opportunity_model(
        row: sqlite3.Row,
    ) -> MarketingOpportunityRead:
        """Convert one row into an opportunity DTO."""

        return MarketingOpportunityRead(
            id=int(row["id"]),
            title=str(row["title"]),
            opportunity_type=row["opportunity_type"],
            region=row["region"],
            source=row["source"],
            publish_time=row["publish_time"],
            deadline=row["deadline"],
            credibility=row["credibility"],
            contact=row["contact"],
            budget=row["budget"],
            purchase_amount=row["purchase_amount"],
            link_status=row["link_status"],
            reason=row["reason"],
            original_link=row["original_link"],
            level=row["level"],
            summary=row["summary"],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
