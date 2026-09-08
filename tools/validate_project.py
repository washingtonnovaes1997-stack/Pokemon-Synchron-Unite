#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "game" / "project.json"


def fail(message: str) -> None:
    raise SystemExit(f"[validate] ERROR: {message}")


def main() -> None:
    if not CONFIG.exists():
        fail("game/project.json is missing")

    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in game/project.json: {exc}")

    required = ["project_name", "engine", "regions"]
    for key in required:
        if key not in data:
            fail(f"missing required field: {key}")

    if not isinstance(data["regions"], list):
        fail("regions must be a list")

    print(f"[validate] Project: {data['project_name']}")
    print(f"[validate] Engine: {data['engine']}")
    print(f"[validate] Regions defined: {len(data['regions'])}")
    print("[validate] Foundation checks passed.")


if __name__ == "__main__":
    main()
