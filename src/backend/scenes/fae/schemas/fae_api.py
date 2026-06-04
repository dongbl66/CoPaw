# -*- coding: utf-8 -*-
"""Schemas for FAE government opportunity API requests/responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── API Request / Response schemas ──


class GovernmentOpportunityCreate(BaseModel):
    """Create government opportunity."""

    project_name: str = Field(..., description="项目名称")
    customer_name: str = Field(..., description="客户名称")
    city: str = Field(..., description="来源城市")
    industry: str = Field(..., description="所属行业")
    support_type: str = Field(..., description="支撑类型")
    requirement_desc: str = Field(..., description="需求描述")
    opportunity_rating: str = Field(..., description="商机评级")
    opportunity_score: int | None = Field(default=None, ge=0, le=100)
    budget_min_yuan: float | None = None
    budget_max_yuan: float | None = None
    budget_note: str | None = None
    display_content: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str | None = None


class GovernmentOpportunityUpdate(BaseModel):
    """Update government opportunity."""

    project_name: str | None = None
    customer_name: str | None = None
    city: str | None = None
    industry: str | None = None
    support_type: str | None = None
    requirement_desc: str | None = None
    opportunity_rating: str | None = None
    opportunity_score: int | None = None
    budget_min_yuan: float | None = None
    budget_max_yuan: float | None = None
    budget_note: str | None = None
    display_content: list[dict[str, Any]] | None = None


class GovernmentOpportunityRead(BaseModel):
    """Government opportunity read model (matches frontend response)."""

    id: int
    project_name: str
    customer_name: str
    city: str
    industry: str
    support_type: str
    create_time: str
    update_time: str
    requirement_desc: str
    opportunity_rating: str
    opportunity_score: int | None = None
    budget_min_yuan: float | None = None
    budget_max_yuan: float | None = None
    budget_note: str | None = None
    display_content: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str | None = None
    agent_id: str | None = None


class GovernmentOpportunityListResponse(BaseModel):
    """List opportunities response."""

    items: list[GovernmentOpportunityRead]


class GovernmentOpportunityDetailResponse(BaseModel):
    """Detail page response (matches GovernmentOpportunityDetail frontend)."""

    id: int
    project_name: str
    customer_name: str
    city: str
    industry: str
    support_type: str
    create_time: str
    update_time: str
    requirement_desc: str
    opportunity_rating: str
    opportunity_score: int | None = None
    budget_min_yuan: float | None = None
    budget_max_yuan: float | None = None
    budget_note: str | None = None
    display_content: list[dict[str, Any]] = Field(default_factory=list)


# ── FAE Result schemas (for result panel API) ──


class FAEResultRead(BaseModel):
    """FAE result read model."""

    id: int
    title: str
    result_type: str
    save_status: str
    scene: str | None = None
    summary: str | None = None
    info: dict[str, Any] = Field(default_factory=dict)
    basic_info: dict[str, Any] = Field(default_factory=dict)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str | None = None
    agent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class FAEResultListResponse(BaseModel):
    """List results response."""

    items: list[FAEResultRead]


class FAEResultLatestResponse(BaseModel):
    """Latest result response."""

    item: FAEResultRead | None


class FAEResultSaveRequest(BaseModel):
    """Save result request."""

    result_id: int


class FAEResultFromToolOutputRequest(BaseModel):
    """Create a FAE result from a tool output when automatic persistence missed it."""

    tool_name: str = "generate_response"
    tool_output: dict[str, Any]
    session_id: str | None = None
    agent_id: str | None = "RA-agent"
