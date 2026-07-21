#!/usr/bin/env python3
"""Одноразовый распил PRD_MAP: чеклисты Ф1–Ф3 → docs/archive/product/PRD_MAP_F1-F3.md."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "docs" / "product" / "PRD_MAP.md"
DST = REPO / "docs" / "archive" / "product" / "PRD_MAP_F1-F3.md"

lines = SRC.read_text(encoding="utf-8").splitlines()

# Границы: с "### Definition of Done — Фаза 1" до строки перед "## Фаза 4"
start = next(i for i, ln in enumerate(lines) if ln.startswith("### Definition of Done — Фаза 1"))
end = next(i for i, ln in enumerate(lines) if ln.startswith("## Фаза 4"))

archived = lines[start:end]
header = (
    "# PRD_MAP — архив: Фазы 1–3 (закрыты)\n\n"
    "> Вынесено из [`docs/product/PRD_MAP.md`](../../product/PRD_MAP.md) 2026-07-21.\n"
    "> Здесь полные чеклисты и DoD закрытых фаз 1–3. Активная работа — Фаза 4 в живом PRD_MAP.\n\n"
)
DST.write_text(header + "\n".join(archived).strip() + "\n", encoding="utf-8", newline="\n")
print(f"archive: {DST.relative_to(REPO)} ({len(archived)} строк)")
print(f"live остаток: {start} строк шапки + {len(lines) - end} строк хвоста")
