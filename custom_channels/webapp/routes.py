# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import httpx
from agentscope.memory import InMemoryMemory
from agentscope_runtime.engine.schemas.agent_schemas import ContentType

from .auth import (
    BootTokenError,
    build_wechat_oauth_authorize_url,
    create_boot_token,
    create_oa_session_token,
    create_oa_state_token,
    validate_boot_token,
    validate_oa_session_token,
    validate_oa_state_token,
)
from .dto import BootstrapRequest, BootstrapResponse
from .scene_registry import SceneRegistry, UnknownSceneError
from .session_resolver import build_session_id
from .ws_hub import WebAppWsHub
from qwenpaw.app.runner.utils import agentscope_msg_to_message


router = APIRouter()
_ws_hub = WebAppWsHub()
_OA_SESSION_COOKIE = "qwenpaw_webapp_oa_session"


@router.get("/api/webapp/demo", response_class=HTMLResponse)
async def webapp_demo_page(
    scene: str = "opportunity_insight",
    source: str = "oa_h5",
    entry: str = "manual_demo",
    boot_token: str = "",
    api_base: str = "",
) -> HTMLResponse:
    return HTMLResponse(
        _render_demo_html_v2(
            scene=scene,
            source=source,
            entry=entry,
            boot_token=boot_token,
            api_base=api_base,
        ),
    )


@router.get("/api/webapp/oa/entry")
async def webapp_oa_entry(
    request: Request,
    scene: str,
    entry: str = "official_account_menu",
    source: str = "oa_h5",
    dev_user_id: str = "",
):
    h5_base_url = _get_h5_base_url(request)
    if _is_oa_dev_mode() and dev_user_id:
        session_token = create_oa_session_token(
            user_id=dev_user_id,
            openid=dev_user_id,
            scene=scene,
            source=source,
            entry=entry,
        )
        response = _redirect_response(
            f"{h5_base_url}?scene={scene}&source={source}&entry={entry}",
        )
        response.set_cookie(
            _OA_SESSION_COOKIE,
            session_token,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
        )
        return response

    app_id = _get_required_env("QWENPAW_WECHAT_OA_APP_ID")
    public_base_url = _get_public_base_url(request)
    redirect_uri = f"{public_base_url}/api/webapp/oa/callback"
    state = create_oa_state_token(
        scene=scene,
        entry=entry,
        h5_base_url=h5_base_url,
        source=source,
    )
    authorize_url = build_wechat_oauth_authorize_url(
        app_id=app_id,
        redirect_uri=redirect_uri,
        state=state,
        scope=_get_oa_scope(),
    )
    return _redirect_response(authorize_url)


