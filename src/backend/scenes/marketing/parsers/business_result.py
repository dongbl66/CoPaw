# -*- coding: utf-8 -*-
"""Helpers for extracting structured business payloads from final output."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agentscope.message import Msg

logger = logging.getLogger(__name__)


class StructuredResultBuilder:
    """Build frontend-compatible structured_result payloads."""

    def build_from_business_result(
        self,
        business_result: dict[str, Any],
        output_text: str,
    ) -> dict[str, Any]:
        """Build one workbench structured result event."""

        if self._has_opportunities(business_result):
            return self._build_business_event(
                business_result=business_result,
                output_text=output_text,
            )

        return self._build_product_event(
            business_result=business_result,
            output_text=output_text,
        )

    def _build_business_event(
        self,
        *,
        business_result: dict[str, Any],
        output_text: str,
    ) -> dict[str, Any]:
        """Build a business workbench result event."""

        return {
            "eventType": "structured_result",
            "version": "1.0",
            "title": self._resolve_title(business_result),
            "subtitle": self._resolve_scene(business_result),
            "result": {
                "type": "business",
                "payload": {
                    "title": self._resolve_title(business_result),
                    "summary": output_text,
                    "scene": self._resolve_scene(business_result),
                    "basicInfo": self._as_dict(business_result.get("basic_info")),
                    "productInfo": self._as_dict(
                        business_result.get("product_info"),
                    ),
                    "opportunities": self._extract_opportunities(business_result),
                    "attachments": self._build_attachments(business_result),
                },
            },
            "layout": {
                "autoOpen": True,
                "replace": True,
            },
            "meta": {
                "bizModule": "marketing",
                "source": "agent_output",
            },
        }

    def _build_product_event(
        self,
        *,
        business_result: dict[str, Any],
        output_text: str,
    ) -> dict[str, Any]:
        """Build a product workbench result event."""

        return {
            "eventType": "structured_result",
            "version": "1.0",
            "title": self._resolve_title(business_result),
            "subtitle": self._resolve_scene(business_result),
            "result": {
                "type": "product",
                "payload": {
                    "title": self._resolve_title(business_result),
                    "summary": output_text,
                    "scene": self._resolve_scene(business_result),
                    "basicInfo": self._as_dict(business_result.get("basic_info")),
                    "productInfo": self._as_dict(
                        business_result.get("product_info"),
                    ),
                    "richText": output_text,
                    "attachments": self._build_attachments(business_result),
                },
            },
            "layout": {
                "autoOpen": True,
                "replace": True,
            },
            "meta": {
                "bizModule": "marketing",
                "source": "agent_output",
            },
        }

    @staticmethod
    def _extract_file_path(item: dict[str, Any]) -> str | None:
        """Extract one display path or URL from a display content item."""

        candidate_keys = (
            "filePath",
            "file_path",
            "pdf_path",
            "pdfPath",
            "fileUrl",
            "file_url",
            "pdf_url",
            "pdfUrl",
            "url",
        )
        for key in candidate_keys:
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                continue
            return value.strip()

        return None

    @staticmethod
    def _resolve_title(business_result: dict[str, Any]) -> str:
        """Resolve a user-facing title from a business result."""

        for key in ("title", "name"):
            value = business_result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return "分析结果"

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        """Return a dict value or an empty dict."""

        return value if isinstance(value, dict) else {}

    def _resolve_scene(self, business_result: dict[str, Any]) -> str | None:
        """Resolve scene from product or basic info."""

        for container_name in ("product_info", "basic_info"):
            container = business_result.get(container_name)
            if not isinstance(container, dict):
                continue
            for key in ("scene", "scenario", "场景"):
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    @staticmethod
    def _has_opportunities(business_result: dict[str, Any]) -> bool:
        """Return True when the payload carries business opportunities."""

        for key in (
            "opportunities",
            "business_opportunities",
            "matched_opportunities",
            "hit_opportunities",
        ):
            value = business_result.get(key)
            if isinstance(value, list) and any(
                isinstance(item, dict) for item in value
            ):
                return True
        return False

    def _extract_opportunities(
        self,
        business_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Normalize opportunity lists for workbench rendering."""

        for key in (
            "opportunities",
            "business_opportunities",
            "matched_opportunities",
            "hit_opportunities",
        ):
            value = business_result.get(key)
            if not isinstance(value, list):
                continue
            return [item for item in value if isinstance(item, dict)]
        return []

    def _build_attachments(
        self,
        business_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Normalize display content items into workbench attachments."""

        display_content = business_result.get("display_content")
        if not isinstance(display_content, list):
            return []

        attachments: list[dict[str, Any]] = []
        for item in display_content:
            if not isinstance(item, dict):
                continue
            file_path = self._extract_file_path(item)
            preview_url = self._first_text(
                item,
                "previewURL",
                "previewUrl",
                "preview_url",
                "preview",
            )
            attachment = {
                "kind": self._resolve_attachment_kind(item, file_path, preview_url),
                "fileName": self._first_text(
                    item,
                    "file_name",
                    "fileName",
                    "name",
                    "title",
                )
                or self._fallback_file_name(file_path),
                "filePath": self._first_text(item, "filePath", "file_path", "path"),
                "fileUrl": self._first_text(
                    item,
                    "fileURL",
                    "fileUrl",
                    "file_url",
                    "url",
                ),
                "previewUrl": preview_url,
                "downloadUrl": self._first_text(
                    item,
                    "downloadURL",
                    "downloadUrl",
                    "download_url",
                    "download",
                ),
                "mimeType": self._first_text(item, "mimeType", "mime_type"),
                "pageIndex": item.get("pageIndex") or item.get("page_index"),
                "extra": dict(item),
            }
            attachments.append(attachment)
        return attachments

    @staticmethod
    def _resolve_attachment_kind(
        item: dict[str, Any],
        file_path: str | None,
        preview_url: str | None,
    ) -> str:
        """Resolve the attachment kind from explicit type or file suffix."""

        item_type = str(item.get("type") or item.get("fileType") or "").lower()
        if item_type in {"pdf", "html", "web", "image", "file"}:
            return item_type

        candidate = (preview_url or file_path or "").lower()
        if candidate.endswith(".pdf"):
            return "pdf"
        if candidate.endswith(".html") or candidate.endswith(".htm"):
            return "html"
        if candidate.startswith("http://") or candidate.startswith("https://"):
            return "web"
        return "file"

    @staticmethod
    def _fallback_file_name(file_path: str | None) -> str | None:
        """Build a display file name from one path-like string."""

        if not isinstance(file_path, str) or not file_path.strip():
            return None
        normalized = file_path.replace("\\", "/").rstrip("/")
        return normalized.rsplit("/", 1)[-1] if "/" in normalized else normalized

    @staticmethod
    def _first_text(item: dict[str, Any], *keys: str) -> str | None:
        """Return the first non-empty string for the given keys."""

        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None


class BusinessResultMetadataInjector:
    """Parse final agent output and inject metadata for the chat result panel."""

    def __init__(
        self,
        structured_result_builder: StructuredResultBuilder | None = None,
    ) -> None:
        self._structured_result_builder = (
            structured_result_builder or StructuredResultBuilder()
        )

    def inject(self, msg: Msg) -> None:
        """Parse final reply text and inject business/structured result metadata."""

        if not isinstance(msg.metadata, dict):
            msg.metadata = {}
        text_blocks = _get_text_blocks(msg)
        if not text_blocks and not isinstance(msg.content, str):
            logger.info(
                "[parser] inject: no text content found, msg.content type=%s",
                type(msg.content).__name__,
            )
            return

        raw_text = (
            "\n".join(block["text"] for block in text_blocks).strip()
            if text_blocks
            else msg.content.strip()
        )
        if not raw_text:
            logger.info("[parser] inject: empty text after strip, skip")
            return

        logger.info(
            "[parser] inject: raw_text len=%d, preview=%.200s",
            len(raw_text),
            raw_text,
        )
        parsed = _extract_business_payload(raw_text)
        if not isinstance(parsed, dict):
            logger.info("[parser] inject: _extract_business_payload returned None")
            return

        business_result = parsed["meta"]["business_result"]
        logger.info(
            "[parser] inject: business_result parsed, keys=%s, has_opportunities=%s",
            list(business_result.keys()),
            self._structured_result_builder._has_opportunities(business_result),
        )
        msg.metadata["business_result"] = business_result
        msg.metadata["business_result_source"] = "agent_output"
        msg.metadata["structured_result"] = (
            self._structured_result_builder.build_from_business_result(
                business_result=business_result,
                output_text=str(parsed.get("output", "")).strip(),
            )
        )
        logger.info(
            "[parser] inject: structured_result built, type=%s, title=%s",
            msg.metadata["structured_result"]["result"]["type"],
            msg.metadata["structured_result"].get("title"),
        )
        _replace_text_output(msg, parsed.get("output", ""))


def _get_text_blocks(msg: Msg) -> list[dict[str, Any]]:
    """Return all text blocks from a message list payload."""

    if not isinstance(msg.content, list):
        return []
    return [
        block
        for block in msg.content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]


def _parse_json_object(value: Any) -> Any:
    """Parse a JSON object string into a dict when possible."""

    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return value
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return value
    return parsed if isinstance(parsed, dict) else value


def _normalize_business_result(
    business_result: dict[str, Any],
) -> dict[str, Any]:
    """Normalize nested JSON strings copied from structured output fields."""

    normalized = dict(business_result)
    normalized["basic_info"] = _parse_json_object(
        normalized.get("basic_info"),
    )
    normalized["product_info"] = _parse_json_object(
        normalized.get("product_info"),
    )
    return normalized


def _is_business_result_dict(data: Any) -> bool:
    """Return True when a dict looks like a business result payload."""

    return isinstance(data, dict) and (
        isinstance(data.get("basic_info"), (dict, str))
        or isinstance(data.get("product_info"), (dict, str))
    )


def _extract_business_payload(text: str) -> dict[str, Any] | None:
    """Extract a normalized business payload from free-form text."""

    fence_matches = [
        (match.group(1).strip(), match.span())
        for match in re.finditer(
            r"```(?:json)?\s*([\s\S]*?)\s*```",
            text,
            flags=re.IGNORECASE,
        )
        if match.group(1).strip()
    ]
    candidates = [candidate for candidate, _span in fence_matches]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    candidates.append(text)

    logger.info(
        "[parser] _extract_business_payload: %d fence blocks, %d total candidates",
        len(fence_matches),
        len(candidates),
    )

    for i, candidate in enumerate(candidates):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            logger.info(
                "[parser] _extract_business_payload: candidate[%d] JSON decode failed, "
                "preview=%.100s",
                i,
                candidate,
            )
            continue
        if not isinstance(parsed, dict):
            logger.info(
                "[parser] _extract_business_payload: candidate[%d] is not dict, type=%s",
                i,
                type(parsed).__name__,
            )
            continue
        meta = parsed.get("meta")
        if isinstance(meta, dict):
            business_result = meta.get("business_result")
            if isinstance(business_result, dict):
                logger.info(
                    "[parser] _extract_business_payload: found via meta.business_result "
                    "at candidate[%d]",
                    i,
                )
                parsed["meta"] = dict(meta)
                parsed["meta"]["business_result"] = _normalize_business_result(
                    business_result,
                )
                return parsed
            logger.info(
                "[parser] _extract_business_payload: candidate[%d] has meta but "
                "no business_result",
                i,
            )
            continue
        top_level_business_result = parsed.get("business_result")
        if isinstance(top_level_business_result, dict):
            logger.info(
                "[parser] _extract_business_payload: found via top-level "
                "business_result at candidate[%d]",
                i,
            )
            return {
                "output": _resolve_output_text(parsed, text),
                "meta": {
                    "business_result": _normalize_business_result(
                        top_level_business_result,
                    ),
                },
            }
        if not _is_business_result_dict(parsed):
            logger.info(
                "[parser] _extract_business_payload: candidate[%d] not a "
                "business_result dict, keys=%s",
                i,
                list(parsed.keys())[:10],
            )
            continue
        logger.info(
            "[parser] _extract_business_payload: candidate[%d] matched as "
            "bare business_result dict",
            i,
        )
        summary_text = text
        for candidate_text, span in fence_matches:
            if candidate == candidate_text:
                summary_text = f"{text[: span[0]]}\n{text[span[1] :]}"
                break
        return {
            "output": summary_text.strip(),
            "meta": {
                "business_result": _normalize_business_result(parsed),
            },
        }
    logger.info("[parser] _extract_business_payload: no match found in any candidate")
    return None


def _resolve_output_text(parsed: dict[str, Any], fallback_text: str) -> str:
    """Resolve a human-readable summary text from parsed wrapper payloads."""

    output = parsed.get("output")
    if isinstance(output, str) and output.strip():
        return output.strip()

    structured_result = parsed.get("structured_result")
    if isinstance(structured_result, dict):
        result = structured_result.get("result")
        if isinstance(result, dict):
            payload = result.get("payload")
            if isinstance(payload, dict):
                for key in ("text", "summary", "richText"):
                    value = payload.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()

    return fallback_text.strip()


def _replace_text_output(msg: Msg, output_value: Any) -> None:
    """Replace the first text block, or string content, with output_value."""

    if not isinstance(output_value, str):
        output_value = json.dumps(output_value, ensure_ascii=False)
    text_blocks = _get_text_blocks(msg)
    if text_blocks:
        text_blocks[0]["text"] = output_value
        return
    msg.content = output_value


def inject_business_result_metadata(msg: Msg) -> None:
    """Compatibility wrapper used by output_binding import-path config."""

    BusinessResultMetadataInjector().inject(msg)
