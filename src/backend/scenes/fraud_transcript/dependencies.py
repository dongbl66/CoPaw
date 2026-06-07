# -*- coding: utf-8 -*-
"""Composition helpers for fraud transcript scene services."""

from backend.database.connection import get_backend_database

from .service import FraudTranscriptResultService


def build_fraud_transcript_result_service() -> FraudTranscriptResultService:
    """Build the fraud transcript result service from shared resources."""

    return FraudTranscriptResultService(get_backend_database())

