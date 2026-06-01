# -*- coding: utf-8 -*-
"""Agent hooks package.

This package provides hook implementations for QwenPawAgent that follow
AgentScope's hook interface (any Callable).

Available Hooks:
    - BootstrapHook: First-time setup guidance
    - BaseBusinessPostReplyHook: 业务回复后处理抽象基类
    - BusinessPostReplyHookManager: 业务回复后处理编排
"""

from .bootstrap import BootstrapHook
from .post_reply_business import (
    BaseBusinessPostReplyHook,
    BusinessPostReplyHookManager,
)

__all__ = [
    "BootstrapHook",
    "BaseBusinessPostReplyHook",
    "BusinessPostReplyHookManager",
]
