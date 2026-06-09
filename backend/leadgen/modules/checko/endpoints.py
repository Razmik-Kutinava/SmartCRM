"""Checko API endpoints (finances, legal, profile)."""
from __future__ import annotations

import logging
from typing import Any

from .helpers import _num, _sum_num
from .http_client import _available, _get

logger = logging.getLogger(__name__)

async def fetch_finances(inn: str) -> dict:
    """
    Финансовая отчётность по ИНН.
    Формат: data.{year}.{code} где 2110=выручка, 2400=прибыль, 1600=активы, 1520=долг
    """
    body = await _get("/finances", {"inn": inn})
    if not body:
        return {}
    data = body.get("data") or {}
    if not data:
        return {}
    return _parse_finances(data)


def _parse_finances(data: dict | list) -> dict:
    """Парсим финансовые данные — коды строк бухотчётности по МСФО."""
    revenue_series: list[tuple[int, float]] = []
    profit_series: list[tuple[int, float]] = []
    assets_val = None
    expense_val = None
    debt_val = None

    if isinstance(data, dict):
        for year_key, yr_data in data.items():
            if not isinstance(yr_data, dict):
                continue
            try:
                yr = int(year_key)
            except (ValueError, TypeError):
                continue
            # Строки бухотчётности (РСБУ)
            rev = _num(yr_data.get("2110"))   # Выручка
            prof = _num(yr_data.get("2400"))  # Чистая прибыль
            assets = _num(yr_data.get("1600"))  # Баланс активов
            # Расходы: себестоимость + коммерч. + управленч.
            exp = _sum_num(yr_data.get("2120"), yr_data.get("2210"), yr_data.get("2220"))
            debt = _num(yr_data.get("1520"))  # Кредиторская задолженность

            if rev is not None:
                revenue_series.append((yr, rev))
            if prof is not None:
                profit_series.append((yr, prof))
            # Берём данные самого свежего года
            if assets is not None:
                assets_val = assets
            if exp is not None:
                expense_val = exp
            if debt is not None:
                debt_val = debt

    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            yr = _num(item.get("year") or item.get("Год"))
            if yr is None:
                continue
            yr = int(yr)
            rev = _num(item.get("2110") or item.get("revenue"))
            prof = _num(item.get("2400") or item.get("profit"))
            if rev is not None:
                revenue_series.append((yr, rev))
            if prof is not None:
                profit_series.append((yr, prof))

    # Сортируем по году (старые → новые)
    revenue_series.sort(key=lambda x: x[0])
    profit_series.sort(key=lambda x: x[0])

    revenue = revenue_series[-1][1] if revenue_series else None
    profit = profit_series[-1][1] if profit_series else None
    finance_year = revenue_series[-1][0] if revenue_series else None

    trend = "unknown"
    if len(revenue_series) >= 2:
        prev = revenue_series[-2][1] or 0
        curr = revenue_series[-1][1] or 0
        if curr > prev * 1.1:
            trend = "growing"
        elif curr < prev * 0.9:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "revenue": revenue,
        "profit": profit,
        "assets": assets_val,
        "expense": expense_val,
        "debt": debt_val,
        "finance_year": finance_year,
        "revenue_trend": trend,
        "revenue_series": revenue_series[-3:],
        "profit_series": profit_series[-3:],
    }


