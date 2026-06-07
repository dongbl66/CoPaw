# -*- coding: utf-8 -*-
"""Registry for backend scene post-reply business hooks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

BusinessPostReplyHookFactory = Callable[[], Any]

_BUSINESS_POST_REPLY_HOOK_FACTORIES: list[BusinessPostReplyHookFactory] = []


def register_business_post_reply_hook(
    factory: BusinessPostReplyHookFactory,
) -> None:
    """Register a backend scene post-reply hook factory.

    Registration is idempotent so backend module loading can be called from
    both app startup and agent construction without duplicating handlers.
    """

    if factory in _BUSINESS_POST_REPLY_HOOK_FACTORIES:
        return
    _BUSINESS_POST_REPLY_HOOK_FACTORIES.append(factory)


def get_business_post_reply_hooks() -> list[Any]:
    """Instantiate all registered post-reply business hooks."""

    return [factory() for factory in _BUSINESS_POST_REPLY_HOOK_FACTORIES]


def get_business_post_reply_hook_factories() -> list[BusinessPostReplyHookFactory]:
    """Return registered post-reply hook factories without instantiating them."""

    return list(_BUSINESS_POST_REPLY_HOOK_FACTORIES)
