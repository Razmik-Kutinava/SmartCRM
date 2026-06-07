"""Checko company search."""
from __future__ import annotations

import logging
import re

import httpx

from .helpers import _extract_city, _parse_status, _str_from_field
from .http_client import _available, _get
from .parse_company import _parse_company

logger = logging.getLogger(__name__)

async def fetch_company(inn: str) -> dict | None:
    """
    Полные данные организации по ИНН.
    Возвращает нормализованный словарь совместимый с dadata._parse_suggestion.
    """
    body = await _get("/company", {"inn": inn})
    if not body:
        return None
    raw = body.get("data") or {}
    if not raw:
        return None
    return _parse_company(raw)


async def search_companies(query: str, count: int = 5) -> list[dict]:
    """
    Поиск организаций по названию через egrul.nalog.ru (бесплатно, без ключа).
    Checko /search не работает на свободном тарифе.
    После получения ИНН — обогащаем через Checko /company.
    """
    rows = await _search_egrul_rows(query, count)
    if not rows:
        return []

    inns = []
    for row in rows[:count]:
        inn = row.get("i") or row.get("inn") or row.get("ИНН") or ""
        if inn:
            inns.append(str(inn))

    # Если ключа Checko нет — возвращаем минимальные данные из ЕГРЮЛ rows.
    if not _available():
        parsed = [_parse_search_item(r) for r in rows[:count]]
        return [p for p in parsed if p]

    import asyncio
    results = await asyncio.gather(
        *[fetch_company(inn) for inn in inns[:count]],
        return_exceptions=True,
    )
    out: list[dict] = []
    for idx, r in enumerate(results):
        if isinstance(r, dict) and r:
            out.append(r)
        else:
            # fallback на минимальные данные из ЕГРЮЛ, если Checko не отдал карточку
            if idx < len(rows):
                p = _parse_search_item(rows[idx])
                if p:
                    out.append(p)
    return out


async def _search_egrul(query: str, count: int = 5) -> list[str]:
    rows = await _search_egrul_rows(query, count)
    inns = []
    for row in rows[:count]:
        inn = row.get("i") or row.get("inn") or row.get("ИНН") or ""
        if inn:
            inns.append(str(inn))
    return inns


async def _search_egrul_rows(query: str, count: int = 5) -> list[dict]:
    """
    Поиск в ЕГРЮЛ по названию → сырые rows.
    Нужен для fallback, когда Checko API ключ не задан.
    """
    try:
        import asyncio
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://egrul.nalog.ru/",
                data={"query": query, "region": "", "page": ""},
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code != 200:
                # Fallback: GET с query
                r = await client.get(
                    "https://egrul.nalog.ru/search-result",
                    params={"query": query, "region": "", "page": ""},
                    headers={"Accept": "application/json"},
                )
            if r.status_code != 200:
                return []
            try:
                data = r.json()
            except Exception:
                return []

            # ЕГРЮЛ может вернуть token t, а строки будут доступны по /search-result/{t}
            rows = []
            if isinstance(data, dict):
                rows = data.get("rows") or []
                token = data.get("t")
                if not rows and token:
                    for _ in range(4):
                        await asyncio.sleep(0.8)
                        rr = await client.get(
                            f"https://egrul.nalog.ru/search-result/{token}",
                            headers={"Accept": "application/json"},
                        )
                        if rr.status_code != 200:
                            continue
                        try:
                            token_data = rr.json()
                        except Exception:
                            continue
                        if token_data.get("status") == "wait":
                            continue
                        rows = token_data.get("rows") or []
                        if rows:
                            break
            elif isinstance(data, list):
                rows = data

            return rows[:count]
    except Exception as e:
        logger.warning("EGRUL search failed for '%s': %s", query, e)
        return []


def _parse_search_item(item: dict) -> dict | None:
    """Парсит элемент из списка /search — формат проще чем /company."""
    if not isinstance(item, dict):
        return None
    inn = item.get("ИНН") or item.get("inn") or item.get("i") or ""
    if not inn:
        return None
    address_raw = item.get("ЮрАдрес") or item.get("address") or item.get("g") or ""
    name_full = item.get("НаимПолн") or item.get("name") or item.get("n") or ""
    name_short = item.get("НаимСокр") or item.get("c") or name_full

    return {
        "inn": inn,
        "kpp": item.get("КПП") or item.get("kpp") or item.get("p") or "",
        "ogrn": item.get("ОГРН") or item.get("ogrn") or item.get("o") or "",
        "name": name_full or name_short,
        "name_short": name_short or "",
        "okved": _str_from_field(item.get("ОКВЭД")),
        "okved_name": "",
        "status": _parse_status(item.get("Статус")),
        "registration_date": item.get("ДатаРег") or item.get("r"),
        "liquidation_date": item.get("ДатаЛикв"),
        "address": address_raw,
        "city": _extract_city(address_raw),
        "director": "",
        "director_post": "",
        "founders": [],
        "employees_count": None,
        "website": "",
        "branch_count": 0,
        "management_type": "hired_director",
        "revenue": None, "income": None, "expense": None,
        "debt": None, "finance_year": None,
        "dadata_emails": [], "dadata_phones": [],
        "smb_category": None, "licenses": [],
        "_source": "checko",
    }



