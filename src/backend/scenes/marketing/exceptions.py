# -*- coding: utf-8 -*-
"""Domain exceptions for marketing result persistence."""


class MarketingResultNotFoundError(Exception):
    """Raised when the target marketing result does not exist."""


class MarketingOpportunityNotFoundError(Exception):
    """Raised when the target marketing opportunity does not exist."""
