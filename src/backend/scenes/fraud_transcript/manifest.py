# -*- coding: utf-8 -*-
"""Fraud transcript business module declaration."""

from backend.core.business_hooks import register_business_post_reply_hook
from backend.core.registry import register_backend_module
from backend.core.types import BackendModuleManifest
from backend.scenes.fraud_transcript.router import create_router


def create_fraud_transcript_post_reply_hook():
    """Create the fraud transcript post-reply hook lazily."""

    from backend.scenes.fraud_transcript.hooks import FraudTranscriptPostReplyHook

    return FraudTranscriptPostReplyHook()


def register() -> None:
    """Register fraud transcript backend scene capabilities."""

    register_backend_module(
        BackendModuleManifest(
            module_id="fraud_transcript",
            name="Fraud transcript module",
            version="0.1.0",
            router_factories=[create_router],
        ),
    )
    register_business_post_reply_hook(create_fraud_transcript_post_reply_hook)


register()

