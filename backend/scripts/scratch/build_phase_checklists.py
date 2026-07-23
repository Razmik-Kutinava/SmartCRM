#!/usr/bin/env python3
"""Одноразовая сборка чеклистов фаз: архив Ф1-Ф3 + живой PRD_MAP Ф4 → docs/operations/phaseN/CHECKLIST_F{N}.md."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARC = REPO / "docs" / "archive" / "product" / "PRD_MAP_F1-F3.md"
LIVE = REPO / "docs" / "product" / "PRD_MAP.md"
OPS = REPO / "docs" / "operations"

LEGEND = """> **Легенда:** ✅ готово (код + смоук + acceptance) · ⚠️ код ✅, хвост в `BACKLOG.md` · 🔲 не начато · `[x]` = ✅ по коду/автомату · `[ ]` = 🔲 или хвост.
> **Закрытие пункта:** pytest + acceptance → `[x]`; финальный `[x]` — только после «ок» оператора. DoD пункта → [`dev-gates`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).
> Результаты (acceptance) — в папках областей рядом: `./{область}/*.md`. Хвосты → [`../session/BACKLOG.md`](../session/BACKLOG.md).
"""

arc = ARC.read_text(encoding="utf-8").splitlines()
live = LIVE.read_text(encoding="utf-8").splitlines()


def find(lines: list[str], prefix: str) -> int:
    return next(i for i, ln in enumerate(lines) if ln.startswith(prefix))


# Границы в архиве (0-based)
dod1 = find(arc, "### Definition of Done — Фаза 1")
dod2 = find(arc, "### Definition of Done — Фаза 2")
scen1 = find(arc, "### Фаза 1 — сценарии")
f1 = find(arc, "## Фаза 1 — MVP")
f2 = find(arc, "## Фаза 2 — Автоматизация")
f3 = find(arc, "## Фаза 3 — Автономия")

phases = {
    "phase1": (1, "Фаза 1 — MVP", "✅ закрыта (DoD 6/6, 2026-06-11)", arc[dod1:dod2] + arc[scen1:f2]),
    "phase2": (2, "Фаза 2 — Автоматизация", "✅ очереди 1–9 пройдены", arc[dod2:scen1] + arc[f2:f3]),
    "phase3": (3, "Фаза 3 — Автономия", "✅ по блокам", arc[f3:]),
}

# Ф4 из живого PRD_MAP: от "## Фаза 4" до "## Связанные документы" (включая сводку модулей)
l4 = find(live, "## Фаза 4")
lend = find(live, "## Связанные документы")
phases["phase4"] = (4, "Фаза 4 — Тюнинг и MVP", "🔄 **текущая фаза**", live[l4:lend])

for folder, (num, title, status, body) in phases.items():
    text = "\n".join(body).strip()
    # Пути были относительны docs/product/ → теперь docs/operations/phaseN/
    text = text.replace("](../operations/session/", "](../session/")
    text = text.replace("](../operations/", "](../")
    text = text.replace("](../../.cursor/", "](../../../.cursor/")
    out = OPS / folder / f"CHECKLIST_F{num}.md"
    header = f"# Чеклист: {title}\n\n**Статус фазы:** {status}\n\n{LEGEND}\n---\n\n"
    out.write_text(header + text + "\n", encoding="utf-8", newline="\n")
    print(f"{out.relative_to(REPO)}: {len(body)} строк")
