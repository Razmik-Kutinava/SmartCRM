"""Карточка лида после сохранения: lead берётся из ответа API, а не из кэша списка.

Баг: третий контакт сохранялся в БД, но список «Контакты на лиде» показывал 2 —
`fetchLeadById` вызывался, результат выбрасывался, а `sync()` читал устаревший
кэш `smartcrm_leads_cache_v2` (на 3k+ лидов `fetchLeads()` идёт больше 10с).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def _function_body(text: str, name: str) -> str:
    """Тело функции от объявления до следующего объявления верхнего уровня."""
    start = text.index(f"function {name}(")
    rest = text[start:]
    nxt = re.search(r"\n\t(?:async )?function ", rest[10:])
    return rest[: nxt.start() + 10] if nxt else rest


def test_fetch_lead_by_id_result_is_applied():
    """Ответ детального API применяется к lead — иначе UI показывает старые данные."""
    text = _page_text()
    orphan = re.findall(r"^\s*await fetchLeadById\([^)]*\);\s*$", text, re.MULTILINE)
    assert not orphan, (
        "fetchLeadById вызван, но результат выброшен — карточка останется на кэше: "
        f"{len(orphan)} мест"
    )


def test_save_contacts_refreshes_lead_from_api():
    """После сохранения контактов lead обновляется ответом API, а не sync() из кэша."""
    body = _function_body(_page_text(), "saveContactsFields")
    assert "refreshLeadFromApi" in body, "нет обновления lead из ответа API"
    assert not re.search(r"^\s*sync\(\);\s*$", body, re.MULTILINE), (
        "sync() читает кэш списка и затирает свежий lead"
    )


def test_save_contacts_does_not_block_on_full_list():
    """Полный список (3k+ лидов) не должен блокировать закрытие сохранения."""
    body = _function_body(_page_text(), "saveContactsFields")
    assert "await fetchLeads()" not in body, (
        "await fetchLeads() тянет весь список и задерживает обновление карточки"
    )


def test_no_duplicate_contacts_draft_sync():
    """Дублирующийся вызов syncContactsDraftFromLead — мусор после правок."""
    text = _page_text()
    assert not re.search(
        r"syncContactsDraftFromLead\(\);\s*\n\s*syncContactsDraftFromLead\(\);", text
    ), "syncContactsDraftFromLead вызван дважды подряд"
