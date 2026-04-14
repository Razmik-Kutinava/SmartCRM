"""
ФНС / ЕГРЮЛ — финансовые данные и юридическая информация.
Используем открытый API egrul.nalog.ru (без ключа, лимит мягкий).
ENV: FNS_API_KEY (опционально, для расширенных данных)
"""
from __future__ import annotations
import asyncio
import logging
import os
import httpx

logger = logging.getLogger(__name__)

EGRUL_URL = "https://egrul.nalog.ru/search-result"
BO_URL = "https://bo.nalog.ru/nbo/organizations"  # бухгалтерская отчётность


async def fetch_financials(inn: str) -> dict:
    """Получить финансовые данные по ИНН."""
    tasks = [
        _fetch_egrul(inn),
        _fetch_bo(inn),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    egrul = results[0] if not isinstance(results[0], Exception) else {}
    bo = results[1] if not isinstance(results[1], Exception) else {}

    return {
        "inn": inn,
        "egrul": egrul,
        "financials": bo,
        "revenue": bo.get("revenue"),
        "profit": bo.get("profit"),
        "assets": bo.get("assets"),
        "revenue_trend": bo.get("revenue_trend"),  # "growing"|"stable"|"declining"
        "arbitration_count": egrul.get("arbitration_count", 0),
        "has_bankruptcy": egrul.get("has_bankruptcy", False),
        "licenses": egrul.get("licenses", []),
        "tax_debt": egrul.get("tax_debt"),
    }


async def _fetch_egrul(inn: str) -> dict:
    """Базовая инфо из ЕГРЮЛ."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(EGRUL_URL, params={"query": inn, "region": "", "page": ""})
            if r.status_code != 200:
                return {}
            data = r.json()
            rows = data.get("rows", [])
            if not rows:
                return {}
            row = rows[0]
            return {
                "ogrn": row.get("o", ""),
                "reg_date": row.get("r", ""),
                "liquidation_date": row.get("lDate"),
                "has_bankruptcy": bool(row.get("lDate")),
                "arbitration_count": 0,
                "licenses": [],
            }
    except Exception as e:
        logger.debug("ЕГРЮЛ fetch failed for %s: %s", inn, e)
        return {}


async def _fetch_bo(inn: str) -> dict:
    """Бухгалтерская отчётность из bo.nalog.ru."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Ищем организацию
            r = await client.get(f"{BO_URL}/search", params={"query": inn})
            if r.status_code != 200:
                return {}
            items = r.json()
            if not items:
                return {}
            org_id = items[0].get("id")
            if not org_id:
                return {}
            # Получаем отчётность
            r2 = await client.get(f"{BO_URL}/{org_id}/charts")
            if r2.status_code != 200:
                return {}
            charts = r2.json()
            return _parse_bo_charts(charts)
    except Exception as e:
        logger.debug("bo.nalog.ru fetch failed for %s: %s", inn, e)
        return {}


def _parse_bo_charts(charts: list) -> dict:
    """Парсим данные финансовой отчётности."""
    revenue_series = []
    profit_series = []
    assets_val = None

    for item in (charts or []):
        code = item.get("code", "")
        values = item.get("values", []) or []
        if code == "2110":  # Выручка
            revenue_series = [(v.get("year"), v.get("value")) for v in values if v.get("value")]
        elif code == "2400":  # Чистая прибыль
            profit_series = [(v.get("year"), v.get("value")) for v in values if v.get("value")]
        elif code == "1600":  # Активы
            if values:
                assets_val = values[-1].get("value")

    revenue = revenue_series[-1][1] if revenue_series else None
    profit = profit_series[-1][1] if profit_series else None

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
        "revenue_trend": trend,
        "revenue_series": revenue_series[-3:],
        "profit_series": profit_series[-3:],
    }
