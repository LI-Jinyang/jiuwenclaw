import json

from jiuwenclaw.agentserver.a2ui import (
    A2UI_BASIC_CATALOG,
    A2UIResponseBuilder,
    extract_a2ui_jsonl_lines,
)
from jiuwenclaw.agentserver.interface import AgentServerInterface


class _Chunk:
    def __init__(self, chunk_type: str, payload):
        self.type = chunk_type
        self.payload = payload


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


def test_parse_stream_chunk_maps_a2ui_event():
    chunk = _Chunk(
        "answer",
        {
            "output": {
                "output": """```a2ui-jsonl
{"createSurface":{"surfaceId":"main","catalogId":"https://a2ui.org/specification/v0_9/basic_catalog.json"}}
```""",
                "chunked": False,
            }
        },
    )
    payload = AgentServerInterface._parse_stream_chunk(chunk)
    assert payload is not None
    assert payload["event_type"] == "chat.a2ui"
    assert payload["is_final"] is True
