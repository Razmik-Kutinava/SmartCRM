#!/usr/bin/env python3
"""Verify agent step closure: ops files touched, optional commit ahead of origin."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OPS = REPO_ROOT / "docs" / "operations"
SESSION_STATE = OPS / "SESSION_STATE.md"
HANDOFF = OPS / "HANDOFF.md"
CHANGELOG = OPS / "CHANGELOG.md"


def run_git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def has_uncommitted_changes() -> bool:
    out = run_git("status", "--porcelain")
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    return len(lines) > 0


def file_modified_in_worktree(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    out = run_git("status", "--porcelain", rel)
    return bool(out.strip())


def session_state_has_recent_entry(max_days: int = 2) -> bool:
    if not SESSION_STATE.is_file():
        return False
    text = SESSION_STATE.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).date()
    for line in reversed(text.splitlines()):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", line.strip())
        if not m:
            continue
        try:
            entry_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        if (today - entry_date).days <= max_days:
            return True
        break
    return False


def handoff_lists_recent_commit() -> bool:
    if not HANDOFF.is_file():
        return False
    head = run_git("rev-parse", "--short", "HEAD").strip()
    if not head:
        return False
    return head in HANDOFF.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if has_uncommitted_changes():
        warnings.append(
            "Есть незакоммиченные изменения — после шага нужен git commit "
            "(smartcrm-agent-workflow §1)."
        )

    if file_modified_in_worktree(SESSION_STATE):
        warnings.append(
            "SESSION_STATE.md изменён, но не закоммичен — включи в коммит шага."
        )
    elif not session_state_has_recent_entry():
        errors.append(
            "SESSION_STATE.md: нет свежей записи (≤2 дней) — обнови ops после шага."
        )

    for name, path in [("HANDOFF.md", HANDOFF), ("CHANGELOG.md", CHANGELOG)]:
        if file_modified_in_worktree(path):
            warnings.append(f"{name} изменён, но не закоммичен.")

    if not handoff_lists_recent_commit():
        warnings.append(
            "HANDOFF.md не содержит хеш текущего HEAD — обнови «Последние коммиты»."
        )

    print("SmartCRM agent step check\n")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
    if warnings:
        for w in warnings:
            print(f"WARN:  {w}")
    if not errors and not warnings:
        print("OK: ops и рабочее дерево выглядят согласованно для закрытия шага.")
        return 0
    if errors:
        print("\nFAIL: исправь ERROR перед отчётом «done».")
        return 1
    print("\nWARN only: можно коммитить и закрывать шаг.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
