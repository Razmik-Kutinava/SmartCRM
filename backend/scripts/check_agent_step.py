#!/usr/bin/env python3
"""Verify agent step closure: commit, ops, SESSION_STATE tail."""

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

DEFER_COMMIT_MARKERS = (
    "коммит по запросу",
    "коммит не делал",
    "жду коммит",
    "жду явного",
    "напиши коммит",
    "нужен ли коммит",
    "коммить",
)

COMMIT_HASH_RE = re.compile(r"Коммит:\s*`([0-9a-f]{7,40})`", re.I)


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


def latest_session_state_entry() -> str | None:
    if not SESSION_STATE.is_file():
        return None
    for line in SESSION_STATE.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\d{4}-\d{2}-\d{2}\s*\|", line.strip()):
            return line.strip()
    return None


def session_state_has_run_tail(entry: str) -> bool:
    required = ("Хвост A:", "Хвост B:", "Хвост C:")
    return all(marker in entry for marker in required)


def session_state_commit_hash(entry: str) -> str | None:
    m = COMMIT_HASH_RE.search(entry)
    return m.group(1) if m else None


def session_state_has_defer_commit_wording(entry: str) -> list[str]:
    lower = entry.lower()
    return [m for m in DEFER_COMMIT_MARKERS if m in lower]


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
        errors.append(
            "FAIL: незакоммиченные изменения — сначала git commit, потом ответ пользователю "
            "(smartcrm-commit-ops.mdc)."
        )

    if file_modified_in_worktree(SESSION_STATE):
        errors.append("FAIL: SESSION_STATE.md изменён, но не закоммичен.")
    elif not session_state_has_recent_entry():
        errors.append("SESSION_STATE.md: нет свежей записи (≤2 дней).")
    else:
        latest = latest_session_state_entry()
        if latest:
            if not session_state_has_run_tail(latest):
                errors.append(
                    "FAIL: последняя SESSION_STATE без Хвост A/B/C — smartcrm-commit-ops.mdc."
                )
            defer_hits = session_state_has_defer_commit_wording(latest)
            if defer_hits:
                errors.append(
                    "FAIL: SESSION_STATE содержит отложенный коммит: "
                    + ", ".join(defer_hits)
                )
            if "Коммит: —" in latest or "Коммит: pending" in latest.lower():
                errors.append("FAIL: SESSION_STATE «Коммит: —» — нужен реальный хеш.")
            if re.search(r"статус:\s*done", latest, re.I):
                if not session_state_commit_hash(latest):
                    errors.append(
                        "FAIL: SESSION_STATE done без «Коммит: `hash`» — сначала commit."
                    )

    for name, path in [("HANDOFF.md", HANDOFF), ("CHANGELOG.md", CHANGELOG)]:
        if file_modified_in_worktree(path):
            errors.append(f"FAIL: {name} изменён, но не закоммичен.")

    if not handoff_lists_recent_commit():
        warnings.append("HANDOFF.md не содержит хеш текущего HEAD.")

    print("SmartCRM agent step check\n")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
    if warnings:
        for w in warnings:
            print(f"WARN:  {w}")
    if not errors and not warnings:
        print("OK: ops и рабочее дерево согласованы для закрытия шага.")
        return 0
    if errors:
        print("\nFAIL: исправь ERROR перед отчётом пользователю.")
        return 1
    print("\nWARN only: обнови HANDOFF (хеш HEAD).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
