from jiuwenclaw.agentserver.features.a2ui_feature import (
    build_a2ui_demo_lines,
    build_a2ui_prompt,
    detect_a2ui_jsonl,
    is_a2ui_demo_enabled,
)


def test_detect_a2ui_jsonl_with_update_components():
    raw = """```a2ui-jsonl
{"createSurface":{"surfaceId":"main","catalogId":"/a2ui/basic_catalog.v0_9.json"}}
{"updateComponents":{"surfaceId":"main","components":[{"id":"root","component":{"Text":{"text":{"literalString":"ok"}}}}]}}
```"""
    lines = detect_a2ui_jsonl(raw)
    assert len(lines) == 2


def test_build_a2ui_demo_lines_returns_v09_messages():
    lines = build_a2ui_demo_lines("/a2ui-demo test")
    joined = "\n".join(lines)
    assert '"createSurface"' in joined
    assert '"updateComponents"' in joined


def test_is_a2ui_demo_enabled_from_slash_command():
    assert is_a2ui_demo_enabled("/a2ui-demo", {}, {"a2ui": {}}) is True


def test_build_a2ui_prompt_mentions_message_types():
    prompt = build_a2ui_prompt("zh")
    assert "updateDataModel" in prompt
    assert "deleteSurface" in prompt
