import json

from jiuwenclaw.agentserver.a2ui import (
    A2UI_BASIC_CATALOG,
    A2UIResponseBuilder,
    extract_a2ui_jsonl_lines,
    is_a2ui_text,
)


def test_a2ui_response_builder_minimal_payload():
    builder = A2UIResponseBuilder()
    lines = (
        builder.create_surface()
        .create_component("c1", "Card", props={"title": "Result"})
        .to_jsonl_lines()
    )
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["createSurface"]["catalogId"] == A2UI_BASIC_CATALOG
    assert second["createComponent"]["type"] == "Card"


def test_extract_a2ui_jsonl_lines_from_fenced_block():
    raw = """```a2ui-jsonl
{"createSurface":{"surfaceId":"main","catalogId":"https://a2ui.org/specification/v0_9/basic_catalog.json"}}
{"createComponent":{"componentId":"c1","surfaceId":"main","parentId":null,"type":"Card","props":{"title":"ok"}}}
```"""
    lines = extract_a2ui_jsonl_lines(raw)
    assert len(lines) == 2
    assert json.loads(lines[0])["version"] == "v0.9"


def test_is_a2ui_text_detects_fenced_payload():
    raw = """```a2ui-jsonl
{"createSurface":{"surfaceId":"main","catalogId":"https://a2ui.org/specification/v0_9/basic_catalog.json"}}
```"""
    assert is_a2ui_text(raw) is True
