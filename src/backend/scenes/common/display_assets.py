# -*- coding: utf-8 -*-
"""Helpers for safely exposing business result display assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import mimetypes

from fastapi import HTTPException, status

DisplayContentItem = dict[str, Any]

ALLOWED_ASSET_DIRS = ("reports", "media", "tool_results")


def normalize_display_content(
    items: list[DisplayContentItem] | None,
    *,
    biz_module: str,
    record_id: int,
    agent_id: str | None,
    collection: str = "results",
) -> list[DisplayContentItem]:
    """Add stable asset ids and API URLs to display_content items."""

    if not items:
        return []

    normalized: list[DisplayContentItem] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        next_item = dict(item)
        asset_type = _asset_type(next_item)
        file_path = _text(next_item, "file_path", "filePath", "path")
        existing_url = _text(next_item, "file_url", "fileUrl", "url")
        if not file_path and not existing_url:
            normalized.append(next_item)
            continue

        asset_id = _text(next_item, "asset_id", "assetId")
        if not asset_id:
            asset_id = f"{asset_type}-{index}"
            next_item["asset_id"] = asset_id

        file_name = _text(next_item, "file_name", "fileName")
        if not file_name and file_path:
            next_item["file_name"] = Path(file_path.replace("\\", "/")).name

        if not existing_url and file_path:
            if collection == "opportunities":
                next_item["file_url"] = (
                    f"/api/backend/results/{biz_module}/opportunities/"
                    f"{record_id}/assets/{asset_id}"
                )
            else:
                next_item["file_url"] = (
                    f"/api/backend/results/{biz_module}/"
                    f"{record_id}/assets/{asset_id}"
                )

        if not _text(next_item, "type") and asset_type:
            next_item["type"] = asset_type

        normalized.append(next_item)

    return normalized


def resolve_display_asset_path(
    items: list[DisplayContentItem] | None,
    *,
    asset_id: str,
    agent_id: str | None,
    working_dir: Path,
) -> tuple[Path, str]:
    """Resolve one display asset to a safe local path and MIME type."""

    target = _find_asset(items or [], asset_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    file_path = _text(target, "file_path", "filePath", "path")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset path not found",
        )

    resolved_path = _resolve_safe_path(
        file_path,
        agent_id=agent_id,
        working_dir=working_dir,
    )
    if not resolved_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset file not found",
        )

    return resolved_path, _mime_type(resolved_path)


def _find_asset(
    items: list[DisplayContentItem],
    asset_id: str,
) -> DisplayContentItem | None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        expected_id = _text(item, "asset_id", "assetId")
        if not expected_id:
            expected_id = f"{_asset_type(item)}-{index}"
        if expected_id == asset_id:
            return item
    return None


def _resolve_safe_path(
    file_path: str,
    *,
    agent_id: str | None,
    working_dir: Path,
) -> Path:
    normalized = file_path.replace("\\", "/").strip()
    raw_path = Path(normalized)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Illegal asset path",
        )

    workspace_name = agent_id or "RA-agent"
    workspace_root = (working_dir / "workspaces" / workspace_name).resolve()
    resolved = (workspace_root / raw_path).resolve()

    allowed_roots = [
        (workspace_root / dirname).resolve()
        for dirname in ALLOWED_ASSET_DIRS
    ]
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Asset path is outside allowed directories",
        )

    return resolved


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".svg":
        return "image/svg+xml"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _asset_type(item: DisplayContentItem) -> str:
    value = _text(item, "type", "kind", "file_type", "fileType")
    if value:
        return value
    file_name = _text(item, "file_name", "fileName", "file_path", "filePath")
    suffix = Path(file_name or "").suffix.lower().lstrip(".")
    if suffix in {"html", "pdf", "png", "jpg", "jpeg", "svg"}:
        return "image" if suffix in {"png", "jpg", "jpeg", "svg"} else suffix
    return "file"


def _text(item: DisplayContentItem, *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
