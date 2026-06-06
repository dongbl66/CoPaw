# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BootstrapRequest(BaseModel):
    boot_token: str
    scene: str
    source: str = "miniapp_webview"
    entry: str = ""


class BootstrapResponse(BaseModel):
    access_token: str
    user_id: str
    conversation_id: str
    session_id: str
    ws_url: str
    scene_config: dict[str, Any] = Field(default_factory=dict)

