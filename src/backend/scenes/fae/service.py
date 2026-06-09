# -*- coding: utf-8 -*-
"""Service layer for FAE government opportunities and results."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from backend.database.connection import BackendDatabase, get_backend_database
from backend.scenes.common.display_assets import normalize_display_content

from .exceptions import FAEGovernmentOpportunityNotFoundError, FAEResultNotFoundError

logger = logging.getLogger(__name__)


class FAEOpportunityService:
    """CRUD operations for government opportunity table."""

    def __init__(self, database: BackendDatabase | None = None) -> None:
        self._db = database or get_backend_database()

    def list_opportunities(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        """List government opportunities, optionally filtered by session."""
        query = """
            SELECT
                id, project_name, customer_name, city, industry,
                support_type, requirement_desc, opportunity_rating,
                opportunity_score, budget_min_yuan, budget_max_yuan,
                budget_note, display_content_json,
                session_id, agent_id, created_at, updated_at
            FROM fae_government_opportunities
        """
        params: tuple[Any, ...] = ()
        if session_id:
            query += " WHERE session_id = ?"
            params = (session_id,)
        query += " ORDER BY id DESC"

        with self._db.transaction() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_opportunity(self, opportunity_id: int) -> dict[str, Any]:
        """Get one opportunity by ID."""
        with self._db.transaction() as conn:
            row = conn.execute(
                """
                SELECT
                    id, project_name, customer_name, city, industry,
                    support_type, requirement_desc, opportunity_rating,
                    opportunity_score, budget_min_yuan, budget_max_yuan,
                    budget_note, display_content_json,
                    session_id, agent_id, created_at, updated_at
                FROM fae_government_opportunities
                WHERE id = ?
                """,
                (opportunity_id,),
            ).fetchone()
        if row is None:
            raise FAEGovernmentOpportunityNotFoundError(
                f"Government opportunity {opportunity_id} not found.",
            )
        return self._row_to_dict(row)

    def create_opportunity(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create one opportunity from LLM output."""
        now = datetime.utcnow().isoformat()
        budget = payload.get("budget") or {}
        if isinstance(budget, dict):
            budget_min = budget.get("min_yuan") or budget.get("minYuan")
            budget_max = budget.get("max_yuan") or budget.get("maxYuan")
            budget_note = budget.get("note")
        else:
            budget_min = None
            budget_max = None
            budget_note = None

        display_content = payload.get("display_content", [])
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO fae_government_opportunities (
                    project_name, customer_name, city, industry, support_type,
                    requirement_desc, opportunity_rating, opportunity_score,
                    budget_min_yuan, budget_max_yuan, budget_note,
                    display_content_json, session_id, agent_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.get("project_name", ""),
                    payload.get("customer_name", ""),
                    payload.get("city", ""),
                    payload.get("industry", ""),
                    payload.get("support_type", ""),
                    payload.get("requirement_desc", ""),
                    payload.get("opportunity_rating", ""),
                    payload.get("opportunity_score"),
                    budget_min,
                    budget_max,
                    budget_note,
                    json.dumps(display_content, ensure_ascii=False) if display_content else "[]",
                    payload.get("session_id"),
                    payload.get("agent_id") or "RA-agent",
                    now,
                    now,
                ),
            )
            opportunity_id = int(cursor.lastrowid)
        return self.get_opportunity(opportunity_id)

    def update_opportunity(
        self, opportunity_id: int, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update one opportunity."""
        current = self.get_opportunity(opportunity_id)
        set_clauses: list[str] = []
        values: list[Any] = []

        for key in (
            "project_name", "customer_name", "city", "industry",
            "support_type", "requirement_desc", "opportunity_rating",
            "opportunity_score", "budget_min_yuan", "budget_max_yuan",
            "budget_note",
        ):
            if key in updates and updates[key] is not None:
                set_clauses.append(f"{key} = ?")
                values.append(updates[key])

        if "display_content" in updates:
            set_clauses.append("display_content_json = ?")
            values.append(
                json.dumps(updates["display_content"], ensure_ascii=False)
            )

        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(opportunity_id)

        with self._db.transaction() as conn:
            conn.execute(
                f"UPDATE fae_government_opportunities SET {', '.join(set_clauses)} WHERE id = ?",
                values,
            )
        return self.get_opportunity(opportunity_id)

    def delete_opportunity(self, opportunity_id: int) -> None:
        """Delete one opportunity."""
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM fae_government_opportunities WHERE id = ?",
                (opportunity_id,),
            )
        if cursor.rowcount == 0:
            raise FAEGovernmentOpportunityNotFoundError(
                f"Government opportunity {opportunity_id} not found.",
            )

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert a SQLite row to a dict matching the API read model."""
        display_content = normalize_display_content(
            json.loads(row["display_content_json"] or "[]"),
            biz_module="fae",
            record_id=int(row["id"]),
            agent_id=row["agent_id"],
            collection="opportunities",
        )

        return {
            "id": int(row["id"]),
            "project_name": str(row["project_name"]),
            "customer_name": str(row["customer_name"]),
            "city": str(row["city"]),
            "industry": str(row["industry"]),
            "support_type": str(row["support_type"]),
            "requirement_desc": str(row["requirement_desc"] or ""),
            "opportunity_rating": str(row["opportunity_rating"]),
            "opportunity_score": row["opportunity_score"],
            "budget_min_yuan": row["budget_min_yuan"],
            "budget_max_yuan": row["budget_max_yuan"],
            "budget_note": row["budget_note"],
            "display_content": display_content,
            "session_id": row["session_id"],
            "agent_id": row["agent_id"],
            "create_time": str(row["created_at"]),
            "update_time": str(row["updated_at"]),
        }


class FAEResultService:
    """CRUD operations for FAE result table."""

    def __init__(self, database: BackendDatabase | None = None) -> None:
        self._db = database or get_backend_database()

    def list_results(self, *, saved_only: bool = False) -> list[dict[str, Any]]:
        """List FAE results ordered by newest first."""
        query = """
            SELECT
                id, title, result_type, save_status, scene,
                summary, detail_content_json, info_json,
                basic_info_json, session_id, agent_id,
                created_at, updated_at
            FROM fae_results
        """
        if saved_only:
            query += " WHERE save_status = 'saved'"
        query += " ORDER BY id DESC"

        with self._db.transaction() as conn:
            rows = conn.execute(query).fetchall()
        return [self._row_to_result_dict(r) for r in rows]

    def get_latest_result_by_session(self, session_id: str) -> dict[str, Any] | None:
        """Get latest FAE result for a session."""
        with self._db.transaction() as conn:
            row = conn.execute(
                """
                SELECT
                    id, title, result_type, save_status, scene,
                    summary, detail_content_json, info_json,
                    basic_info_json, session_id, agent_id,
                    created_at, updated_at
                FROM fae_results
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_result_dict(row)

    def mark_result_as_saved(self, result_id: int) -> dict[str, Any]:
        """Mark a result as saved."""
        with self._db.transaction() as conn:
            conn.execute(
                "UPDATE fae_results SET save_status = 'saved', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), result_id),
            )
        return self.get_result(result_id)

    def get_result(self, result_id: int) -> dict[str, Any]:
        """Get one result by ID."""
        with self._db.transaction() as conn:
            row = conn.execute(
                """
                SELECT
                    id, title, result_type, save_status, scene,
                    summary, detail_content_json, info_json,
                    basic_info_json, session_id, agent_id,
                    created_at, updated_at
                FROM fae_results
                WHERE id = ?
                """,
                (result_id,),
            ).fetchone()
        if row is None:
            raise FAEResultNotFoundError(f"FAE result {result_id} not found.")
        return self._row_to_result_dict(row)

    def create_result(
        self,
        title: str,
        result_type: str,
        *,
        save_status: str = "draft",
        scene: str | None = None,
        summary: str | None = None,
        detail_content: list[dict[str, Any]] | None = None,
        info: dict[str, Any] | None = None,
        basic_info: dict[str, Any] | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Create one FAE result."""
        now = datetime.utcnow().isoformat()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO fae_results (
                    title, result_type, save_status, scene, summary,
                    detail_content_json, info_json, basic_info_json,
                    session_id, agent_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    result_type,
                    save_status,
                    scene,
                    summary,
                    json.dumps(detail_content or [], ensure_ascii=False),
                    json.dumps(info or {}, ensure_ascii=False),
                    json.dumps(basic_info or {}, ensure_ascii=False),
                    session_id,
                    agent_id,
                    now,
                    now,
                ),
            )
            result_id = int(cursor.lastrowid)
        return self.get_result(result_id)

    @staticmethod
    def _row_to_result_dict(row) -> dict[str, Any]:
        """Convert a SQLite row to a result dict."""
        detail_content = normalize_display_content(
            json.loads(row["detail_content_json"] or "[]"),
            biz_module="fae",
            record_id=int(row["id"]),
            agent_id=row["agent_id"],
        )
        info = json.loads(row["info_json"] or "{}")
        if isinstance(info, dict):
            structured_result = info.get("structuredResult")
            if isinstance(structured_result, dict):
                result = structured_result.get("result")
                if isinstance(result, dict):
                    payload = result.get("payload")
                    if isinstance(payload, dict):
                        payload["display_content"] = detail_content

            payload = info.get("payload")
            if isinstance(payload, dict):
                payload["display_content"] = detail_content

        basic_info = json.loads(row["basic_info_json"] or "{}")
        if isinstance(basic_info, dict):
            basic_info["display_content"] = detail_content

        return {
            "id": int(row["id"]),
            "title": str(row["title"]),
            "result_type": str(row["result_type"]),
            "save_status": str(row["save_status"] or "draft"),
            "scene": row["scene"],
            "summary": row["summary"],
            "info": info,
            "basic_info": basic_info,
            "detail_content": detail_content,
            "display_content": detail_content,
            "attachments": detail_content,
            "session_id": row["session_id"],
            "agent_id": row["agent_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
