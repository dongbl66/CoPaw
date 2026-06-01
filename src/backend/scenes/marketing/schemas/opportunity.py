# -*- coding: utf-8 -*-
"""Schemas for marketing opportunity CRUD."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MarketingOpportunityCreate(BaseModel):
    """Input payload for creating one opportunity."""

    title: str = Field(..., min_length=1, max_length=255)
    opportunity_type: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=255)
    publish_time: str | None = Field(default=None, max_length=100)
    deadline: str | None = Field(default=None, max_length=100)
    credibility: float | None = None
    contact: str | None = Field(default=None, max_length=255)
    budget: float | None = None
    purchase_amount: float | None = None
    link_status: str | None = Field(default=None, max_length=100)
    reason: str | None = None
    original_link: str | None = Field(default=None, max_length=1024)
    level: str | None = Field(default=None, max_length=100)
    summary: str | None = None
    session_id: str | None = None
    agent_id: str | None = None


class MarketingOpportunityUpdate(BaseModel):
    """Input payload for updating one opportunity."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    opportunity_type: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=255)
    publish_time: str | None = Field(default=None, max_length=100)
    deadline: str | None = Field(default=None, max_length=100)
    credibility: float | None = None
    contact: str | None = Field(default=None, max_length=255)
    budget: float | None = None
    purchase_amount: float | None = None
    link_status: str | None = Field(default=None, max_length=100)
    reason: str | None = None
    original_link: str | None = Field(default=None, max_length=1024)
    level: str | None = Field(default=None, max_length=100)
    summary: str | None = None
    session_id: str | None = None
    agent_id: str | None = None


class MarketingOpportunityRead(BaseModel):
    """Read model returned by the opportunity APIs."""

    id: int
    title: str
    opportunity_type: str | None = None
    region: str | None = None
    source: str | None = None
    publish_time: str | None = None
    deadline: str | None = None
    credibility: float | None = None
    contact: str | None = None
    budget: float | None = None
    purchase_amount: float | None = None
    link_status: str | None = None
    reason: str | None = None
    original_link: str | None = None
    level: str | None = None
    summary: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class MarketingOpportunityListResponse(BaseModel):
    """List response returned by the opportunity APIs."""

    items: list[MarketingOpportunityRead] = Field(default_factory=list)
