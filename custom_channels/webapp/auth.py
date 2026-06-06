# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from qwenpaw.constant import EnvVarLoader, SECRET_DIR


BOOT_TOKEN_TTL_SECONDS = EnvVarLoader.get_int(
    "QWENPAW_WEBAPP_BOOT_TOKEN_TTL_SECONDS",
    300,
    min_value=1,
)
OA_STATE_TTL_SECONDS = EnvVarLoader.get_int(
    "QWENPAW_WEBAPP_OA_STATE_TTL_SECONDS",
    600,
    min_value=1,
)
OA_SESSION_TTL_SECONDS = EnvVarLoader.get_int(
    "QWENPAW_WEBAPP_OA_SESSION_TTL_SECONDS",
    7200,
    min_value=1,
)
_BOOT_TOKEN_SECRET_FILE = SECRET_DIR / "webapp_boot_token_secret"


class BootTokenError(ValueError):
    """Raised when a webapp boot token is missing, invalid, or expired."""


def create_boot_token(
    *,
    user_id: str,
    scene: str,
    source: str = "",
    entry: str = "",
    expiry_seconds: int | None = None,
) -> str:
    if not user_id:
        raise BootTokenError("user_id is required")
    if not scene:
        raise BootTokenError("scene is required")
    ttl = expiry_seconds if expiry_seconds is not None else BOOT_TOKEN_TTL_SECONDS
    ttl = max(1, int(ttl))
    payload = {
        "sub": user_id,
        "scene": scene,
        "source": source,
        "entry": entry,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
        "nonce": secrets.token_hex(8),
    }
    payload_b64 = _urlsafe_b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    signature = hmac.new(
        _get_boot_token_secret().encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def create_oa_state_token(
    *,
    scene: str,
    entry: str,
    h5_base_url: str,
    source: str = "oa_h5",
    expiry_seconds: int | None = None,
) -> str:
    if not scene:
        raise BootTokenError("scene is required")
    if not h5_base_url:
        raise BootTokenError("h5_base_url is required")
    ttl = expiry_seconds if expiry_seconds is not None else OA_STATE_TTL_SECONDS
    payload = {
        "type": "oa_state",
        "scene": scene,
        "entry": entry,
        "h5_base_url": h5_base_url,
        "source": source,
        "iat": int(time.time()),
        "exp": int(time.time()) + max(1, int(ttl)),
        "nonce": secrets.token_hex(8),
    }
    return _sign_payload(payload)


def validate_oa_state_token(token: str) -> dict[str, Any]:
    payload = _validate_signed_payload(token)
    if payload.get("type") != "oa_state":
        raise BootTokenError("invalid oa_state token type")
    return payload


def create_oa_session_token(
    *,
    user_id: str,
    openid: str,
    scene: str,
    source: str,
    entry: str,
    expiry_seconds: int | None = None,
) -> str:
    if not user_id:
        raise BootTokenError("user_id is required")
    if not openid:
        raise BootTokenError("openid is required")
    if not scene:
        raise BootTokenError("scene is required")
    ttl = expiry_seconds if expiry_seconds is not None else OA_SESSION_TTL_SECONDS
    payload = {
        "type": "oa_session",
        "sub": user_id,
        "openid": openid,
        "scene": scene,
        "source": source,
        "entry": entry,
        "iat": int(time.time()),
        "exp": int(time.time()) + max(1, int(ttl)),
        "nonce": secrets.token_hex(8),
    }
    return _sign_payload(payload)


def validate_oa_session_token(token: str) -> dict[str, Any]:
    payload = _validate_signed_payload(token)
    if payload.get("type") != "oa_session":
        raise BootTokenError("invalid oa_session token type")
    return payload


def validate_boot_token(
    boot_token: str,
    *,
    expected_scene: str | None = None,
) -> dict[str, Any]:
    if not boot_token:
        raise BootTokenError("boot_token is required")
    parts = boot_token.split(".", 1)
    if len(parts) != 2:
        raise BootTokenError("invalid boot_token format")
    payload_b64, signature = parts
    expected_sig = hmac.new(
        _get_boot_token_secret().encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        raise BootTokenError("invalid boot_token signature")
    try:
        payload = json.loads(_urlsafe_b64decode(payload_b64).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise BootTokenError("invalid boot_token payload") from exc
    if payload.get("exp", 0) < int(time.time()):
        raise BootTokenError("boot_token expired")
    if not payload.get("sub"):
        raise BootTokenError("boot_token missing subject")
    token_scene = str(payload.get("scene") or "")
    if expected_scene and token_scene != expected_scene:
        raise BootTokenError("boot_token scene mismatch")
    return payload


def build_wechat_oauth_authorize_url(
    *,
    app_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "snsapi_base",
) -> str:
    query = urlencode(
        {
            "appid": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
        },
    )
    return (
        "https://open.weixin.qq.com/connect/oauth2/authorize?"
        f"{query}#wechat_redirect"
    )


def _get_boot_token_secret() -> str:
    env_secret = os.environ.get("QWENPAW_WEBAPP_BOOT_TOKEN_SECRET", "").strip()
    if env_secret:
        return env_secret
    if _BOOT_TOKEN_SECRET_FILE.is_file():
        secret = _BOOT_TOKEN_SECRET_FILE.read_text(encoding="utf-8").strip()
        if secret:
            return secret
    secret = secrets.token_hex(32)
    _BOOT_TOKEN_SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    _BOOT_TOKEN_SECRET_FILE.write_text(secret, encoding="utf-8")
    try:
        os.chmod(_BOOT_TOKEN_SECRET_FILE, 0o600)
    except OSError:
        pass
    return secret


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign_payload(payload: dict[str, Any]) -> str:
    payload_b64 = _urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    )
    signature = hmac.new(
        _get_boot_token_secret().encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def _validate_signed_payload(token: str) -> dict[str, Any]:
    if not token:
        raise BootTokenError("token is required")
    parts = token.split(".", 1)
    if len(parts) != 2:
        raise BootTokenError("invalid token format")
    payload_b64, signature = parts
    expected_sig = hmac.new(
        _get_boot_token_secret().encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        raise BootTokenError("invalid token signature")
    try:
        payload = json.loads(_urlsafe_b64decode(payload_b64).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise BootTokenError("invalid token payload") from exc
    if payload.get("exp", 0) < int(time.time()):
        raise BootTokenError("token expired")
    return payload
