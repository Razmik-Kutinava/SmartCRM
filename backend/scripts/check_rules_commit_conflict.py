#!/usr/bin/env python3
"""Fail if repo rules/docs contain conflicting commit-on-request wording."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCAN_DIRS = (
    REPO_ROOT / ".cursor" / "rules",
    REPO_ROOT / "docs" / "operations",
)
SCAN_FILES = (
    REPO_ROOT / ".cursorrules",
)

SKIP_NAMES = {
    "check_rules_commit_conflict.py",
    "SESSION_STATE.md",  # historical lines; header is canonical
    "smartcrm-commit-ops.mdc",  # canon lists forbidden phrases
}

# Patterns that contradict smartcrm-commit-ops.mdc (case-insensitive).
BAD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("commit_only_on_request", re.compile(r"коммит\s+по\s+запросу", re.I)),
    ("commit_only_when_requested", re.compile(r"only\s+create\s+commits\s+when\s+requested", re.I)),
    ("commit_if_user_asks", re.compile(r"коммит\s+только\s+по\s+запросу", re.I)),
    ("ask_if_commit_needed", re.compile(r"скажи.*коммит|нужен\s+ли\s+коммит", re.I)),
    ("commit_not_done", re.compile(r"коммит\s+не\s+делал", re.I)),
    ("optional_ops_header", re.compile(r"по\s+желанию.*SESSION", re.I)),
    ("commit_needs_approval", re.compile(r"коммит.*→.*апрув|апрув.*коммит", re.I)),
    ("stop_until_approval_ambiguous", re.compile(r"стоп\s+до\s+апрува", re.I)),
]

ALLOWLIST_SUBSTRINGS = (
    "smartcrm-commit-ops.mdc",
    "check_rules_commit_conflict.py",
    "Запрещено",
    "НЕ писать",
    "не писать",
    "удалить",
    "Удалить",
    "historical",
)


def _should_scan(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return False
    if path.suffix not in {".mdc", ".md", ".cursorrules"} and path.name != ".cursorrules":
        return False
    return True


def _is_allowlisted(line: str) -> bool:
    if any(s in line for s in ALLOWLIST_SUBSTRINGS):
        return True
    # Quoted examples of forbidden agent phrases
    if "«" in line and "»" in line:
        return True
    return False


def scan_file(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: read error: {exc}"]
    in_delete_section = False
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "удалить конфликт" in line.lower() or stripped.startswith("## Шаг 1"):
            in_delete_section = True
            continue
        if stripped.startswith("## Шаг 2"):
            in_delete_section = False
        if in_delete_section:
            continue
        if _is_allowlisted(line):
            continue
        for label, pattern in BAD_PATTERNS:
            if pattern.search(line):
                hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno} [{label}] {line.strip()[:120]}")
    return hits


def main() -> int:
    paths: list[Path] = []
    for d in SCAN_DIRS:
        if d.is_dir():
            paths.extend(sorted(p for p in d.rglob("*") if p.is_file() and _should_scan(p)))
    for f in SCAN_FILES:
        if f.is_file():
            paths.append(f)

    all_hits: list[str] = []
    for path in paths:
        all_hits.extend(scan_file(path))

    if all_hits:
        print("RULE CONFLICT: commit/ops wording contradicts smartcrm-commit-ops.mdc\n")
        for hit in all_hits:
            print(f"  - {hit}")
        print(f"\n{len(all_hits)} conflict(s). Fix rules/docs, then re-run.")
        return 1

    print("OK: no commit/ops rule conflicts in scanned rules/docs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
