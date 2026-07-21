#!/usr/bin/env python3
"""Verify agent step closure: commit, ops, SESSION_STATE tail."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Кириллица в выводе не должна зависеть от кодовой страницы консоли (cp866 на Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
OPS = REPO_ROOT / "docs" / "operations" / "session"
SESSION_STATE = OPS / "SESSION_STATE.md"
HANDOFF = OPS / "HANDOFF.md"
CHANGELOG = REPO_ROOT / "docs" / "operations" / "session" / "CHANGELOG.md"

# Reuse SESSION_STATE validators (pre-commit + agent step)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_state_validate import validate_latest_entry  # noqa: E402


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
    out = run_git("status", "--porcelain", "--untracked-files=no")
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


def session_state_has_recent_entry(max_days: int = 2) -> bool:
    if not SESSION_STATE.is_file():
        return False
    text = SESSION_STATE.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).date()
    for line in text.splitlines():
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


def _latest_date(text: str, pattern: str) -> date | None:
    dates = []
    for m in re.finditer(pattern, text, re.M):
        try:
            dates.append(datetime.strptime(m.group(1), "%Y-%m-%d").date())
        except ValueError:
            continue
    return max(dates) if dates else None


def ops_freshness_errors(
    entry: str | None,
    changelog_text: str,
    handoff_text: str,
) -> list[str]:
    """CHANGELOG/HANDOFF не должны отставать от последнего done-шага SESSION_STATE.

    Гранулярность — день: последний done-шаг датирован N → в CHANGELOG (`## N — …`)
    и HANDOFF (`**N:**`) должна быть запись с датой ≥ N. Подшаги in_progress
    (SBR RED) проверку не запускают — CHANGELOG/HANDOFF для них по правилу не пишутся.
    """
    if not entry or not re.search(r"Статус:\s*done", entry):
        return []
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", entry)
    if not m:
        return []
    try:
        step_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return []

    errors: list[str] = []
    checks = [
        ("CHANGELOG.md", changelog_text, r"^##\s+(\d{4}-\d{2}-\d{2})"),
        ("HANDOFF.md", handoff_text, r"\*\*(\d{4}-\d{2}-\d{2})"),
    ]
    for name, text, pattern in checks:
        latest = _latest_date(text, pattern)
        if latest is None or latest < step_date:
            errors.append(
                f"FAIL: {name} отстаёт — последний done-шаг SESSION_STATE от {step_date}, "
                f"последняя запись {name}: {latest or 'нет'} (smartcrm-commit-ops.mdc: "
                "CHANGELOG+HANDOFF в конце шага)."
            )
    return errors


def handoff_lists_recent_commit(depth: int = 20) -> bool:
    """HANDOFF должен ссылаться на один из последних коммитов или «этот».

    Проверка по HEAD невыполнима по построению: HANDOFF коммитится вместе с шагом
    и не может содержать собственный хеш. Поэтому принимаем любой из последних
    `depth` хешей либо маркер «Коммит: `этот`» (один коммит на шаг).
    """
    if not HANDOFF.is_file():
        return False
    text = HANDOFF.read_text(encoding="utf-8")
    if re.search(r"Коммит[:\s]*`этот`", text, re.I):
        return True
    hashes = run_git("log", f"-{depth}", "--format=%h").split()
    return any(h and h in text for h in hashes)


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
        text = SESSION_STATE.read_text(encoding="utf-8")
        for msg in validate_latest_entry(text):
            errors.append(f"FAIL: SESSION_STATE — {msg}")

    for name, path in [("HANDOFF.md", HANDOFF), ("CHANGELOG.md", CHANGELOG)]:
        if file_modified_in_worktree(path):
            errors.append(f"FAIL: {name} изменён, но не закоммичен.")

    errors.extend(
        ops_freshness_errors(
            latest_session_state_entry(),
            CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.is_file() else "",
            HANDOFF.read_text(encoding="utf-8") if HANDOFF.is_file() else "",
        )
    )

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
