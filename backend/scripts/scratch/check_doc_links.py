#!/usr/bin/env python3
"""Одноразовая проверка относительных ссылок в живых доках после реорганизации."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")

targets = [
    *(REPO / "docs" / "product").glob("*.md"),
    REPO / "docs" / "README.md",
    REPO / "docs" / "archive" / "README.md",
    REPO / ".cursorrules",
    REPO / "AGENTS.md",
    *(REPO / ".cursor" / "rules").rglob("*.mdc"),
    *(REPO / "docs" / "operations" / "session").glob("*.md"),
    *(REPO / "docs" / "operations" / "baselines").glob("*.md"),
]

broken = 0
for f in targets:
    text = f.read_text(encoding="utf-8")
    for m in LINK_RE.finditer(text):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target = (f.parent / href).resolve()
        if not target.exists():
            print(f"BROKEN: {f.relative_to(REPO)} -> {href}")
            broken += 1
print(f"\n{'FAIL' if broken else 'OK'}: {broken} битых ссылок")
