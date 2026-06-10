#!/usr/bin/env python3
"""Fail if rules/docs teach deferred or optional git commit."""

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
    REPO_ROOT / "AGENTS.md",
)

SKIP_NAMES = {
    "check_rules_commit_conflict.py",
}

BAD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("commit_only_on_request", re.compile(r"коммит\s+по\s+запросу", re.I)),
    ("commit_only_when_requested", re.compile(r"only\s+create\s+commits\s+when\s+requested", re.I)),
    ("commit_en_only_on_request", re.compile(r"commit\s+только\s+по\s+явному\s+запросу", re.I)),
    ("commit_en_explicit_request", re.compile(r"commit\s+only\s+(when\s+requested|by\s+explicit|on\s+request)", re.I)),
    ("commit_if_user_asks", re.compile(r"коммит\s+только\s+по\s+запросу", re.I)),
    ("go_then_commit", re.compile(r"`go`\s+commit|go\s+commit\s*→", re.I)),
    ("committing_changes_rule", re.compile(r"committing-changes-with-git", re.I)),
    ("ask_if_commit_needed", re.compile(r"скажи.*коммит|нужен\s+ли\s+коммит|напиши.*коммит", re.I)),
    ("commit_not_done", re.compile(r"коммит\s+не\s+делал", re.I)),
    ("wait_for_commit", re.compile(r"жду.*коммит|жду\s+явн", re.I)),
    ("commit_dash", re.compile(r"Коммит:\s*—", re.I)),
    ("next_step_commit", re.compile(r"следующий\s+шаг:\s*(коммит|commit)\b", re.I)),
    ("defer_commit_phrase", re.compile(r"следующий\s+шаг:.*\b(коммит|commit)\b", re.I)),
    ("commit_arrow", re.compile(r"следующий\s+шаг:.*коммит\s*→", re.I)),
    ("commit_needs_approval", re.compile(r"апрув.*→\s*commit|commit.*→.*апрув|апрув.*commit\+push", re.I)),
]


def _should_scan(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return False
    if path.suffix not in {".mdc", ".md", ".cursorrules"} and path.name != ".cursorrules":
        return False
    return True


def _is_commit_hash_line(line: str) -> bool:
    return bool(re.search(r"Коммит:\s*`[0-9a-f]{7,40}`", line, re.I))


ENTRY_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s*\|")


def scan_file(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: read error: {exc}"]
    skip_journal = path.name == "SESSION_STATE.md"
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if skip_journal and ENTRY_LINE_RE.match(stripped):
            continue
        if _is_commit_hash_line(line):
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
        print("RULE CONFLICT: deferred/optional commit wording found\n")
        for hit in all_hits:
            print(f"  - {hit}")
        print(f"\n{len(all_hits)} conflict(s). Fix rules/docs, then re-run.")
        return 1

    print("OK: no deferred/optional commit wording in scanned rules/docs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
