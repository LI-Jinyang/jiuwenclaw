"""A2UI feature module: keeps A2UI-specific logic isolated from core agent flow."""

from __future__ import annotations

import os
from typing import Any

from jiuwenclaw.agentserver.a2ui import (
    A2UI_BASIC_CATALOG_LOCAL,
    A2UI_BASIC_CATALOG_REMOTE,
    A2UIResponseBuilder,
    extract_a2ui_jsonl_lines,
    is_a2ui_text,
    resolve_allow_catalog_ids,
    resolve_catalog_id,
)


def detect_a2ui_jsonl(raw_text: str) -> list[str]:
    """Parse JSONL lines when text contains A2UI payload, otherwise empty."""
    if not is_a2ui_text(raw_text):
        return []
    return extract_a2ui_jsonl_lines(raw_text)


def is_a2ui_demo_enabled(query: str, params: dict[str, Any], config_base: dict[str, Any]) -> bool:
    env_enabled = os.getenv("JIUWENCLAW_A2UI_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}
    cfg_enabled = bool((config_base.get("a2ui", {}) or {}).get("demo_enabled", False))
    req_enabled = bool(params.get("a2ui_demo", False))
    slash_enabled = (query or "").strip().lower().startswith("/a2ui-demo")
    return env_enabled or cfg_enabled or req_enabled or slash_enabled


def build_a2ui_demo_lines(query: str, config_base: dict[str, Any] | None = None) -> list[str]:
    trimmed = (query or "").strip()
    if trimmed.startswith("/a2ui-demo"):
        trimmed = trimmed[len("/a2ui-demo"):].strip()
    description = trimmed or "这是一个用于验证 A2UI 集成效果的演示响应。"
    builder = A2UIResponseBuilder(
        catalog_id=resolve_catalog_id(config_base),
        allow_catalog_ids=resolve_allow_catalog_ids(config_base),
    )
    components = [
        {"id": "root", "component": {"Card": {"title": {"literalString": "A2UI Demo"}, "child": "desc"}}},
        {"id": "desc", "component": {"Text": {"text": {"literalString": description}}}},
        {"id": "actions", "component": {"Row": {"children": {"explicitList": ["btn_confirm", "btn_cancel"]}}}},
        {"id": "btn_confirm", "component": {"Button": {"label": {"literalString": "确认"}}}},
        {"id": "btn_cancel", "component": {"Button": {"label": {"literalString": "取消"}}}},
    ]
    return builder.create_surface().update_components(components).to_jsonl_lines()


def build_a2ui_prompt(language: str) -> str:
    """Prompt snippet dedicated to A2UI protocol guidance."""
    if language == "zh":
        template = """## A2UI 生成式 UI 输出规范（v0.9）

当任务更适合结构化交互时（表单收集、可点击按钮、表格、结构化结果、图表卡片），优先输出 A2UI；简单问答、问候、解释性回答使用普通文本。

### 输出协议
- A2UI 必须使用 JSONL（每行一个 JSON 对象）。
- 合法消息类型只有：`createSurface` / `updateComponents` / `updateDataModel` / `deleteSurface`。
- 第一行必须是 `createSurface`，随后通常发送 `updateComponents`（必要时再发 `updateDataModel`）。
- 默认使用本地 catalog：`__A2UI_LOCAL_CATALOG__`（可按配置切换在线 catalog）。
- 仅允许输出受信任 catalog 中的组件，不允许输出 HTML / JS / 可执行代码。

### v0.9 关键 schema（必须遵守）
- `createSurface`: `{"version":"v0.9","createSurface":{"surfaceId":"...","catalogId":"..."}}`
- `updateComponents`: `{"version":"v0.9","updateComponents":{"surfaceId":"...","components":[{"id":"root","component":{"Text":{...}}}]}}`
- `updateDataModel`: `{"version":"v0.9","updateDataModel":{"surfaceId":"...","dataModel":{...}}}`
- `deleteSurface`: `{"version":"v0.9","deleteSurface":{"surfaceId":"..."}}`

### 传输约定（用于网关识别）
```a2ui-jsonl
{"version":"v0.9","createSurface":{"surfaceId":"main","catalogId":"__A2UI_LOCAL_CATALOG__"}}
{"version":"v0.9","updateComponents":{"surfaceId":"main","components":[{"id":"root","component":{"Text":{"text":{"literalString":"Result"}}}}]}}
{"version":"v0.9","updateDataModel":{"surfaceId":"main","dataModel":{"status":"ok"}}}
```
"""
        return template.replace("__A2UI_LOCAL_CATALOG__", A2UI_BASIC_CATALOG_LOCAL)
    template = """## A2UI Generative UI output rules (v0.9)

Prefer A2UI when the task benefits from structured interaction (forms, clickable actions, tables, cards/charts). Use plain text for simple Q&A, greetings, and explanations.

### Protocol
- A2UI must be JSONL (one JSON object per line).
- Valid message types are only: `createSurface` / `updateComponents` / `updateDataModel` / `deleteSurface`.
- First line must be `createSurface`, then usually `updateComponents` (and `updateDataModel` when needed).
- Default to local catalog: `__A2UI_LOCAL_CATALOG__` (config may switch to remote catalog such as `__A2UI_REMOTE_CATALOG__`).
- Only use trusted catalog components; never output HTML/JS/executable code.

### Required v0.9 schema shape
- `createSurface`: `{"version":"v0.9","createSurface":{"surfaceId":"...","catalogId":"..."}}`
- `updateComponents`: `{"version":"v0.9","updateComponents":{"surfaceId":"...","components":[{"id":"root","component":{"Text":{...}}}]}}`
- `updateDataModel`: `{"version":"v0.9","updateDataModel":{"surfaceId":"...","dataModel":{...}}}`
- `deleteSurface`: `{"version":"v0.9","deleteSurface":{"surfaceId":"..."}}`

### Transport signal
```a2ui-jsonl
{"version":"v0.9","createSurface":{"surfaceId":"main","catalogId":"__A2UI_LOCAL_CATALOG__"}}
{"version":"v0.9","updateComponents":{"surfaceId":"main","components":[{"id":"root","component":{"Text":{"text":{"literalString":"Result"}}}}]}}
{"version":"v0.9","updateDataModel":{"surfaceId":"main","dataModel":{"status":"ok"}}}
```
"""
    return (
        template
        .replace("__A2UI_LOCAL_CATALOG__", A2UI_BASIC_CATALOG_LOCAL)
        .replace("__A2UI_REMOTE_CATALOG__", A2UI_BASIC_CATALOG_REMOTE)
    )