@router.get("/api/webapp/oa/callback")
async def webapp_oa_callback(
    request: Request,
    code: str,
    state: str,
):
    state_payload = validate_oa_state_token(state)
    oauth_result = await _exchange_wechat_oauth_code(code)
    openid = str(oauth_result.get("openid") or "")
    if not openid:
        raise HTTPException(status_code=502, detail="Missing openid from WeChat OAuth")
    user_id = _map_openid_to_user_id(openid)
    session_token = create_oa_session_token(
        user_id=user_id,
        openid=openid,
        scene=str(state_payload["scene"]),
        source=str(state_payload.get("source") or "oa_h5"),
        entry=str(state_payload.get("entry") or "official_account_menu"),
    )
    h5_url = (
        f"{state_payload['h5_base_url']}?scene={state_payload['scene']}"
        f"&source={state_payload.get('source', 'oa_h5')}"
        f"&entry={state_payload.get('entry', 'official_account_menu')}"
    )
    response = _redirect_response(h5_url)
    response.set_cookie(
        _OA_SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    return response


@router.get("/api/webapp/oa/context")
async def webapp_oa_context(request: Request) -> dict:
    session_token = request.cookies.get(_OA_SESSION_COOKIE, "")
    if not session_token:
        raise HTTPException(status_code=401, detail="Missing OA session cookie")
    session_payload = validate_oa_session_token(session_token)
    boot_token = create_boot_token(
        user_id=str(session_payload["sub"]),
        scene=str(session_payload["scene"]),
        source=str(session_payload.get("source") or "oa_h5"),
        entry=str(session_payload.get("entry") or "official_account_menu"),
    )
    return {
        "user_id": str(session_payload["sub"]),
        "scene": str(session_payload["scene"]),
        "source": str(session_payload.get("source") or "oa_h5"),
        "entry": str(session_payload.get("entry") or "official_account_menu"),
        "boot_token": boot_token,
        "qwenpaw_base_url": _get_public_base_url(request),
    }


@router.post("/api/webapp/bootstrap", response_model=BootstrapResponse)
async def webapp_bootstrap(request: BootstrapRequest) -> BootstrapResponse:
    try:
        boot_payload = validate_boot_token(
            request.boot_token,
            expected_scene=request.scene,
        )
        user_id = str(boot_payload["sub"])
        scene_config = SceneRegistry().get(request.scene)
    except BootTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except UnknownSceneError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    conversation_id = uuid4().hex[:12]
    session_id = build_session_id(
        scene=request.scene,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    access_token = f"webapp-session-{conversation_id}"
    _ws_hub.register_token_context(
        access_token,
        {
            "agent_id": scene_config["agent_id"],
            "scene": request.scene,
            "source": str(boot_payload.get("source") or request.source),
            "entry": str(boot_payload.get("entry") or request.entry),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "session_id": session_id,
            "scene_config": scene_config,
            "ui_mode": str(
                scene_config.get("conversation_contract", {}).get("mode")
                or "chat"
            ),
            "conversation_contract": scene_config.get(
                "conversation_contract",
                {},
            ),
        },
    )
    return BootstrapResponse(
        access_token=access_token,
        user_id=user_id,
        conversation_id=conversation_id,
        session_id=session_id,
        ws_url=f"/api/webapp/chat/ws?token={access_token}",
        scene_config=scene_config,
    )


@router.get("/api/webapp/chat/history")
async def webapp_chat_history(request: Request, conversation_id: str) -> dict:
    token = _extract_token_from_request(request)
    context = _require_context_for_http(token, conversation_id)
    if not context:
        return {
            "conversation_id": conversation_id,
            "messages": [],
        }

    workspace = await request.app.state.multi_agent_manager.get_agent(
        context["agent_id"],
    )
    chat_id = await workspace.chat_manager.get_chat_id_by_session(
        context["session_id"],
        "webapp",
    )
    if not chat_id:
        return {
            "conversation_id": conversation_id,
            "messages": [],
        }

    state = await workspace.runner.session.get_session_state_dict(
        context["session_id"],
        context["user_id"],
        "webapp",
    )
    if not state:
        return {
            "conversation_id": conversation_id,
            "messages": [],
        }

    memory_state = state.get("agent", {}).get("memory", {})
    memory = InMemoryMemory()
    memory.load_state_dict(memory_state, strict=False)
    memories = await memory.get_memory(prepend_summary=True)
    runtime_messages = agentscope_msg_to_message(memories)
    messages = []
    for message in runtime_messages:
        parts = getattr(message, "content", None) or []
        text = "".join(
            getattr(part, "text", "")
            for part in parts
            if getattr(part, "type", None) == ContentType.TEXT
        )
        messages.append(
            {
                "id": str(getattr(message, "id", "") or ""),
                "role": str(getattr(message, "role", "") or ""),
                "text": text,
            },
        )
    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }


@router.post("/api/webapp/chat/stop")
async def webapp_chat_stop(request: Request, payload: dict) -> dict:
    conversation_id = str(payload.get("conversation_id") or "")
    token = str(payload.get("access_token") or "") or _extract_token_from_request(
        request,
    )
    context = _require_context_for_http(token, conversation_id)
    if not context:
        return {"ok": False}
    workspace = await request.app.state.multi_agent_manager.get_agent(
        context["agent_id"],
    )
    chat_id = await workspace.chat_manager.get_chat_id_by_session(
        context["session_id"],
        "webapp",
    )
    if not chat_id:
        return {"ok": False}
    stopped = await workspace.task_tracker.request_stop(chat_id)
    return {
        "ok": stopped,
    }


@router.websocket("/api/webapp/chat/ws")
async def webapp_chat_ws(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token", "")
    context = _ws_hub.get_token_context(token)
    if not token.startswith("webapp-session-") or not context:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await _ws_hub.connect(token, websocket)
    try:
        await _ws_hub.send_hello(websocket)
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            if message["type"] != "websocket.receive":
                continue
            text = message.get("text")
            if not text:
                continue
            payload = json.loads(text)
            if payload.get("type") != "user_message":
                continue
            await websocket.send_json(
                {
                    "type": "user_message_ack",
                    "conversation_id": context["conversation_id"],
                    "client_msg_id": payload.get("client_msg_id", ""),
                },
            )
            workspace = await websocket.app.state.multi_agent_manager.get_agent(
                context["agent_id"],
            )
            channel = await workspace.channel_manager.get_channel("webapp")
            if channel is None:
                await websocket.send_json(
                    {
                        "type": "assistant_error",
                        "conversation_id": context["conversation_id"],
                        "error": "webapp channel not available",
                    },
                )
                continue
            native_payload = {
                "channel_id": "webapp",
                "sender_id": context["user_id"],
                "text": str(payload.get("text") or ""),
                "meta": {
                    "scene": context["scene"],
                    "source": context["source"],
                    "entry": context["entry"],
                    "conversation_id": context["conversation_id"],
                    "session_id": context["session_id"],
                    "ui_mode": context.get("ui_mode", "chat"),
                    "conversation_contract": context.get(
                        "conversation_contract",
                        {},
                    ),
                },
            }
            chat = await workspace.chat_manager.get_or_create_chat(
                context["session_id"],
                context["user_id"],
                "webapp",
                name=str(payload.get("text") or "")[:10] or "New Chat",
            )
            queue, _ = await workspace.task_tracker.attach_or_start(
                chat.id,
                native_payload,
                channel.stream_one,
            )
            async for sse in workspace.task_tracker.stream_from_queue(
                queue,
                chat.id,
            ):
                data = _sse_data_to_payload(sse)
                if data is not None:
                    await websocket.send_json(data)
    except WebSocketDisconnect:
        await _ws_hub.disconnect(token, websocket)
    finally:
        await _ws_hub.disconnect(token, websocket)


def register_app_routes(app) -> None:
    app.include_router(router)


def _sse_data_to_payload(sse: str) -> dict | None:
    prefix = "data: "
    if not sse.startswith(prefix):
        return None
    body = sse[len(prefix) :].strip()
    if not body:
        return None
    return json.loads(body)


def _extract_token_from_request(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    token = request.query_params.get("token", "")
    return str(token or "")


def _require_context_for_http(
    token: str,
    conversation_id: str,
) -> dict | None:
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    context = _ws_hub.get_token_context(token)
    if not context:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if conversation_id and context.get("conversation_id") != conversation_id:
        raise HTTPException(status_code=403, detail="Conversation mismatch")
    return context


def _render_demo_html(
    *,
    scene: str,
    source: str,
    entry: str,
    boot_token: str,
    api_base: str,
) -> str:
    initial = json.dumps(
        {
            "scene": scene,
            "source": source,
            "entry": entry,
            "bootToken": boot_token,
            "apiBase": api_base,
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>商机研析 Demo</title>
  <style>
    :root {{
      --bg: #eef4fb;
      --panel: #ffffff;
      --ink: #10263f;
      --muted: #5f7288;
      --line: #d7e3f0;
      --accent: #2f6de0;
      --accent-soft: #dfeaff;
      --user: #ebf3ff;
      --bot: #ffffff;
      --shadow: 0 14px 34px rgba(33, 68, 119, 0.08);
      --radius: 24px;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Noto Serif SC", "Songti SC", serif;
      background: var(--bg);
      color: var(--ink);
    }}
    .shell {{
      min-height: 100dvh;
      max-width: 520px;
      margin: 0 auto;
      padding: 18px 16px calc(112px + env(safe-area-inset-bottom));
      position: relative;
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      padding: 8px 0 18px;
    }}
    .back {{
      position: absolute;
      left: 0;
      top: 4px;
      border: 0;
      background: transparent;
      color: var(--ink);
      font-size: 28px;
      line-height: 1;
      cursor: pointer;
    }}
    .title {{
      font-size: 20px;
      font-weight: 600;
      letter-spacing: 0;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 84px 1fr;
      gap: 16px;
      align-items: center;
      margin-bottom: 20px;
      padding: 16px 0 8px;
    }}
    .avatar {{
      width: 84px;
      height: 84px;
      border-radius: 50%;
      background: linear-gradient(180deg, #e6f0ff 0%, #d5e6ff 100%);
      display: grid;
      place-items: center;
      box-shadow: var(--shadow);
      font-size: 34px;
    }}
    .hero-copy h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.08;
      text-wrap: balance;
    }}
    .hero-copy p {{
      margin: 0;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
      font-size: 14px;
      color: var(--muted);
      line-height: 1.6;
      text-wrap: pretty;
    }}
    .controls {{
      background: rgba(255,255,255,0.8);
      backdrop-filter: blur(6px);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 14px;
      box-shadow: var(--shadow);
      margin-bottom: 18px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
    .controls summary {{
      cursor: pointer;
      color: var(--muted);
      font-weight: 600;
    }}
    .grid {{
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-size: 12px;
      color: var(--muted);
    }}
    input, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px 14px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      resize: vertical;
    }}
    textarea {{ min-height: 84px; }}
    .row {{
      display: flex;
      gap: 10px;
    }}
    .btn {{
      border: 0;
      border-radius: 16px;
      padding: 12px 16px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-weight: 600;
      transition: transform 160ms ease-out, opacity 160ms ease-out;
    }}
    .btn:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
    }}
    .btn:active {{
      transform: translateY(1px);
    }}
    .btn.secondary {{
      background: var(--accent-soft);
      color: var(--accent);
    }}
    .status {{
      margin-top: 10px;
      font-size: 12px;
      color: var(--muted);
    }}
    .suggestions {{
      display: grid;
      gap: 12px;
      margin-bottom: 18px;
    }}
    .chip {{
      border: 0;
      background: var(--panel);
      color: var(--ink);
      text-align: left;
      padding: 16px 18px;
      border-radius: 22px;
      box-shadow: var(--shadow);
      font-size: 15px;
      line-height: 1.45;
      cursor: pointer;
      text-wrap: pretty;
    }}
    .messages {{
      display: grid;
      gap: 12px;
      padding-bottom: 12px;
    }}
    .bubble {{
      max-width: 86%;
      padding: 14px 16px;
      border-radius: 22px;
      box-shadow: var(--shadow);
      line-height: 1.65;
      font-size: 15px;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .bubble.user {{
      margin-left: auto;
      background: var(--user);
      border-bottom-right-radius: 8px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
    .bubble.bot {{
      background: var(--bot);
      border-bottom-left-radius: 8px;
    }}
    .composer {{
      position: fixed;
      left: 50%;
      bottom: 0;
      transform: translateX(-50%);
      width: min(520px, 100%);
      padding: 12px 16px calc(14px + env(safe-area-inset-bottom));
      background: rgba(238, 244, 251, 0.96);
      border-top: 1px solid rgba(215, 227, 240, 0.9);
      backdrop-filter: blur(10px);
    }}
    .composer-card {{
      display: flex;
      align-items: flex-end;
      gap: 10px;
      background: #fff;
      border-radius: 24px;
      padding: 10px;
      box-shadow: var(--shadow);
      border: 1px solid var(--line);
    }}
    .composer textarea {{
      min-height: 24px;
      max-height: 132px;
      border: 0;
      padding: 10px 12px;
      background: transparent;
    }}
    .composer-actions {{
      display: grid;
      gap: 8px;
    }}
    .icon-btn {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 0;
      cursor: pointer;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 18px;
    }}
    .footnote {{
      text-align: center;
      margin-top: 10px;
      color: var(--muted);
      font-size: 11px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="topbar">
      <button class="back" type="button" aria-label="返回" onclick="history.back()">‹</button>
      <div class="title">商机研析 Demo</div>
    </div>

    <section class="hero">
      <div class="avatar" aria-hidden="true">✦</div>
      <div class="hero-copy">
        <h1 id="hero-title">商机智脑</h1>
        <p id="hero-subtitle">用最小 H5 页面直连现有 webapp Channel，快速验证公众号内 H5 的聊天问诊效果。</p>
      </div>
    </section>

    <details class="controls" open>
      <summary>连接配置</summary>
      <div class="grid">
        <label>QwenPaw API Base
          <input id="apiBase" placeholder="默认同源，例如 https://api.example.com" />
        </label>
        <label>Scene
          <input id="scene" placeholder="opportunity_insight" />
        </label>
        <label>Boot Token
          <textarea id="bootToken" placeholder="把 generate_webapp_boot_token.py 生成的 boot_token 粘贴到这里"></textarea>
        </label>
        <div class="row">
          <button id="connectBtn" class="btn" type="button">连接 Demo</button>
          <button id="historyBtn" class="btn secondary" type="button">恢复历史</button>
        </div>
        <div class="status" id="status">等待连接</div>
      </div>
    </details>

    <section class="suggestions" id="suggestions"></section>
    <section class="messages" id="messages"></section>
  </div>

  <div class="composer">
    <div class="composer-card">
      <textarea id="composer" placeholder="请输入客户背景、需求描述、会议纪要或商机线索"></textarea>
      <div class="composer-actions">
        <button id="sendBtn" class="icon-btn" type="button" aria-label="发送">➤</button>
        <button id="stopBtn" class="icon-btn" type="button" aria-label="停止生成">■</button>
      </div>
    </div>
    <div class="footnote">内容由 AI 生成 · 事件链包含 /api/webapp/bootstrap、assistant_delta、assistant_final</div>
  </div>

  <script>
    const initial = {initial};
    const state = {{
      accessToken: "",
      conversationId: "",
      ws: null,
      currentAssistant: null,
      sceneConfig: null,
      msgSeq: 0,
    }};

    const els = {{
      apiBase: document.getElementById("apiBase"),
      scene: document.getElementById("scene"),
      bootToken: document.getElementById("bootToken"),
      connectBtn: document.getElementById("connectBtn"),
      historyBtn: document.getElementById("historyBtn"),
      status: document.getElementById("status"),
      suggestions: document.getElementById("suggestions"),
      messages: document.getElementById("messages"),
      composer: document.getElementById("composer"),
      sendBtn: document.getElementById("sendBtn"),
      stopBtn: document.getElementById("stopBtn"),
      heroTitle: document.getElementById("hero-title"),
      heroSubtitle: document.getElementById("hero-subtitle"),
    }};

    els.apiBase.value = initial.apiBase || window.location.origin;
    els.scene.value = initial.scene || "opportunity_insight";
    els.bootToken.value = initial.bootToken || "";

    function setStatus(text) {{
      els.status.textContent = text;
    }}

    function normalizeBase(url) {{
      return (url || window.location.origin).replace(/\\/$/, "");
    }}

    function addBubble(role, text) {{
      const div = document.createElement("div");
      div.className = `bubble ${{role}}`;
      div.textContent = text;
      els.messages.appendChild(div);
      div.scrollIntoView({{ block: "end", behavior: "smooth" }});
      return div;
    }}

    function renderSuggestions(suggestions) {{
      els.suggestions.innerHTML = "";
      for (const suggestion of suggestions || []) {{
        const button = document.createElement("button");
        button.className = "chip";
        button.type = "button";
        button.textContent = suggestion;
        button.addEventListener("click", () => {{
          els.composer.value = suggestion;
          sendMessage();
        }});
        els.suggestions.appendChild(button);
      }}
    }}

    async function bootstrap() {{
      const apiBase = normalizeBase(els.apiBase.value);
      const payload = {{
        boot_token: els.bootToken.value.trim(),
        scene: els.scene.value.trim(),
        source: initial.source || "oa_h5",
        entry: initial.entry || "manual_demo",
      }};
      if (!payload.boot_token) {{
        setStatus("请先输入 boot_token");
        return;
      }}
      setStatus("正在 bootstrap...");
      const response = await fetch(`${{apiBase}}/api/webapp/bootstrap`, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload),
      }});
      if (!response.ok) {{
        const error = await response.text();
        setStatus(`bootstrap 失败: ${{response.status}}`);
        throw new Error(error);
      }}
      const data = await response.json();
      state.accessToken = data.access_token;
      state.conversationId = data.conversation_id;
      state.sceneConfig = data.scene_config;
      els.heroTitle.textContent = data.scene_config.title || "商机智脑";
      els.heroSubtitle.textContent = data.scene_config.welcome || "已连接";
      els.composer.placeholder = data.scene_config.placeholder || "请输入内容";
      renderSuggestions(data.scene_config.suggestions || []);
      setStatus("bootstrap 完成，正在建立连接...");
      await connectWs(apiBase, data.ws_url);
    }}

    async function connectWs(apiBase, wsUrl) {{
      if (state.ws) {{
        state.ws.close();
      }}
      const resolved = wsUrl.startsWith("ws")
        ? wsUrl
        : `${{apiBase.replace(/^http/, "ws")}}${{wsUrl}}`;
      state.ws = new WebSocket(resolved);
      state.ws.onopen = () => setStatus("WebSocket 已连接");
      state.ws.onmessage = (event) => handleServerEvent(JSON.parse(event.data));
      state.ws.onclose = () => setStatus("WebSocket 已关闭");
      state.ws.onerror = () => setStatus("WebSocket 错误");
    }}

    function handleServerEvent(event) {{
      if (event.type === "hello") {{
        setStatus("连接成功，可以开始问诊");
        return;
      }}
      if (event.type === "user_message_ack") {{
        setStatus("消息已送达，等待 RA-agent 回答...");
        return;
      }}
      if (event.type === "assistant_delta") {{
        if (!state.currentAssistant) {{
          state.currentAssistant = addBubble("bot", "");
        }}
        state.currentAssistant.textContent = event.accumulated_text || "";
        state.currentAssistant.scrollIntoView({{ block: "end", behavior: "smooth" }});
        return;
      }}
      if (event.type === "assistant_final") {{
        if (!state.currentAssistant) {{
          state.currentAssistant = addBubble("bot", event.text || "");
        }} else {{
          state.currentAssistant.textContent = event.text || state.currentAssistant.textContent;
        }}
        state.currentAssistant = null;
        setStatus("本轮回复完成");
        return;
      }}
      if (event.type === "assistant_error") {{
        state.currentAssistant = null;
        addBubble("bot", `错误：${{event.error || "未知错误"}}`);
        setStatus("回复失败");
      }}
    }}

    function sendMessage() {{
      const text = els.composer.value.trim();
      if (!text || !state.ws || state.ws.readyState !== WebSocket.OPEN) {{
        setStatus("请先连接 Demo");
        return;
      }}
      addBubble("user", text);
      state.currentAssistant = null;
      state.msgSeq += 1;
      state.ws.send(JSON.stringify({{
        type: "user_message",
        conversation_id: state.conversationId,
        client_msg_id: `m${{state.msgSeq}}`,
        text,
        scene: els.scene.value.trim(),
      }}));
      els.composer.value = "";
    }}

    async function restoreHistory() {{
      if (!state.accessToken || !state.conversationId) {{
        setStatus("请先连接 Demo");
        return;
      }}
      const apiBase = normalizeBase(els.apiBase.value);
      const response = await fetch(
        `${{apiBase}}/api/webapp/chat/history?conversation_id=${{encodeURIComponent(state.conversationId)}}`,
        {{
          headers: {{
            "Authorization": `Bearer ${{state.accessToken}}`,
          }},
        }},
      );
      const data = await response.json();
      els.messages.innerHTML = "";
      for (const message of data.messages || []) {{
        addBubble(message.role === "user" ? "user" : "bot", message.text || "");
      }}
      setStatus("历史已恢复");
    }}

    async function stopGeneration() {{
      if (!state.accessToken || !state.conversationId) {{
        setStatus("当前没有可停止的会话");
        return;
      }}
      const apiBase = normalizeBase(els.apiBase.value);
      const response = await fetch(`${{apiBase}}/api/webapp/chat/stop`, {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json",
          "Authorization": `Bearer ${{state.accessToken}}`,
        }},
        body: JSON.stringify({{
          conversation_id: state.conversationId,
          access_token: state.accessToken,
        }}),
      }});
      const data = await response.json();
      setStatus(data.ok ? "已发送停止请求" : "停止请求失败");
    }}

    els.connectBtn.addEventListener("click", () => bootstrap().catch((error) => {{
      console.error(error);
      addBubble("bot", `连接失败：${{error.message}}`);
    }}));
    els.historyBtn.addEventListener("click", () => restoreHistory().catch((error) => {{
      console.error(error);
      setStatus("恢复历史失败");
    }}));
    els.sendBtn.addEventListener("click", sendMessage);
    els.stopBtn.addEventListener("click", () => stopGeneration().catch((error) => {{
      console.error(error);
      setStatus("停止失败");
    }}));
    els.composer.addEventListener("keydown", (event) => {{
      if (event.key === "Enter" && !event.shiftKey) {{
        event.preventDefault();
        sendMessage();
      }}
    }});

    if (initial.bootToken) {{
      bootstrap().catch((error) => {{
        console.error(error);
        setStatus("自动连接失败，请手工检查 boot_token");
      }});
    }} else {{
      renderSuggestions([
        "我刚见完一个客户，帮我梳理这个商机该怎么继续跟",
        "客户提了AI诉求，但需求很模糊，帮我设计追问路径",
        "根据这段会议纪要，帮我判断预算、阶段和突破口"
      ]);
    }}
  </script>
</body>
</html>"""


def _redirect_response(url: str):
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=url, status_code=307)


def _render_demo_html_v2(
    *,
    scene: str,
    source: str,
    entry: str,
    boot_token: str,
    api_base: str,
) -> str:
    initial = json.dumps(
        {
            "scene": scene,
            "source": source,
            "entry": entry,
            "bootToken": boot_token,
            "apiBase": api_base,
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>商机研析 Demo</title>
  <style>
    :root {{
      --bg: #edf4ff;
      --panel: #ffffff;
      --panel-soft: rgba(255, 255, 255, 0.82);
      --ink: #14283f;
      --muted: #5b7188;
      --line: rgba(201, 217, 236, 0.92);
      --accent: #2c69e3;
      --accent-soft: #dce8ff;
      --accent-ink: #1448a7;
      --user: #ecf3ff;
      --bot: #ffffff;
      --status: #eff5ff;
      --shadow: 0 18px 42px rgba(45, 83, 129, 0.10);
      --shadow-soft: 0 10px 24px rgba(45, 83, 129, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Iowan Old Style", "Palatino Linotype", "Noto Serif SC", "Songti SC", serif;
      background:
        radial-gradient(circle at 88% 8%, rgba(255,255,255,0.92), transparent 22%),
        radial-gradient(circle at 12% 24%, rgba(223,238,255,0.82), transparent 28%),
        linear-gradient(180deg, #ecf4ff 0%, #f4f8fd 48%, #fbfdff 100%);
      overflow-x: hidden;
    }}
    body::before {{
      content: "";
      position: fixed;
      right: -90px;
      top: 120px;
      width: 280px;
      height: 180px;
      background:
        radial-gradient(circle at 28% 35%, rgba(188, 217, 255, 0.72), transparent 44%),
        radial-gradient(circle at 70% 48%, rgba(255,255,255,0.95), transparent 48%);
      opacity: 0.78;
      pointer-events: none;
    }}
    .shell {{
      min-height: 100dvh;
      max-width: 540px;
      margin: 0 auto;
      padding: 18px 18px calc(124px + env(safe-area-inset-bottom));
      position: relative;
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      padding: 10px 0 18px;
    }}
    .back {{
      position: absolute;
      left: 0;
      top: 2px;
      border: 0;
      background: transparent;
      color: var(--ink);
      font-size: 28px;
      line-height: 1;
      cursor: pointer;
    }}
    .title {{
      font-size: 20px;
      font-weight: 600;
    }}
    .hero-card {{
      position: relative;
      overflow: hidden;
      border-radius: 32px;
      padding: 24px 20px 22px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.90), rgba(255,255,255,0.76)),
        radial-gradient(circle at right top, rgba(186,219,255,0.85), transparent 38%);
      border: 1px solid rgba(255,255,255,0.7);
      box-shadow: var(--shadow);
      margin-bottom: 18px;
    }}
    .hero-card::after {{
      content: "";
      position: absolute;
      right: -40px;
      bottom: -24px;
      width: 210px;
      height: 124px;
      background:
        radial-gradient(circle at 28% 35%, rgba(188, 217, 255, 0.72), transparent 44%),
        radial-gradient(circle at 70% 48%, rgba(255,255,255,0.95), transparent 48%);
      opacity: 0.78;
      pointer-events: none;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 84px 1fr;
      gap: 18px;
      align-items: center;
      position: relative;
      z-index: 1;
    }}
    .avatar {{
      width: 84px;
      height: 84px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      border: 4px solid rgba(255,255,255,0.86);
      box-shadow: 0 12px 28px rgba(76, 123, 190, 0.24);
      background:
        radial-gradient(circle at 32% 28%, rgba(255,255,255,0.95), rgba(255,255,255,0.18) 40%),
        linear-gradient(180deg, #92d4ff 0%, #6ea9ff 100%);
      font-size: 34px;
    }}
    .hero-copy h1 {{
      margin: 0 0 10px;
      font-size: 29px;
      line-height: 1.1;
      text-wrap: balance;
    }}
    .hero-copy p {{
      margin: 0;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
      font-size: 14px;
      line-height: 1.65;
      color: var(--muted);
      text-wrap: pretty;
    }}
    .meta-strip {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 16px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
      position: relative;
      z-index: 1;
    }}
    .meta-tag,
    .status-chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(214, 227, 244, 0.96);
      background: rgba(255,255,255,0.82);
      box-shadow: var(--shadow-soft);
      font-size: 12px;
      color: var(--muted);
    }}
    .status-chip {{
      background: var(--status);
      color: var(--accent-ink);
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #91a7c0;
      flex: 0 0 auto;
    }}
    .status-chip.ready .status-dot {{ background: #3faa6a; }}
    .status-chip.error .status-dot {{ background: #d3535d; }}
    .controls {{
      background: var(--panel-soft);
      backdrop-filter: blur(6px);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 14px 14px 12px;
      box-shadow: var(--shadow-soft);
      margin-bottom: 18px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
    .controls summary {{
      cursor: pointer;
      color: var(--muted);
      font-weight: 600;
      list-style: none;
    }}
    .controls summary::-webkit-details-marker {{ display: none; }}
    .grid {{
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-size: 12px;
      color: var(--muted);
    }}
    input, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px 14px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      resize: vertical;
    }}
    textarea {{ min-height: 84px; }}
    .row {{
      display: flex;
      gap: 10px;
    }}
    .btn {{
      border: 0;
      border-radius: 16px;
      padding: 12px 16px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-weight: 600;
      transition: transform 160ms ease-out, opacity 160ms ease-out;
    }}
    .btn.secondary {{
      background: var(--accent-soft);
      color: var(--accent-ink);
    }}
    .btn:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}
    .btn:active {{ transform: translateY(1px); }}
    .status-note {{
      margin-top: 10px;
      font-size: 12px;
      color: var(--muted);
    }}
    .section-kicker {{
      margin: 0 0 10px;
      padding-left: 6px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
      font-size: 12px;
      color: var(--muted);
    }}
    .suggestions {{
      display: grid;
      gap: 12px;
      margin-bottom: 18px;
    }}
    .chip {{
      border: 1px solid rgba(228, 236, 247, 0.98);
      background: var(--panel);
      color: var(--ink);
      text-align: left;
      padding: 18px 18px;
      border-radius: 22px;
      box-shadow: var(--shadow-soft);
      font-size: 15px;
      line-height: 1.55;
      cursor: pointer;
      text-wrap: pretty;
    }}
    .messages {{
      display: grid;
      gap: 12px;
      padding-bottom: 12px;
    }}
    .bubble {{
      max-width: 86%;
      padding: 14px 16px;
      border-radius: 22px;
      box-shadow: var(--shadow-soft);
      line-height: 1.7;
      font-size: 15px;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .bubble.user {{
      margin-left: auto;
      background: var(--user);
      border-bottom-right-radius: 8px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
    .bubble.bot {{
      background: var(--bot);
      border-bottom-left-radius: 8px;
    }}
    .composer {{
      position: fixed;
      left: 50%;
      bottom: 0;
      transform: translateX(-50%);
      width: min(540px, 100%);
      padding: 12px 16px calc(14px + env(safe-area-inset-bottom));
      background: rgba(237, 244, 255, 0.94);
      border-top: 1px solid rgba(215, 227, 240, 0.9);
      backdrop-filter: blur(10px);
    }}
    .composer-card {{
      display: flex;
      align-items: flex-end;
      gap: 10px;
      background: #fff;
      border-radius: 24px;
      padding: 10px;
      box-shadow: var(--shadow);
      border: 1px solid var(--line);
    }}
    .composer textarea {{
      min-height: 24px;
      max-height: 132px;
      border: 0;
      padding: 10px 12px;
      background: transparent;
    }}
    .composer-actions {{
      display: grid;
      gap: 8px;
    }}
    .icon-btn {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 0;
      cursor: pointer;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 18px;
    }}
    .footnote {{
      text-align: center;
      margin-top: 10px;
      color: var(--muted);
      font-size: 11px;
      font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="topbar">
      <button class="back" type="button" aria-label="返回" onclick="history.back()">‹</button>
      <div class="title">商机研析 Demo</div>
    </div>

    <section class="hero-card">
      <div class="hero">
        <div class="avatar" aria-hidden="true">✦</div>
        <div class="hero-copy">
          <h1 id="hero-title">商机智脑</h1>
          <p id="hero-subtitle">商机智脑上线，帮你快速识别客户需求、项目机会与推进路径</p>
        </div>
      </div>
      <div class="meta-strip">
        <div class="meta-tag">公众号内 H5 体验</div>
        <div class="status-chip" id="statusChip">
          <span class="status-dot"></span>
          <span id="status">等待连接</span>
        </div>
      </div>
    </section>

    <details class="controls">
      <summary>连接配置（内部试用）</summary>
      <div class="grid">
        <label>QwenPaw API Base
          <input id="apiBase" placeholder="默认同源，例如 https://api.example.com" />
        </label>
        <label>Scene
          <input id="scene" placeholder="opportunity_insight" />
        </label>
        <label>Boot Token
          <textarea id="bootToken" placeholder="把 generate_webapp_boot_token.py 生成的 boot_token 粘贴到这里"></textarea>
        </label>
        <div class="row">
          <button id="connectBtn" class="btn" type="button">连接 Demo</button>
          <button id="historyBtn" class="btn secondary" type="button">恢复历史</button>
        </div>
        <div class="status-note">如果 URL 中已经带了 boot_token，页面会自动建立连接。</div>
      </div>
    </details>

    <p class="section-kicker">你可以直接点下面的问题开始试，也可以自己输入商机线索。</p>
    <section class="suggestions" id="suggestions"></section>
    <section class="messages" id="messages"></section>
  </div>

  <div class="composer">
    <div class="composer-card">
      <textarea id="composer" placeholder="请输入客户背景、需求描述、会议纪要或商机线索"></textarea>
      <div class="composer-actions">
        <button id="sendBtn" class="icon-btn" type="button" aria-label="发送">➤</button>
        <button id="stopBtn" class="icon-btn" type="button" aria-label="停止生成">■</button>
      </div>
    </div>
    <div class="footnote">内容由 AI 生成 · 事件链包含 /api/webapp/bootstrap、assistant_delta、assistant_final</div>
  </div>

  <script>
    const initial = {initial};
    const state = {{
      accessToken: "",
      conversationId: "",
      ws: null,
      currentAssistant: null,
      sceneConfig: null,
      msgSeq: 0,
    }};

    const els = {{
      apiBase: document.getElementById("apiBase"),
      scene: document.getElementById("scene"),
      bootToken: document.getElementById("bootToken"),
      connectBtn: document.getElementById("connectBtn"),
      historyBtn: document.getElementById("historyBtn"),
      status: document.getElementById("status"),
      statusChip: document.getElementById("statusChip"),
      suggestions: document.getElementById("suggestions"),
      messages: document.getElementById("messages"),
      composer: document.getElementById("composer"),
      sendBtn: document.getElementById("sendBtn"),
      stopBtn: document.getElementById("stopBtn"),
      heroTitle: document.getElementById("hero-title"),
      heroSubtitle: document.getElementById("hero-subtitle"),
    }};

    els.apiBase.value = initial.apiBase || window.location.origin;
    els.scene.value = initial.scene || "opportunity_insight";
    els.bootToken.value = initial.bootToken || "";

    function setStatus(text) {{
      els.status.textContent = text;
    }}

    function setStatusTone(kind) {{
      els.statusChip.classList.remove("ready", "error");
      if (kind) {{
        els.statusChip.classList.add(kind);
      }}
    }}

    function normalizeBase(url) {{
      return (url || window.location.origin).replace(/\\/$/, "");
    }}

    function addBubble(role, text) {{
      const div = document.createElement("div");
      div.className = `bubble ${{role}}`;
      div.textContent = text;
      els.messages.appendChild(div);
      div.scrollIntoView({{ block: "end", behavior: "smooth" }});
      return div;
    }}

    function renderSuggestions(suggestions) {{
      els.suggestions.innerHTML = "";
      for (const suggestion of suggestions || []) {{
        const button = document.createElement("button");
        button.className = "chip";
        button.type = "button";
        button.textContent = suggestion;
        button.addEventListener("click", () => {{
          els.composer.value = suggestion;
          sendMessage();
        }});
        els.suggestions.appendChild(button);
      }}
    }}

    async function bootstrap() {{
      const apiBase = normalizeBase(els.apiBase.value);
      const payload = {{
        boot_token: els.bootToken.value.trim(),
        scene: els.scene.value.trim(),
        source: initial.source || "oa_h5",
        entry: initial.entry || "manual_demo",
      }};
      if (!payload.boot_token) {{
        setStatus("请先输入 boot_token");
        setStatusTone("error");
        return;
      }}
      setStatus("正在 bootstrap...");
      setStatusTone("");
      const response = await fetch(`${{apiBase}}/api/webapp/bootstrap`, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload),
      }});
      if (!response.ok) {{
        const error = await response.text();
        setStatus(`bootstrap 失败: ${{response.status}}`);
        setStatusTone("error");
        throw new Error(error);
      }}
      const data = await response.json();
      state.accessToken = data.access_token;
      state.conversationId = data.conversation_id;
      state.sceneConfig = data.scene_config;
      els.heroTitle.textContent = data.scene_config.title || "商机智脑";
      els.heroSubtitle.textContent = data.scene_config.welcome || "商机智脑上线，帮你快速识别客户需求、项目机会与推进路径";
      els.composer.placeholder = data.scene_config.placeholder || "请输入内容";
      renderSuggestions(data.scene_config.suggestions || []);
      setStatus("bootstrap 完成，正在建立连接...");
      await connectWs(apiBase, data.ws_url);
    }}

    async function connectWs(apiBase, wsUrl) {{
      if (state.ws) {{
        state.ws.close();
      }}
      const resolved = wsUrl.startsWith("ws")
        ? wsUrl
        : `${{apiBase.replace(/^http/, "ws")}}${{wsUrl}}`;
      state.ws = new WebSocket(resolved);
      state.ws.onopen = () => {{
        setStatus("WebSocket 已连接");
        setStatusTone("ready");
      }};
      state.ws.onmessage = (event) => handleServerEvent(JSON.parse(event.data));
      state.ws.onclose = () => {{
        setStatus("WebSocket 已关闭");
        setStatusTone("");
      }};
      state.ws.onerror = () => {{
        setStatus("WebSocket 错误");
        setStatusTone("error");
      }};
    }}

    function handleServerEvent(event) {{
      if (event.type === "hello") {{
        setStatus("连接成功，可以开始问诊");
        setStatusTone("ready");
        return;
      }}
      if (event.type === "user_message_ack") {{
        setStatus("消息已送达，等待 RA-agent 回答...");
        return;
      }}
      if (event.type === "assistant_delta") {{
        if (!state.currentAssistant) {{
          state.currentAssistant = addBubble("bot", "");
        }}
        state.currentAssistant.textContent = event.accumulated_text || "";
        state.currentAssistant.scrollIntoView({{ block: "end", behavior: "smooth" }});
        return;
      }}
      if (event.type === "assistant_final") {{
        if (!state.currentAssistant) {{
          state.currentAssistant = addBubble("bot", event.text || "");
        }} else {{
          state.currentAssistant.textContent = event.text || state.currentAssistant.textContent;
        }}
        state.currentAssistant = null;
        setStatus("本轮回复完成");
        setStatusTone("ready");
        return;
      }}
      if (event.type === "assistant_error") {{
        state.currentAssistant = null;
        addBubble("bot", `错误：${{event.error || "未知错误"}}`);
        setStatus("回复失败");
        setStatusTone("error");
      }}
    }}

    function sendMessage() {{
      const text = els.composer.value.trim();
      if (!text || !state.ws || state.ws.readyState !== WebSocket.OPEN) {{
        setStatus("请先连接 Demo");
        setStatusTone("error");
        return;
      }}
      addBubble("user", text);
      state.currentAssistant = null;
      state.msgSeq += 1;
      state.ws.send(JSON.stringify({{
        type: "user_message",
        conversation_id: state.conversationId,
        client_msg_id: `m${{state.msgSeq}}`,
        text,
        scene: els.scene.value.trim(),
      }}));
      els.composer.value = "";
    }}

    async function restoreHistory() {{
      if (!state.accessToken || !state.conversationId) {{
        setStatus("请先连接 Demo");
        setStatusTone("error");
        return;
      }}
      const apiBase = normalizeBase(els.apiBase.value);
      const response = await fetch(
        `${{apiBase}}/api/webapp/chat/history?conversation_id=${{encodeURIComponent(state.conversationId)}}`,
        {{
          headers: {{
            "Authorization": `Bearer ${{state.accessToken}}`,
          }},
        }},
      );
      const data = await response.json();
      els.messages.innerHTML = "";
      for (const message of data.messages || []) {{
        addBubble(message.role === "user" ? "user" : "bot", message.text || "");
      }}
      setStatus("历史已恢复");
      setStatusTone("ready");
    }}

    async function stopGeneration() {{
      if (!state.accessToken || !state.conversationId) {{
        setStatus("当前没有可停止的会话");
        setStatusTone("error");
        return;
      }}
      const apiBase = normalizeBase(els.apiBase.value);
      const response = await fetch(`${{apiBase}}/api/webapp/chat/stop`, {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json",
          "Authorization": `Bearer ${{state.accessToken}}`,
        }},
        body: JSON.stringify({{
          conversation_id: state.conversationId,
          access_token: state.accessToken,
        }}),
      }});
      const data = await response.json();
      setStatus(data.ok ? "已发送停止请求" : "停止请求失败");
      setStatusTone(data.ok ? "ready" : "error");
    }}

    els.connectBtn.addEventListener("click", () => bootstrap().catch((error) => {{
      console.error(error);
      addBubble("bot", `连接失败：${{error.message}}`);
    }}));
    els.historyBtn.addEventListener("click", () => restoreHistory().catch((error) => {{
      console.error(error);
      setStatus("恢复历史失败");
      setStatusTone("error");
    }}));
    els.sendBtn.addEventListener("click", sendMessage);
    els.stopBtn.addEventListener("click", () => stopGeneration().catch((error) => {{
      console.error(error);
      setStatus("停止失败");
      setStatusTone("error");
    }}));
    els.composer.addEventListener("keydown", (event) => {{
      if (event.key === "Enter" && !event.shiftKey) {{
        event.preventDefault();
        sendMessage();
      }}
    }});

    if (initial.bootToken) {{
      bootstrap().catch((error) => {{
        console.error(error);
        setStatus("自动连接失败，请手工检查 boot_token");
        setStatusTone("error");
      }});
    }} else {{
      renderSuggestions([
        "我刚见完一个客户，帮我梳理这个商机该怎么继续跟",
        "客户提了AI诉求，但需求很模糊，帮我设计追问路径",
        "根据这段会议纪要，帮我判断预算、阶段和突破口"
      ]);
    }}
  </script>
</body>
</html>"""


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing required env: {name}")
    return value


def _get_public_base_url(request: Request) -> str:
    configured = os.environ.get("QWENPAW_WEBAPP_PUBLIC_BASE_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _get_h5_base_url(request: Request) -> str:
    configured = os.environ.get("QWENPAW_WEBAPP_H5_BASE_URL", "").strip()
    if configured:
        return configured
    return f"{_get_public_base_url(request)}/api/webapp/demo"


def _get_oa_scope() -> str:
    return os.environ.get("QWENPAW_WECHAT_OA_SCOPE", "snsapi_base").strip() or "snsapi_base"


def _is_oa_dev_mode() -> bool:
    return os.environ.get("QWENPAW_WECHAT_OA_DEV_MODE", "").lower() in {
        "1",
        "true",
        "yes",
    }


def _map_openid_to_user_id(openid: str) -> str:
    return f"wechat_oa:{openid}"


async def _exchange_wechat_oauth_code(code: str) -> dict[str, str]:
    app_id = _get_required_env("QWENPAW_WECHAT_OA_APP_ID")
    app_secret = _get_required_env("QWENPAW_WECHAT_OA_APP_SECRET")
    params = {
        "appid": app_id,
        "secret": app_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.weixin.qq.com/sns/oauth2/access_token",
            params=params,
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errcode"):
        raise HTTPException(status_code=502, detail=f"WeChat OAuth exchange failed: {payload}")
    return {
        "openid": str(payload.get("openid") or ""),
        "unionid": str(payload.get("unionid") or ""),
    }
