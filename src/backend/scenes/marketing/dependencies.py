# -*- coding: utf-8 -*-
"""Composition helpers for marketing scene services."""

from backend.database.connection import get_backend_database

from .service import MarketingOpportunityService, MarketingResultService


def build_marketing_result_service() -> MarketingResultService:
    """Build the marketing result service from shared backend resources."""

    return MarketingResultService(get_backend_database())


def build_marketing_opportunity_service() -> MarketingOpportunityService:
    """Build the marketing opportunity service from shared backend resources."""

    return MarketingOpportunityService(get_backend_database())
