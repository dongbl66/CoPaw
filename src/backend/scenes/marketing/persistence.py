# -*- coding: utf-8 -*-
"""Automatic persistence for marketing structured results."""

from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg

from backend.database.connection import BackendDatabase, get_backend_database

from .service import MarketingOpportunityService, MarketingResultService

logger = logging.getLogger(__name__)


class MarketingStructuredResultPersistence:
    """Persist structured result messages into marketing_results."""

    def __init__(self, database: BackendDatabase | None = None) -> None:
        backend_database = database or get_backend_database()
        self._marketing_result_service = MarketingResultService(backend_database)
        self._marketing_opportunity_service = MarketingOpportunityService(
            backend_database,
        )

    def persist_message(
        self,
        msg: Msg,
        *,
        session_id: str | None,
        agent_id: str | None,
    ) -> None:
        """Persist a message when it contains a structured_result payload."""

        metadata = msg.metadata if isinstance(msg.metadata, dict) else {}
        structured_result = metadata.get("structured_result")
        if not isinstance(structured_result, dict):
            logger.info(
                "[persistence] persist_message: no structured_result in metadata, skip"
            )
            return

        business_result = metadata.get("business_result")
        if not isinstance(business_result, dict):
            business_result = {}
            logger.info(
                "[persistence] persist_message: no business_result in metadata, "
                "using empty dict"
            )

        result = structured_result.get("result")
        if not isinstance(result, dict):
            logger.info(
                "[persistence] persist_message: structured_result.result is not dict, skip"
            )
            return

        result_type = result.get("type")
        payload = result.get("payload")
        if not isinstance(result_type, str) or not isinstance(payload, dict):
            logger.info(
                "[persistence] persist_message: result_type=%s payload_type=%s, skip",
                result_type,
                type(payload).__name__ if payload is not None else None,
            )
            return

        title = structured_result.get("title")
        if not isinstance(title, str) or not title.strip():
            title = "分析结果"

        logger.info(
            "[persistence] persist_message: creating result, title=%s type=%s "
            "session_id=%s agent_id=%s",
            title.strip(),
            result_type,
            session_id,
            agent_id,
        )
        self._marketing_result_service.create_result(
            title=title.strip(),
            result_type=result_type,
            scene=self._resolve_scene(business_result),
            summary=self._resolve_summary(msg, structured_result),
            detail_content=self._resolve_detail_content(business_result),
            info=self._build_info_payload(
                msg=msg,
                structured_result=structured_result,
                payload=payload,
            ),
            basic_info=self._as_dict(business_result.get("basic_info")),
            product_info=self._as_dict(business_result.get("product_info")),
            attachments=self._build_attachments(business_result),
            session_id=session_id,
            agent_id=agent_id,
        )
        logger.info("[persistence] persist_message: marketing_result created")

        self._persist_opportunities(
            business_result=business_result,
            session_id=session_id,
            agent_id=agent_id,
        )

    @staticmethod
    def _build_info_payload(
        *,
        msg: Msg,
        structured_result: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the stored metadata payload for one structured result."""

        return {
            "messageContent": msg.content,
            "structuredResult": structured_result,
            "payload": payload,
        }

    @staticmethod
    def _resolve_scene(business_result: dict[str, Any]) -> str | None:
        """Resolve the user-facing scene field from product info."""

        product_info = business_result.get("product_info")
        if not isinstance(product_info, dict):
            return None
        for key in ("scene", "scenario", "场景"):
            value = product_info.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _resolve_summary(msg: Msg, structured_result: dict[str, Any]) -> str:
        """Resolve a concise summary string for one product result."""

        result = structured_result.get("result")
        if isinstance(result, dict):
            payload = result.get("payload")
            if isinstance(payload, dict):
                text = payload.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()
        if isinstance(msg.content, str):
            return msg.content.strip()
        return ""

    @staticmethod
    def _resolve_detail_content(
        business_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Resolve the display content list stored under one product result."""

        display_content = business_result.get("display_content")
        if isinstance(display_content, list):
            return [item for item in display_content if isinstance(item, dict)]
        return []

    @classmethod
    def _build_attachments(
        cls,
        business_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build attachment rows from display content."""

        attachments: list[dict[str, Any]] = []
        for index, item in enumerate(cls._resolve_detail_content(business_result)):
            normalized = cls._normalize_attachment(item, sort_order=index)
            if normalized is not None:
                attachments.append(normalized)
        return attachments

    @classmethod
    def _normalize_attachment(
        cls,
        item: dict[str, Any],
        *,
        sort_order: int,
    ) -> dict[str, Any] | None:
        """Normalize one display content item into attachment storage fields."""

        file_name = cls._first_text(item, "file_name", "fileName", "name", "title")
        file_type = cls._first_text(item, "type", "fileType", "file_type")
        file_url = cls._first_text(item, "fileURL", "fileUrl", "file_url", "url")
        preview_url = cls._first_text(item, "previewURL", "previewUrl", "preview_url", "preview")
        download_url = cls._first_text(item, "downloadURL", "downloadUrl", "download_url", "download")
        file_path = cls._first_text(item, "filePath", "file_path", "path")
        file_id = cls._first_text(item, "fileId", "file_id")

        if not file_name and file_path:
            file_name = file_path.rsplit("/", 1)[-1]
        if not file_type:
            for candidate in (file_name, file_path, file_url):
                if isinstance(candidate, str) and "." in candidate:
                    file_type = candidate.rsplit(".", 1)[-1].lower()
                    break
        if not file_name or not file_type:
            return None

        return {
            "file_name": file_name,
            "file_type": file_type,
            "file_url": file_url,
            "preview_url": preview_url,
            "download_url": download_url,
            "file_path": file_path,
            "file_id": file_id,
            "mime_type": cls._first_text(item, "mimeType", "mime_type"),
            "file_size": item.get("fileSize") or item.get("file_size"),
            "page_index": item.get("pageIndex") or item.get("page_index"),
            "sort_order": sort_order,
            "source_type": cls._first_text(item, "sourceType", "source_type") or "display_content",
            "extra": dict(item),
        }

    @staticmethod
    def _first_text(item: dict[str, Any], *keys: str) -> str | None:
        """Return the first non-empty string for the given keys."""

        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        """Return a dict value or an empty dict."""

        return value if isinstance(value, dict) else {}

    def _persist_opportunities(
        self,
        *,
        business_result: dict[str, Any],
        session_id: str | None,
        agent_id: str | None,
    ) -> None:
        """Persist extracted opportunities under the marketing opportunity table."""

        items = self._extract_opportunities(business_result)
        logger.info(
            "[persistence] _persist_opportunities: %d opportunity candidates extracted",
            len(items),
        )
        for item in items:
            title = self._first_text(item, "title", "name", "项目名称", "商机标题")
            if not title:
                logger.info(
                    "[persistence] _persist_opportunities: skipping item without title"
                )
                continue
            logger.info(
                "[persistence] _persist_opportunities: creating opportunity title=%s",
                title,
            )
            self._marketing_opportunity_service.create_opportunity(
                title=title,
                opportunity_type=self._first_text(
                    item,
                    "type",
                    "opportunity_type",
                    "商机类型",
                ),
                region=self._first_text(item, "region", "地区", "区域"),
                source=self._first_text(item, "source", "来源"),
                publish_time=self._first_text(
                    item,
                    "publishTime",
                    "publish_time",
                    "发布时间",
                ),
                deadline=self._first_text(item, "deadline", "截止时间", "报名截止"),
                credibility=self._first_float(
                    item,
                    "credibility",
                    "可信度",
                    "confidence",
                ),
                contact=self._first_text(item, "contact", "联系人"),
                budget=self._first_float(item, "budget", "预算"),
                purchase_amount=self._first_float(
                    item,
                    "purchaseAmount",
                    "purchase_amount",
                    "采购金额",
                ),
                link_status=self._first_text(
                    item,
                    "linkStatus",
                    "link_status",
                    "链接状态",
                ),
                reason=self._first_text(item, "reason", "推荐理由", "摘要"),
                original_link=self._first_text(
                    item,
                    "originalLink",
                    "original_link",
                    "link",
                    "url",
                    "原始链接",
                ),
                level=self._first_text(item, "level", "等级", "推荐等级"),
                summary=self._first_text(
                    item,
                    "summary",
                    "摘要",
                    "description",
                    "说明",
                ),
                session_id=session_id,
                agent_id=agent_id,
            )

    @classmethod
    def _extract_opportunities(
        cls,
        business_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract zero or more opportunities from a business result payload."""

        candidates: list[dict[str, Any]] = []
        list_keys = (
            "opportunities",
            "business_opportunities",
            "opportunity_list",
            "matched_opportunities",
            "hit_opportunities",
            "items",
        )
        for key in list_keys:
            value = business_result.get(key)
            if isinstance(value, list):
                candidates.extend(
                    item for item in value if isinstance(item, dict)
                )

        basic_info = business_result.get("basic_info")
        if isinstance(basic_info, dict):
            for key in list_keys:
                value = basic_info.get(key)
                if isinstance(value, list):
                    candidates.extend(
                        item for item in value if isinstance(item, dict)
                    )

        if candidates:
            return candidates

        flattened = cls._build_opportunity_candidate(business_result)
        return [flattened] if flattened is not None else []

    @classmethod
    def _build_opportunity_candidate(
        cls,
        business_result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Build one fallback opportunity candidate from mixed business fields."""

        basic_info = cls._as_dict(business_result.get("basic_info"))
        merged = dict(basic_info)
        merged.update(business_result)
        title = cls._first_text(
            merged,
            "title",
            "name",
            "项目名称",
            "商机标题",
        )
        if not title:
            return None
        has_opportunity_signal = any(
            cls._first_text(merged, *keys)
            for keys in (
                ("budget", "预算"),
                ("contact", "联系人"),
                ("originalLink", "original_link", "原始链接"),
                ("level", "推荐等级", "等级"),
                ("reason", "推荐理由"),
            )
        )
        return merged if has_opportunity_signal else None

    @staticmethod
    def _first_float(item: dict[str, Any], *keys: str) -> float | None:
        """Return the first numeric value for the given keys."""

        for key in keys:
            value = item.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().replace(",", "")
                if not stripped:
                    continue
                try:
                    return float(stripped)
                except ValueError:
                    continue
        return None
