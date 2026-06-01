# -*- coding: utf-8 -*-
"""Weekly Report Storage Module"""
from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

from ..constant import WORKING_DIR

WEEKLY_REPORTS_DIR = WORKING_DIR / "weekly_reports"
WEEKLY_REPORT_INDEX_FILE = WEEKLY_REPORTS_DIR / "index.json"
_LOCK = asyncio.Lock()


@dataclass
class WeeklyReport:
    id: str
    title: str
    period_start: str  # ISO date string
    period_end: str    # ISO date string
    author: str
    content: str       # Markdown content
    project_name: Optional[str] = None
    status: str = "draft"  # draft, submitted, archived
    created_at: float = 0.0
    updated_at: float = 0.0
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at == 0:
            self.created_at = datetime.now().timestamp()
        if self.updated_at == 0:
            self.updated_at = datetime.now().timestamp()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeeklyReport":
        return cls(**data)

    def get_file_path(self) -> Path:
        return WEEKLY_REPORTS_DIR / f"{self.id}.md"


def _ensure_dir():
    WEEKLY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> list[dict[str, Any]]:
    _ensure_dir()
    if not WEEKLY_REPORT_INDEX_FILE.exists():
        return []
    try:
        data = json.loads(WEEKLY_REPORT_INDEX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _save_index(index: list[dict[str, Any]]):
    _ensure_dir()
    WEEKLY_REPORT_INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _save_report_content(report: WeeklyReport):
    _ensure_dir()
    report.get_file_path().write_text(report.content, encoding="utf-8")


def _load_report_content(report_id: str) -> Optional[str]:
    file_path = WEEKLY_REPORTS_DIR / f"{report_id}.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return None


async def create_report(
    title: str,
    period_start: str,
    period_end: str,
    author: str,
    content: str,
    project_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> WeeklyReport:
    """Create a new weekly report"""
    report = WeeklyReport(
        id=str(uuid.uuid4()),
        title=title,
        period_start=period_start,
        period_end=period_end,
        author=author,
        content=content,
        project_name=project_name,
        tags=tags or [],
    )

    async with _LOCK:
        # Save content file
        _save_report_content(report)
        # Update index
        index = _load_index()
        index.insert(0, report.to_dict())
        _save_index(index)

    return report


async def get_report(report_id: str) -> Optional[WeeklyReport]:
    """Get a weekly report by ID"""
    async with _LOCK:
        index = _load_index()
        for item in index:
            if item["id"] == report_id:
                content = _load_report_content(report_id)
                if content:
                    item["content"] = content
                return WeeklyReport.from_dict(item)
    return None


async def list_reports(
    status: Optional[str] = None,
    project_name: Optional[str] = None,
    author: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[WeeklyReport]:
    """List weekly reports with filters"""
    async with _LOCK:
        index = _load_index()

    filtered = []
    for item in index:
        if status and item.get("status") != status:
            continue
        if project_name and item.get("project_name") != project_name:
            continue
        if author and item.get("author") != author:
            continue
        filtered.append(WeeklyReport.from_dict(item))

    return filtered[offset:offset + limit]


async def update_report(
    report_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    status: Optional[str] = None,
    project_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Optional[WeeklyReport]:
    """Update a weekly report"""
    async with _LOCK:
        index = _load_index()
        found = None
        found_idx = -1

        for idx, item in enumerate(index):
            if item["id"] == report_id:
                found = item
                found_idx = idx
                break

        if not found:
            return None

        # Update fields
        if title is not None:
            found["title"] = title
        if status is not None:
            found["status"] = status
        if project_name is not None:
            found["project_name"] = project_name
        if tags is not None:
            found["tags"] = tags
        found["updated_at"] = datetime.now().timestamp()

        report = WeeklyReport.from_dict(found)

        # Update content file if needed
        if content is not None:
            report.content = content
            _save_report_content(report)

        # Load full content
        full_content = _load_report_content(report_id)
        if full_content:
            report.content = full_content

        # Update index
        index[found_idx] = report.to_dict()
        _save_index(index)

    return report


async def delete_report(report_id: str) -> bool:
    """Delete a weekly report"""
    async with _LOCK:
        index = _load_index()
        new_index = []
        deleted = False

        for item in index:
            if item["id"] == report_id:
                deleted = True
            else:
                new_index.append(item)

        if deleted:
            _save_index(new_index)
            # Delete content file
            file_path = WEEKLY_REPORTS_DIR / f"{report_id}.md"
            if file_path.exists():
                file_path.unlink()

    return deleted
