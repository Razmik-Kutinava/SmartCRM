"""Косяки, найденные обходом фронта через Chrome DevTools MCP (2026-08-01).

1. Карточка лида грузила всё дважды: `page.subscribe(pullLead)` вызывался
   повторно (openHubPanel меняет `?panel=`), а `lastFetchedOkId` ставился
   только после двух `await` — гонка успевала пропустить оба вызова.
2. localStorage забит кэшем списка (4.7 МБ, 3231 лид) — квота исчерпана,
   `setItem` молча падает, кэш застыл и блокирует запись других ключей.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
STORAGE = ROOT / "frontend" / "src" / "lib" / "leadsStorage.js"


def _pull_lead_body() -> str:
    text = PAGE.read_text(encoding="utf-8")
    start = text.index("async function pullLead()")
    rest = text[start:]
    return rest[: rest.index("\n\t\tloadIndustryOptions()")]


def test_pull_lead_marks_id_before_await():
    """Отметка «этот лид уже грузим» — до первого await, иначе двойная загрузка."""
    body = _pull_lead_body()
    first_await = body.index("await ")
    head = body[:first_await]
    assert re.search(r"(inFlight|pending|requestedId)", head), (
        "id фиксируется только после await — два вызова подписки пройдут проверку "
        "и карточка загрузит всё дважды"
    )


def test_cache_write_handles_quota():
    """Квота localStorage: мусор чистим, а не пишем в молчаливый except."""
    text = STORAGE.read_text(encoding="utf-8")
    body = text[text.index("function cacheWrite") : text.index("function cacheRead")]
    assert "removeItem" in body, (
        "при QuotaExceededError старый кэш остаётся в localStorage и держит квоту "
        "занятой — другие ключи тоже перестают писаться"
    )


def test_cache_strips_heavy_fields():
    """В кэш списка не кладём тяжёлые поля карточки (checko/tech/history)."""
    text = STORAGE.read_text(encoding="utf-8")
    assert "cacheSlim" in text or "stripHeavyFields" in text, (
        "полный лид с досье и UF не должен попадать в кэш списка"
    )
