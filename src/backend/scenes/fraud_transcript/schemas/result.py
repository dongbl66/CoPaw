# -*- coding: utf-8 -*-
"""Schemas for fraud transcript result CRUD."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FraudTranscriptResultCreate(BaseModel):
    """Input payload for creating one fraud transcript result."""

    title: str = Field(..., min_length=1, max_length=200)
    result_type: str = Field(..., min_length=1, max_length=50)
    save_status: str = Field(default="draft", min_length=1, max_length=20)
    scene: str | None = Field(default="fraud_transcript_report", max_length=100)
    summary: str | None = None
    basic_info: dict[str, Any] = Field(default_factory=dict)
    product_info: dict[str, Any] = Field(default_factory=dict)
    qa_records: list[dict[str, Any]] = Field(default_factory=list)
    structured_result: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None
    agent_id: str | None = None


class FraudTranscriptResultUpdate(BaseModel):
    """Input payload for updating one fraud transcript result."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    result_type: str | None = Field(default=None, min_length=1, max_length=50)
    save_status: str | None = Field(default=None, min_length=1, max_length=20)
    scene: str | None = Field(default=None, max_length=100)
    summary: str | None = None
    basic_info: dict[str, Any] | None = None
    product_info: dict[str, Any] | None = None
    qa_records: list[dict[str, Any]] | None = None
    structured_result: dict[str, Any] | None = None
    session_id: str | None = None
    agent_id: str | None = None


class FraudTranscriptResultRead(BaseModel):
    """Read model returned by fraud transcript result APIs."""

    id: int
    title: str
    result_type: str
    save_status: str = "draft"
    scene: str | None = None
    summary: str | None = None
    basic_info: dict[str, Any] = Field(default_factory=dict)
    product_info: dict[str, Any] = Field(default_factory=dict)
    qa_records: list[dict[str, Any]] = Field(default_factory=list)
    structured_result: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None
    agent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class FraudTranscriptResultListResponse(BaseModel):
    """Collection response for fraud transcript results."""

    items: list[FraudTranscriptResultRead]


class FraudTranscriptResultLatestResponse(BaseModel):
    """Latest-result response for one chat session."""

    item: FraudTranscriptResultRead | None = None

