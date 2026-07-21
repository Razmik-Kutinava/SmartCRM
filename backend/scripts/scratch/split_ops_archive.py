#!/usr/bin/env python3
"""Одноразовый распил ops-журналов по месяцам: старое → docs/archive/ops/."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OPS = REPO / "docs" / "operations" / "session"
ARCHIVE = REPO / "docs" / "archive" / "ops"
KEEP_MONTH = "2026-07"  # текущий месяц остаётся в живом файле

DATE_RE = re.compile(r"(\d{4}-\d{2})-\d{2}")


def write_archive(name: str, by_month: dict[str, list[str]], title: str) -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for month, chunks in sorted(by_month.items()):
        path = ARCHIVE / f"{month}_{name}"
        header = f"# {title} — архив {month}\n\n> Вынесено из `docs/operations/session/{name}` (распил по месяцам, 2026-07-21).\n\n"
        path.write_text(header + "\n".join(chunks).strip() + "\n", encoding="utf-8", newline="\n")
        print(f"archive: {path.relative_to(REPO)} ({len(chunks)} записей)")


def split_session_state() -> None:
    src = OPS / "SESSION_STATE.md"
    lines = src.read_text(encoding="utf-8").splitlines()
    head: list[str] = []
    keep: list[str] = []
    old: dict[str, list[str]] = defaultdict(list)
    entry_re = re.compile(r"^(\d{4}-\d{2})-\d{2}\s*\|")
    seen_entry = False
    for ln in lines:
        m = entry_re.match(ln.strip())
        if m:
            seen_entry = True
            (keep if m.group(1) == KEEP_MONTH else old[m.group(1)]).append(ln.strip())
        elif not seen_entry:
            head.append(ln)
    body = "\n".join(head).strip() + "\n\n" + "\n\n".join(keep) + "\n\n> Архив: `docs/archive/ops/` (записи по месяцам).\n"
    src.write_text(body, encoding="utf-8", newline="\n")
    write_archive("SESSION_STATE.md", {k: [e + "\n" for e in v] for k, v in old.items()}, "SESSION_STATE")
    print(f"live SESSION_STATE: {len(keep)} записей")


def split_changelog() -> None:
    src = OPS / "CHANGELOG.md"
    text = src.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(?=## \d{4}-\d{2}-\d{2})", text)
    head = parts[0].rstrip()
    keep: list[str] = []
    old: dict[str, list[str]] = defaultdict(list)
    for sec in parts[1:]:
        m = DATE_RE.search(sec.splitlines()[0])
        month = m.group(1) if m else "unknown"
        (keep if month == KEEP_MONTH else old[month]).append(sec.rstrip() + "\n")
    body = head + "\n\n" + "\n".join(keep) + "\n> Архив: `docs/archive/ops/` (секции по месяцам).\n"
    src.write_text(body, encoding="utf-8", newline="\n")
    write_archive("CHANGELOG.md", old, "CHANGELOG")
    print(f"live CHANGELOG: {len(keep)} секций")


def split_handoff() -> None:
    src = OPS / "HANDOFF.md"
    text = src.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^---\s*$", text)
    head_done = False
    keep: list[str] = []
    old: dict[str, list[str]] = defaultdict(list)
    header = "# HANDOFF\n"
    for b in blocks:
        chunk = b.strip()
        if not chunk:
            continue
        if not head_done and chunk.startswith("# HANDOFF"):
            chunk = chunk[len("# HANDOFF"):].strip()
            head_done = True
            if not chunk:
                continue
        m = DATE_RE.search(chunk)
        month = m.group(1) if m else "unknown"
        (keep if month == KEEP_MONTH else old[month]).append(chunk + "\n")
    body = header + "\n" + "\n---\n\n".join(keep) + "\n---\n\n> Архив: `docs/archive/ops/` (блоки по месяцам).\n"
    src.write_text(body, encoding="utf-8", newline="\n")
    write_archive("HANDOFF.md", {k: ["\n---\n\n".join(v)] for k, v in old.items()}, "HANDOFF")
    print(f"live HANDOFF: {len(keep)} блоков")


if __name__ == "__main__":
    split_session_state()
    split_changelog()
    split_handoff()
