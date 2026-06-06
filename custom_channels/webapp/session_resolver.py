# -*- coding: utf-8 -*-
from __future__ import annotations


def build_session_id(
    *,
    scene: str,
    user_id: str,
    conversation_id: str,
) -> str:
    if not scene:
        raise ValueError("scene is required")
    if not user_id:
        raise ValueError("user_id is required")
    if not conversation_id:
        raise ValueError("conversation_id is required")
    return f"webapp:{scene}:{user_id}:{conversation_id}"

