"""Список лидов: пока идёт первая загрузка, не показываем демо-лидов как настоящие.

DevTools-обход 2026-08-01: `/api/leads` на 3258 лидах отвечает 13 секунд.
Всё это время список рисовал `DEFAULT_LEADS` («АО МашПром», «Иван Петров»)
и заголовок «7 лидов» — выглядит как реальная база, ссылки ведут на
несуществующие /leads/2. Раньше это маскировал кэш, который перестал
помещаться в квоту localStorage.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIST_PAGE = ROOT / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"
STORAGE = ROOT / "frontend" / "src" / "lib" / "leadsStorage.js"


def test_storage_exposes_cache_without_demo():
    """Нужен доступ к кэшу без подмены демо-данными."""
    text = STORAGE.read_text(encoding="utf-8")
    assert "readLeadsCacheOrNull" in text, (
        "readLeadsCache() всегда подставляет DEFAULT_LEADS — списку нужен "
        "способ отличить «кэша нет» от «есть данные»"
    )


def test_list_starts_without_demo_rows():
    """Стартовое состояние списка — кэш или пусто, но не демо."""
    text = LIST_PAGE.read_text(encoding="utf-8")
    assert "let leads = $state(readLeadsCache())" not in text, (
        "список стартует с демо-лидов и показывает их 13 секунд как настоящие"
    )
    assert "readLeadsCacheOrNull" in text


def test_list_has_loading_state():
    """Пока грузим — говорим об этом, а не рисуем чужие данные."""
    text = LIST_PAGE.read_text(encoding="utf-8")
    assert "leadsLoading" in text, "нет флага первой загрузки"
    assert "Загружаю" in text or "Загрузка" in text, "пользователю не видно, что идёт загрузка"


def test_demo_leads_only_on_api_error():
    """Демо-витрина остаётся, но только когда API недоступен."""
    text = LIST_PAGE.read_text(encoding="utf-8")
    catch_block = text[text.index("catch (e)") : text.index("catch (e)") + 400]
    assert "DEMO" in catch_block or "demo" in catch_block.lower(), (
        "при недоступном API список должен падать на демо-данные, как раньше"
    )
