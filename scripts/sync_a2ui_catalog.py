#!/usr/bin/env python3
"""Download A2UI basic catalog to local public assets."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

REMOTE_URL = "https://a2ui.org/specification/v0_9/basic_catalog.json"
TARGET_PATH = Path(__file__).resolve().parents[1] / "jiuwenclaw" / "web" / "public" / "a2ui" / "basic_catalog.v0_9.json"


def main() -> None:
    with urllib.request.urlopen(REMOTE_URL, timeout=30) as resp:
        data = resp.read()
    parsed = json.loads(data.decode("utf-8"))
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"catalog synced: {TARGET_PATH}")


if __name__ == "__main__":
    main()
