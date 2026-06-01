# -*- coding: utf-8 -*-
"""Schemas for marketing product-result CRUD."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MarketingResultFileCreate(BaseModel):
    """Attachment payload persisted under one product result."""

    file_name: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., min_length=1, max_length=50)
    mime_type: str | None = None
    file_url: str | None = None
    preview_url: str | None = None
    download_url: str | None = None
    file_path: str | None = None
    file_id: str | None = None
    file_size: int | None = None
    page_index: int | None = None
    sort_order: int = 0
    source_type: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class MarketingResultFileRead(MarketingResultFileCreate):
    """Attachment read model returned with one product result."""

    id: int
    result_id: int
    created_at: datetime
    updated_at: datetime


class MarketingResultCreate(BaseModel):
    """Input payload for creating one product result."""

    title: str = Field(..., min_length=1, max_length=200)
    result_type: str = Field(..., min_length=1, max_length=50)
    scene: str | None = Field(default=None, max_length=100)
    summary: str | None = None
    detail_content: list[dict[str, Any]] = Field(default_factory=list)
    info: dict[str, Any] = Field(default_factory=dict)
    basic_info: dict[str, Any] = Field(default_factory=dict)
    product_info: dict[str, Any] = Field(default_factory=dict)
    attachments: list[MarketingResultFileCreate] = Field(
        default_factory=list,
    )
    save_status: str = Field(default="draft", min_length=1, max_length=20)
    session_id: str | None = None
    agent_id: str | None = None


class MarketingResultUpdate(BaseModel):
    """Input payload for updating one product result."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    result_type: str | None = Field(default=None, min_length=1, max_length=50)
    scene: str | None = Field(default=None, max_length=100)
    summary: str | None = None
    detail_content: list[dict[str, Any]] | None = None
    info: dict[str, Any] | None = None
    basic_info: dict[str, Any] | None = None
    product_info: dict[str, Any] | None = None
    attachments: list[MarketingResultFileCreate] | None = None
    save_status: str | None = Field(default=None, min_length=1, max_length=20)
    session_id: str | None = None
    agent_id: str | None = None


class MarketingResultRead(BaseModel):
    """Read model returned by the product-result APIs."""

    id: int
    title: str
    result_type: str
    save_status: str = "draft"
    scene: str | None = None
    summary: str | None = None
    detail_content: list[dict[str, Any]] = Field(default_factory=list)
    info: dict[str, Any] = Field(default_factory=dict)
    basic_info: dict[str, Any] = Field(default_factory=dict)
    product_info: dict[str, Any] = Field(default_factory=dict)
    attachments: list[MarketingResultFileRead] = Field(default_factory=list)
    session_id: str | None = None
    agent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class MarketingResultListResponse(BaseModel):
    """Collection response for marketing results."""

    items: list[MarketingResultRead]


class MarketingResultLatestResponse(BaseModel):
    """Latest-result response for one chat session."""

    item: MarketingResultRead | None = None
