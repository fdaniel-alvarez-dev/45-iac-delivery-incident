#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_MARKERS = ("TODO:", "TBD", "PLACEHOLDER")


def iter_text_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for base, dirs, files in os.walk(root):
        if ".git" in dirs:
            dirs.remove(".git")
        if "artifacts" in dirs:
            dirs.remove("artifacts")
        if ".venv" in dirs:
            dirs.remove(".venv")
        for name in files:
            p = Path(base) / name
            if p.name == "AGENTS.md" or p.name.startswith("AGENTS") and p.suffix == ".md":
                continue
            if p.resolve() == Path(__file__).resolve():
                continue
            if p.suffix in {".py", ".md", ".yml", ".yaml", ".json", ".txt", ""}:
                paths.append(p)
    paths.sort()
    return paths


def main() -> int:
    offenders: list[str] = []
    for path in iter_text_files(REPO_ROOT):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)} contains '{marker}'")

    if offenders:
        print("Lint failed: forbidden markers found:")
        for line in offenders:
            print(f"- {line}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
