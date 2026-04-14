"""
BuiltWith Free API — технологический стек сайта компании.
API: https://api.builtwith.com/free1/api.json
ENV: BUILTWITH_API_KEY

Free API возвращает groups[] с categories[] (не отдельные технологии как в Paid API).
Структура: {"domain":..., "groups": [{"name":"cms", "categories":[{"name":"CMS","live":N},...]},...]}
"""
from __future__ import annotations
import logging
import os
import httpx

logger = logging.getLogger(__name__)

BUILTWITH_URL = "https://api.builtwith.com/free1/api.json"

# Маппинг BuiltWith группы → наши категории
GROUP_TO_CATEGORY = {
    "cms": "cms",
    "analytics": "analytics",
    "javascript": "javascript",
    "ssl": "security",
    "cdn": "hosting",
    "hosting": "hosting",
    "ns": "hosting",
    "email": "email",
    "payment": "ecommerce",
    "shop": "ecommerce",
    "ecommerce": "ecommerce",
    "crm": "crm",
    "marketing": "marketing",
    "advertising": "marketing",
    "social": "social",
    "chat": "chat",
    "widgets": "widgets",
}

# Категории которые сигнализируют о CRM
CRM_CATEGORY_KEYWORDS = ["crm", "marketing automation", "marketing platform", "customer"]
ANALYTICS_KEYWORDS = ["analytics", "measurement", "tag manager", "tracking"]
ENTERPRISE_KEYWORDS = ["enterprise", "integrated business", "erp", "workflow"]
ECOMMERCE_KEYWORDS = ["ecommerce", "payment", "shop"]
SECURITY_KEYWORDS = ["ssl", "security", "firewall", "waf"]


async def fetch_tech_stack(domain: str) -> dict:
    """Получить технологический стек домена."""
    if not domain:
        return {}
    domain = _clean_domain(domain)
    if not domain:
        return {}

    api_key = os.getenv("BUILTWITH_API_KEY", "")
    if not api_key:
        logger.debug("BUILTWITH_API_KEY не задан — пропускаем BuiltWith")
        return {"_skipped": True, "reason": "no_api_key"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(BUILTWITH_URL, params={"KEY": api_key, "LOOKUP": domain})
            r.raise_for_status()
            data = r.json()

            # Ошибки API (например "Not a valid domain")
            if data.get("Errors") or data.get("error"):
                errs = data.get("Errors") or []
                logger.debug("BuiltWith error for %s: %s", domain, errs)
                return {"_error": True, "domain": domain}

            return _parse_response(data, domain)
    except Exception as e:
        logger.warning("BuiltWith fetch failed for %s: %s", domain, e)
        return {}


def _clean_domain(url: str) -> str:
    if not url:
        return ""
    url = url.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if url.startswith(prefix):
            url = url[len(prefix):]
    domain = url.split("/")[0].split("?")[0]
    # Убираем невалидные домены
    if not domain or "." not in domain or len(domain) > 100:
        return ""
    # BuiltWith не принимает .ru домены для некоторых компаний - возвращаем как есть
    return domain


def _parse_response(data: dict, domain: str) -> dict:
    """
    Парсит ответ Free API BuiltWith.
    Структура: {"groups": [{"name": "cms", "live": N, "categories": [{"name": "...", "live": N}]}]}
    """
    groups = data.get("groups") or []

    # Сбор всех категорий (живых технологий)
    all_categories: list[str] = []
    by_group: dict[str, list[str]] = {}

    for group in groups:
        group_name = (group.get("name") or "other").lower()
        cats = group.get("categories") or []
        live_cats = []
        for cat in cats:
            cat_name = cat.get("name") or ""
            live = cat.get("live") or 0
            if live > 0 and cat_name:
                live_cats.append(cat_name)
                all_categories.append(cat_name)
        if live_cats:
            by_group[group_name] = live_cats

    # Определяем наличие ключевых технологий по категориям
    all_lower = [c.lower() for c in all_categories]

    crm_tools = _filter_by_keywords(all_categories, CRM_CATEGORY_KEYWORDS)
    analytics = _filter_by_keywords(all_categories, ANALYTICS_KEYWORDS)
    security = _filter_by_keywords(all_categories, SECURITY_KEYWORDS)
    ecommerce = _filter_by_keywords(all_categories, ECOMMERCE_KEYWORDS)
    enterprise = _filter_by_keywords(all_categories, ENTERPRISE_KEYWORDS)

    # Всего живых технологических групп
    total_live = sum(g.get("live") or 0 for g in groups if (g.get("live") or 0) > 0)
    group_count = len(by_group)

    maturity = _assess_maturity(group_count, bool(enterprise), bool(crm_tools), total_live)

    # Список технологических категорий как "стек" (для UI)
    tech_list = all_categories[:30]

    return {
        "domain": domain,
        "all_technologies": tech_list,      # список категорий (в free API нет имён продуктов)
        "by_category": by_group,
        "crm": crm_tools,
        "analytics": analytics,
        "hosting": by_group.get("hosting") or by_group.get("cdn") or by_group.get("ns") or [],
        "cms": by_group.get("cms") or [],
        "security": security,
        "ecommerce": ecommerce,
        "enterprise": enterprise,
        "tech_count": group_count,          # число технологических групп (не отдельных продуктов)
        "tech_signals": total_live,         # число живых технологических записей
        "maturity_level": maturity,
        "has_crm": bool(crm_tools),
        "has_analytics": bool(analytics),
        "has_ecommerce": bool(ecommerce),
        "has_enterprise": bool(enterprise),
    }


def _filter_by_keywords(categories: list[str], keywords: list[str]) -> list[str]:
    """Фильтрует категории по ключевым словам."""
    result = []
    for cat in categories:
        cat_lower = cat.lower()
        if any(kw in cat_lower for kw in keywords):
            result.append(cat)
    return result


def _assess_maturity(group_count: int, has_enterprise: bool, has_crm: bool, total_signals: int) -> str:
    if has_enterprise or total_signals > 50:
        return "enterprise"
    if group_count > 8 or has_crm or total_signals > 20:
        return "high"
    if group_count > 4 or total_signals > 10:
        return "medium"
    return "low"
