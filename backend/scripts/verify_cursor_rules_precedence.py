#!/usr/bin/env python3
"""Verify SmartCRM commit-ops canon is present and consistent."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AGENTS = REPO / "AGENTS.md"
COMMIT_OPS = REPO / ".cursor" / "rules" / "smartcrm-commit-ops.mdc"
CONFLICT_CHECK = REPO / "backend" / "scripts" / "check_rules_commit_conflict.py"

REQUIRED_PHRASES = (
    "git commit",
    "SESSION_STATE",
    "push",
)


def main() -> int:
    errors: list[str] = []

    for path in (AGENTS, COMMIT_OPS):
        if not path.is_file():
            errors.append(f"MISSING: {path.relative_to(REPO)}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                errors.append(f"{path.name}: нет фразы «{phrase}»")

    if COMMIT_OPS.is_file():
        head = COMMIT_OPS.read_text(encoding="utf-8").splitlines()[:6]
        if not any("alwaysApply: true" in line for line in head):
            errors.append("smartcrm-commit-ops.mdc: нет alwaysApply: true")

    proc = subprocess.run(
        [sys.executable, str(CONFLICT_CHECK)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append("check_rules_commit_conflict.py FAIL")
        errors.append(proc.stdout.strip() or proc.stderr.strip())

    if errors:
        print("FAIL: commit-ops canon incomplete\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: commit-ops canon (AGENTS.md + smartcrm-commit-ops.mdc) настроен.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
