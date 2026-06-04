# -*- coding: utf-8 -*-
"""Schemas for government opportunity analysis — RA-agent structured output."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SupportTypeEnum(str, Enum):
    """支撑类型（对应前端 GovernmentOpportunityDetail supportType）。"""

    TECH = "技术支撑"
    SOLUTION = "方案支撑"
    BIDDING = "投标支撑"
    COMPREHENSIVE = "综合支撑"


class OpportunityRatingEnum(str, Enum):
    """商机评级。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BudgetRange(BaseModel):
    """预算区间。"""

    min_yuan: float
    max_yuan: float
    note: str | None = None


class AttachmentItem(BaseModel):
    """展示附件。"""

    type: str = Field(..., description="文件类型: pdf / html / web / file")
    file_name: str
    file_path: str | None = None
    file_url: str | None = None


class GovernmentOpportunityAnalysis(BaseModel):
    """RA-agent 政企项目商机分析结构化输出模型。

    由 LLM 在 reply(structured_model=...) 调用时直接输出。
    字段映射到前端 GovernmentOpportunityDetailResponse。
    """

    # ── 摘要 ──
    output: str = Field(..., description="用户可读的商机分析摘要文字")

    # ── 基本信息 → GovernmentOpportunityListItem ──
    project_name: str = Field(..., description="项目名称")
    customer_name: str = Field(..., description="客户名称")
    city: str = Field(..., description="来源城市")
    industry: str = Field(..., description="所属行业")
    support_type: SupportTypeEnum = Field(..., description="支撑类型")

    # ── 需求描述 → requirementDesc ──
    requirement_desc: str = Field(..., description="需求描述全文")

    # ── 商机评级 ──
    opportunity_rating: OpportunityRatingEnum = Field(..., description="商机评级")
    opportunity_score: int | None = Field(default=None, ge=0, le=100, description="商机评分 0-100")

    # ── 预算区间 ──
    budget: BudgetRange | None = None

    # ── 附件 ──
    display_content: list[AttachmentItem] = Field(
        default_factory=list,
        description="关联的展示附件（PDF 报告等）",
    )
