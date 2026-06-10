#!/usr/bin/env python3
"""Validate SESSION_STATE journal lines — block deferred-commit wording."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SESSION_STATE = REPO_ROOT / "docs" / "operations" / "SESSION_STATE.md"

ENTRY_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s*\|")
COMMIT_HASH_RE = re.compile(r"Коммит:\s*`([0-9a-f]{7,40})`", re.I)

DEFER_MARKERS = (
    "коммит по запросу",
    "коммит не делал",
    "жду коммит",
    "жду явного",
    "напиши коммит",
    "нужен ли коммит",
    "коммить",
    "коммитни",
)

DEFER_REGEXES = (
    re.compile(r"Коммит:\s*—", re.I),
    re.compile(r"коммит\s+по\s+запросу", re.I),
    re.compile(r"следующий\s+шаг:.*\b(коммит|commit)\b", re.I),
)


def is_journal_entry(line: str) -> bool:
    return bool(ENTRY_LINE_RE.match(line.strip()))


def validate_journal_line(line: str, *, require_tail: bool = False) -> list[str]:
    """Return error messages for a single journal line."""
    errors: list[str] = []
    stripped = line.strip()
    if not is_journal_entry(stripped):
        return errors

    lower = stripped.lower()
    for marker in DEFER_MARKERS:
        if marker in lower:
            errors.append(f"отложенный коммит: «{marker}»")

    for pattern in DEFER_REGEXES:
        if pattern.search(stripped):
            errors.append(f"паттерн: {pattern.pattern}")

    if require_tail or "Хвост A:" in stripped:
        for label in ("Хвост A:", "Хвост B:", "Хвост C:"):
            if label not in stripped:
                errors.append(f"нет {label}")

    if re.compile(r"Коммит:\s*pending", re.I).search(stripped):
        errors.append("«Коммит: pending» — сначала git commit, потом хеш")

    is_done = bool(re.search(r"статус:\s*done", stripped, re.I))
    if is_done and not COMMIT_HASH_RE.search(stripped):
        errors.append("Статус done без «Коммит: `hash`»")

    return errors


def iter_journal_lines(text: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if is_journal_entry(line):
            rows.append((lineno, line.strip()))
    return rows


def validate_text(text: str, *, only_lines: set[int] | None = None) -> list[str]:
    errors: list[str] = []
    for lineno, line in iter_journal_lines(text):
        if only_lines is not None and lineno not in only_lines:
            continue
        require_tail = "Хвост A:" in line or lineno <= 30
        for msg in validate_journal_line(line, require_tail=require_tail and "Хвост A:" in line):
            errors.append(f"строка {lineno}: {msg}")
    return errors


def staged_session_state_text() -> str | None:
    proc = subprocess.run(
        ["git", "show", ":docs/operations/SESSION_STATE.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def staged_added_journal_line_numbers() -> set[int] | None:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--unified=0",
            "--",
            "docs/operations/SESSION_STATE.md",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0 or proc.stdout is None or not proc.stdout.strip():
        return None

    new_line_nums: set[int] = set()
    current_new = 0
    for raw in proc.stdout.splitlines():
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            current_new = int(m.group(1)) if m else 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            if is_journal_entry(raw[1:]):
                new_line_nums.add(current_new)
            current_new += 1
        elif raw.startswith(" ") or raw.startswith("+"):
            current_new += 1
    return new_line_nums if new_line_nums else None


def is_session_state_staged() -> bool:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "docs/operations/SESSION_STATE.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return bool(proc.stdout and proc.stdout.strip())


def validate_latest_entry(text: str) -> list[str]:
    for _lineno, line in iter_journal_lines(text):
        return validate_journal_line(line, require_tail="Хвост A:" in line)
    return ["нет журнальной строки"]


def main() -> int:
    mode = "--file"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    errors: list[str] = []

    if mode == "--pre-commit":
        if not is_session_state_staged():
            return 0
        staged = staged_session_state_text()
        if staged is None:
            print("FAIL: не прочитать staged SESSION_STATE.md")
            return 1
        added = staged_added_journal_line_numbers()
        if added:
            errors.extend(validate_text(staged, only_lines=added))
        latest_errs = validate_latest_entry(staged)
        for e in latest_errs:
            errors.append(f"последняя запись: {e}")
    else:
        path = SESSION_STATE
        if not path.is_file():
            print(f"FAIL: нет {path}")
            return 1
        text = path.read_text(encoding="utf-8")
        for e in validate_latest_entry(text):
            errors.append(f"последняя запись: {e}")

    if errors:
        print("SESSION_STATE validation FAIL\n")
        for e in errors:
            print(f"  - {e}")
        print("\nИсправь: git commit, затем Коммит: `hash` в SESSION_STATE. См. smartcrm-commit-ops.mdc")
        return 1

    print("OK: SESSION_STATE journal lines valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