# ══════════════════════════════════════════════════════════════════════════════
# /legal-cases — арбитражные дела (КАД)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_legal_cases(inn: str) -> dict:
    body = await _get("/legal-cases", {"inn": inn})
    if not body:
        return {"arbitration_count": 0, "cases": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or data.get("cases") or [])

    parsed = []
    for c in items[:5]:
        if isinstance(c, dict):
            parsed.append({
                "number": c.get("number") or c.get("НомерДела") or "",
                "date": c.get("date") or c.get("ДатаПод") or "",
                "amount": _num(c.get("amount") or c.get("Сумма")),
                "role": c.get("role") or c.get("Роль") or "",
                "result": c.get("result") or c.get("Результат") or "",
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total") or data.get("count")) or total

    return {"arbitration_count": int(total), "cases": parsed}


# ══════════════════════════════════════════════════════════════════════════════
# /enforcements — исполнительные производства ФССП
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_enforcements(inn: str) -> dict:
    body = await _get("/enforcements", {"inn": inn})
    if not body:
        return {"enforcement_count": 0, "enforcement_debt": 0, "enforcements": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    total_debt = 0.0
    parsed = []
    for item in items[:5]:
        if isinstance(item, dict):
            amount = _num(item.get("amount") or item.get("Сумма") or 0) or 0
            total_debt += amount
            parsed.append({
                "number": item.get("number") or item.get("НомерИП") or "",
                "date": item.get("date") or item.get("Дата") or "",
                "amount": amount,
                "reason": item.get("reason") or item.get("Предмет") or "",
                "status": item.get("status") or item.get("Статус") or "",
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {
        "enforcement_count": int(total),
        "enforcement_debt": total_debt,
        "enforcements": parsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /contracts — госзакупки (44-ФЗ)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_contracts(inn: str, limit: int = 5) -> dict:
    body = await _get("/contracts", {
        "inn": inn, "law": "44", "role": "supplier", "sort": "-date"
    })
    if not body:
        return {"contracts_count": 0, "contracts_total_amount": 0, "contracts": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or data.get("contracts") or [])

    total_amount = 0.0
    parsed = []
    for c in items[:limit]:
        if isinstance(c, dict):
            amount = _num(c.get("price") or c.get("amount") or c.get("Цена") or 0) or 0
            total_amount += amount
            parsed.append({
                "number": c.get("number") or c.get("regNum") or c.get("РегНом") or "",
                "date": c.get("date") or c.get("signDate") or c.get("Дата") or "",
                "amount": amount,
                "customer": c.get("customer") or c.get("Заказчик") or "",
                "subject": (c.get("subject") or c.get("name") or c.get("Предмет") or "")[:120],
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {
        "contracts_count": int(total),
        "contracts_total_amount": total_amount,
        "contracts": parsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /bankruptcy-messages — банкротство (ЕФРСБ)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_bankruptcy(inn: str) -> dict:
    body = await _get("/bankruptcy-messages", {"inn": inn})
    if not body:
        return {"has_bankruptcy": False, "bankruptcy_messages": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    has_bankrupt = False
    messages = []
    for m in items[:3]:
        if isinstance(m, dict):
            msg_type = m.get("type") or m.get("Тип") or ""
            if any(kw in str(msg_type).lower() for kw in ("банкрот", "конкурс", "несостоят")):
                has_bankrupt = True
            messages.append({
                "type": msg_type,
                "date": m.get("date") or m.get("Дата") or "",
                "text": (m.get("text") or m.get("Содержание") or "")[:200],
            })

    return {
        "has_bankruptcy": has_bankrupt or bool(items),
        "bankruptcy_messages": messages,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /inspections — проверки Генпрокуратуры
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_inspections(inn: str) -> dict:
    body = await _get("/inspections", {"inn": inn})
    if not body:
        return {"inspection_count": 0, "inspections": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    parsed = []
    for item in items[:5]:
        if isinstance(item, dict):
            parsed.append({
                "authority": item.get("authority") or item.get("Орган") or "",
                "date": item.get("date") or item.get("Дата") or "",
                "result": item.get("result") or item.get("Результат") or "",
                "violations": bool(item.get("violations") or item.get("Нарушения")),
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {"inspection_count": int(total), "inspections": parsed}


# ══════════════════════════════════════════════════════════════════════════════
# /fedresurs — сообщения Федресурса
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_fedresurs(inn: str) -> dict:
    body = await _get("/fedresurs", {"inn": inn})
    if not body:
        return {"fedresurs_count": 0, "fedresurs_messages": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    parsed = []
    for m in items[:5]:
        if isinstance(m, dict):
            parsed.append({
                "type": m.get("type") or m.get("Тип") or "",
                "date": m.get("date") or m.get("Дата") or "",
                "text": (m.get("text") or m.get("Содержание") or m.get("Сообщение") or "")[:250],
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {"fedresurs_count": int(total), "fedresurs_messages": parsed}


# ══════════════════════════════════════════════════════════════════════════════
# fetch_full_profile — всё в одном запросе (параллельно)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_full_profile(inn: str) -> dict:
    """
    Параллельно запрашивает: финансы, арбитраж, ФССП, госзакупки,
    банкротство, проверки, Федресурс. Используется в pipeline вместо fns.py.
    """
    import asyncio

    if not _available():
        return {}

    results = await asyncio.gather(
        fetch_finances(inn),
        fetch_legal_cases(inn),
        fetch_enforcements(inn),
        fetch_contracts(inn),
        fetch_bankruptcy(inn),
        fetch_inspections(inn),
        fetch_fedresurs(inn),
        return_exceptions=True,
    )

    def _safe(r) -> dict:
        return r if isinstance(r, dict) else {}

    fin, legal, enf, contracts, bankrupt, insp, fedresurs = [_safe(r) for r in results]

    return {
        # Финансы
        "revenue": fin.get("revenue"),
        "profit": fin.get("profit"),
        "assets": fin.get("assets"),
        "expense": fin.get("expense"),
        "debt": fin.get("debt"),
        "finance_year": fin.get("finance_year"),
        "revenue_trend": fin.get("revenue_trend", "unknown"),
        "revenue_series": fin.get("revenue_series", []),
        "profit_series": fin.get("profit_series", []),
        # Арбитраж
        "arbitration_count": legal.get("arbitration_count", 0),
        "arbitration_cases": legal.get("cases", []),
        # ФССП
        "enforcement_count": enf.get("enforcement_count", 0),
        "enforcement_debt": enf.get("enforcement_debt", 0),
        "enforcements": enf.get("enforcements", []),
        # Госзакупки
        "contracts_count": contracts.get("contracts_count", 0),
        "contracts_total_amount": contracts.get("contracts_total_amount", 0),
        "contracts": contracts.get("contracts", []),
        # Банкротство
        "has_bankruptcy": bankrupt.get("has_bankruptcy", False),
        "bankruptcy_messages": bankrupt.get("bankruptcy_messages", []),
        # Проверки
        "inspection_count": insp.get("inspection_count", 0),
        "inspections": insp.get("inspections", []),
        # Федресурс
        "fedresurs_count": fedresurs.get("fedresurs_count", 0),
        "fedresurs_messages": fedresurs.get("fedresurs_messages", []),
        "_checko": True,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /person — все компании физического лица (учредитель / директор / ИП)
# ══════════════════════════════════════════════════════════════════════════════


