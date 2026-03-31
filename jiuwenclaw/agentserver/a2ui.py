"""A2UI (v0.9) message helpers and parsers."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

A2UI_VERSION = "v0.9"
A2UI_BASIC_CATALOG_REMOTE = "https://a2ui.org/specification/v0_9/basic_catalog.json"
A2UI_BASIC_CATALOG_LOCAL = "/a2ui/basic_catalog.v0_9.json"
A2UI_TEXT_DELIMITER = "```a2ui-jsonl"


def resolve_catalog_id(config: dict[str, Any] | None = None) -> str:
    """Resolve default catalog id: local by default, optional remote override."""
    cfg = config or {}
    a2ui_cfg = cfg.get("a2ui", {}) if isinstance(cfg, dict) else {}
    source = str(
        os.getenv("JIUWENCLAW_A2UI_CATALOG_SOURCE")
        or a2ui_cfg.get("catalog_source")
        or "local"
    ).strip().lower()
    remote_url = str(
        os.getenv("JIUWENCLAW_A2UI_CATALOG_URL")
        or a2ui_cfg.get("catalog_url")
        or A2UI_BASIC_CATALOG_REMOTE
    ).strip()
    if source == "remote":
        return remote_url or A2UI_BASIC_CATALOG_REMOTE
    return A2UI_BASIC_CATALOG_LOCAL


def resolve_allow_catalog_ids(config: dict[str, Any] | None = None) -> set[str]:
    cfg = config or {}
    a2ui_cfg = cfg.get("a2ui", {}) if isinstance(cfg, dict) else {}
    ids = {
        A2UI_BASIC_CATALOG_LOCAL,
        A2UI_BASIC_CATALOG_REMOTE,
        resolve_catalog_id(cfg),
    }
    extra = a2ui_cfg.get("allowed_catalog_ids", [])
    if isinstance(extra, list):
        ids.update(str(item).strip() for item in extra if str(item).strip())
    return ids


def _parse_json_line(line: str) -> dict[str, Any] | None:
    text = line.strip()
    if not text.startswith("{") or not text.endswith("}"):
        return None
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    if (
        "createSurface" in parsed
        or "updateComponents" in parsed
        or "updateDataModel" in parsed
        or "deleteSurface" in parsed
    ):
        return parsed
    return None


def extract_a2ui_jsonl_lines(raw_text: str) -> list[str]:
    """Extract valid A2UI JSONL lines from plain LLM text output."""
    text = (raw_text or "").strip()
    if not text:
        return []

    fenced_pattern = re.compile(r"```a2ui-jsonl\s*(.*?)```", re.IGNORECASE | re.DOTALL)
    fenced_match = fenced_pattern.search(text)
    candidate_block = fenced_match.group(1) if fenced_match else text
    lines = [line.strip() for line in candidate_block.splitlines() if line.strip()]
    valid_lines: list[str] = []
    for line in lines:
        payload = _parse_json_line(line)
        if payload is None:
            continue
        if "version" not in payload:
            payload["version"] = A2UI_VERSION
        valid_lines.append(json.dumps(payload, ensure_ascii=False))
    return valid_lines


def is_a2ui_text(raw_text: str) -> bool:
    """Whether text likely contains an A2UI JSONL payload."""
    if not raw_text:
        return False
    if A2UI_TEXT_DELIMITER in raw_text.lower():
        return True
    return len(extract_a2ui_jsonl_lines(raw_text)) > 0


@dataclass
class A2UIResponseBuilder:
    """Builds A2UI v0.9 JSONL responses with basic validation."""

    surface_id: str = "main"
    catalog_id: str = A2UI_BASIC_CATALOG_LOCAL
    allow_catalog_ids: set[str] = field(
        default_factory=lambda: {
            A2UI_BASIC_CATALOG_LOCAL,
            A2UI_BASIC_CATALOG_REMOTE,
        }
    )
    messages: list[dict[str, Any]] = field(default_factory=list)

    def create_surface(self, send_data_model: bool = False, theme: dict[str, Any] | None = None) -> "A2UIResponseBuilder":
        if self.catalog_id not in self.allow_catalog_ids:
            raise ValueError(f"catalog_id not allowed: {self.catalog_id}")
        message: dict[str, Any] = {
            "version": A2UI_VERSION,
            "createSurface": {
                "surfaceId": self.surface_id,
                "catalogId": self.catalog_id,
            },
        }
        if send_data_model:
            message["createSurface"]["sendDataModel"] = True
        if theme:
            message["createSurface"]["theme"] = dict(theme)
        self.messages.append(message)
        return self

    def update_components(self, components: list[dict[str, Any]]) -> "A2UIResponseBuilder":
        message = {
            "version": A2UI_VERSION,
            "updateComponents": {
                "surfaceId": self.surface_id,
                "components": components,
            },
        }
        self.messages.append(message)
        return self

    def create_component(
        self,
        component_id: str,
        component_type: str,
        *,
        props: dict[str, Any] | None = None,
    ) -> "A2UIResponseBuilder":
        """Compatibility helper.

        A2UI v0.9 uses `updateComponents`; this helper maps legacy call sites
        to a single-item `updateComponents` payload to reduce migration impact.
        """
        return self.update_components(
            [
                {
                    "id": component_id,
                    "component": {
                        component_type: props or {},
                    },
                }
            ]
        )

    def update_data_model(self, data_model: dict[str, Any]) -> "A2UIResponseBuilder":
        message = {
            "version": A2UI_VERSION,
            "updateDataModel": {
                "surfaceId": self.surface_id,
                "dataModel": data_model,
            },
        }
        self.messages.append(message)
        return self

    def delete_surface(self) -> "A2UIResponseBuilder":
        message = {
            "version": A2UI_VERSION,
            "deleteSurface": {
                "surfaceId": self.surface_id,
            },
        }
        self.messages.append(message)
        return self

    def to_jsonl_lines(self) -> list[str]:
        return [json.dumps(msg, ensure_ascii=False) for msg in self.messages]
