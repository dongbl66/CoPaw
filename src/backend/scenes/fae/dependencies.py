# -*- coding: utf-8 -*-
"""FAE scene dependencies (service builders for FastAPI)."""

from __future__ import annotations

from backend.database.connection import get_backend_database

from .service import FAEOpportunityService, FAEResultService


def build_fae_opportunity_service() -> FAEOpportunityService:
    """Provide a government opportunity service instance."""

    return FAEOpportunityService(get_backend_database())


def build_fae_result_service() -> FAEResultService:
    """Provide a FAE result service instance."""

    return FAEResultService(get_backend_database())
