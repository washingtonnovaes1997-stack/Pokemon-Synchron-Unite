#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_overlay(project: Path, engine: Path) -> int:
    overlay = project / "overlay"
    if not overlay.exists():
        print("[overlay] No overlay directory yet; base engine will be built unchanged.")
        return 0

    copied = 0
    for src in overlay.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(overlay)
        dst = engine / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[overlay] {rel}")
        copied += 1
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Pokemon Synchron Unite files to pokeemerald-expansion")
    parser.add_argument("--project", default=".")
    parser.add_argument("--engine", required=True)
    args = parser.parse_args()

    project = Path(args.project).resolve()
    engine = Path(args.engine).resolve()
    if not engine.exists():
        raise SystemExit(f"Engine directory not found: {engine}")

    copied = copy_overlay(project, engine)
    print(f"[overlay] Complete: {copied} file(s) applied.")


if __name__ == "__main__":
    main()
