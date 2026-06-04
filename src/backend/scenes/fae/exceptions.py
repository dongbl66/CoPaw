# -*- coding: utf-8 -*-
"""FAE exceptions."""


class FAEGovernmentOpportunityNotFoundError(Exception):
    """Raised when a government opportunity record is not found."""


class FAEResultNotFoundError(Exception):
    """Raised when a FAE result record is not found."""
