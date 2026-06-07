"""Checko person lookup."""
from __future__ import annotations

import logging
from typing import Any

from .helpers import (
    _clean_city,
    _detect_mgt,
    _extract_city,
    _num,
    _parse_status,
    _str_from_field,
    _sum_num,
)
from .http_client import _get

logger = logging.getLogger(__name__)

async def fetch_person(person_inn: str) -> dict:
    """
    GET /person?inn={person_inn}
    Возвращает все связи физлица:
    - Учред: компании где он учредитель (с долями)
    - Руковод: компании где он директор/руководитель
    - ИП: его индивидуальные предпринимательства
    - Дисквал: флаг дисквалификации
    """
    if not _available() or not person_inn:
        return {}
    body = await _get("/person", {"inn": person_inn})
    if not body:
        return {}
    data = body.get("data") or body
    if not data or isinstance(data, list):
        return {}
    return _parse_person_data(data, person_inn)


def _parse_person_data(d: dict, person_inn: str) -> dict:
    """Нормализует ответ /person."""
    name = d.get("ФИО") or d.get("fio") or ""

    # Компании где учредитель
    founder_companies: list[dict] = []
    for c in (d.get("Учред") or []):
        if not isinstance(c, dict):
            continue
        c_inn = c.get("ИНН") or ""
        c_name = c.get("НаимСокр") or c.get("НаимПолн") or ""
        if c_inn or c_name:
            founder_companies.append({
                "inn": c_inn,
                "ogrn": c.get("ОГРН") or "",
                "name": c_name,
                "name_full": c.get("НаимПолн") or c_name,
                "status": _parse_status(c.get("Статус") or ""),
                "okved": c.get("ОКВЭД") or "",
                "city": _extract_city(c.get("ЮрАдрес") or ""),
                "address": c.get("ЮрАдрес") or "",
                "_relation": f"учредитель: {name}",
            })

    # Компании где директор/руководитель
    director_companies: list[dict] = []
    for c in (d.get("Руковод") or []):
        if not isinstance(c, dict):
            continue
        c_inn = c.get("ИНН") or ""
        c_name = c.get("НаимСокр") or c.get("НаимПолн") or ""
        if c_inn or c_name:
            director_companies.append({
                "inn": c_inn,
                "ogrn": c.get("ОГРН") or "",
                "name": c_name,
                "name_full": c.get("НаимПолн") or c_name,
                "status": _parse_status(c.get("Статус") or ""),
                "okved": c.get("ОКВЭД") or "",
                "city": _extract_city(c.get("ЮрАдрес") or ""),
                "address": c.get("ЮрАдрес") or "",
                "_relation": f"директор: {name}",
            })

    # ИП
    ip_list: list[dict] = []
    for ip in (d.get("ИП") or []):
        if not isinstance(ip, dict):
            continue
        ogrnip = ip.get("ОГРНИП") or ip.get("ОGRНИП") or ip.get("Рег") or ""
        status = _parse_status(ip.get("Статус") or "")
        ip_list.append({
            "ogrnip": ogrnip,
            "name": name,
            "status": status,
            "reg_date": ip.get("ДатаРег") or "",
            "okved": ip.get("ОКВЭД") or "",
            "city": _extract_city(ip.get("Адрес") or ""),
            "_relation": f"ИП: {name}",
        })

    return {
        "person_inn": person_inn,
        "person_name": name,
        "is_disqualified": bool(d.get("Дисквал") or d.get("Дисквалиф")),
        "is_mass_founder": bool(d.get("МассФЛ")),
        "founder_companies": founder_companies,
        "director_companies": director_companies,
        "ip_list": ip_list,
        "total_companies": len(founder_companies) + len(director_companies) + len(ip_list),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Вспомогательные функции
# ══════════════════════════════════════════════════════════════════════════════


