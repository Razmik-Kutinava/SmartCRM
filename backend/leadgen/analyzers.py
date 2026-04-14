"""
5 анализов профиля компании для лидогенерации.
Каждый анализ принимает собранные данные и возвращает структурированный вывод.
"""
from __future__ import annotations
from typing import Any


def analyze_it_maturity(profile: dict) -> dict:
    """
    Анализ 1: IT-зрелость
    Источники: BuiltWith (стек), новости (найм IT), вакансии
    Вывод: базовый/оптимизация/энтерпрайз → какой продукт предлагать
    """
    tech = profile.get("tech", {}) or {}
    news = profile.get("news", []) or []
    financials = profile.get("financials", {}) or {}

    maturity_raw = tech.get("maturity_level", "unknown")
    tech_count = tech.get("tech_count", 0)
    has_crm = tech.get("has_crm", False)
    has_analytics = tech.get("has_analytics", False)

    # Сигналы из новостей: упоминание найма IT
    it_hiring = any(
        kw in (a.get("title", "") + a.get("description", "")).lower()
        for a in news
        for kw in ("разработчик", "devops", "it директор", "цифровиза", "автоматизация")
    )

    # Определяем уровень
    if maturity_raw == "enterprise" or tech_count > 30:
        level = "enterprise"
        recommendation = "Энтерпрайз-продукты: ManageEngine Enterprise Suite, ITSM"
    elif maturity_raw in ("high", "medium") or tech_count > 10 or has_crm:
        level = "optimization"
        recommendation = "Оптимизация: OpManager, Log360, AD360"
    else:
        level = "basic"
        recommendation = "Базовый старт: ServiceDesk Plus, Desktop Central"

    return {
        "level": level,
        "tech_count": tech_count,
        "has_crm": has_crm,
        "has_analytics": has_analytics,
        "it_hiring_signal": it_hiring,
        "recommendation": recommendation,
        "score_impact": {"enterprise": 20, "optimization": 15, "basic": 5}.get(level, 5),
    }


def analyze_decision_structure(profile: dict) -> dict:
    """
    Анализ 2: Структура принятия решений
    Источники: DaData (учредители, директора), ФНС (филиалы)
    Вывод: собственник/наёмный директор/совет → кому писать
    """
    company = profile.get("company", {}) or {}
    financials = profile.get("financials", {}) or {}

    management_type = company.get("management_type", "hired_director")
    director = company.get("director", "")
    founders = company.get("founders") or []
    branch_count = company.get("branch_count", 0)

    # Определяем ЛПР
    lpr_role = "Генеральный директор"
    lpr_name = director
    decision_level = "director"

    if management_type == "owner_managed":
        lpr_role = "Собственник / Генеральный директор"
        decision_level = "owner"
    elif management_type == "board" or len(founders) > 3:
        lpr_role = "Совет директоров / Топ-менеджмент"
        decision_level = "board"

    # Если крупная компания — нужен IT-директор
    revenue = (profile.get("financials") or {}).get("revenue") or 0
    if revenue and float(revenue or 0) > 500_000_000:  # >500 млн
        secondary_lpr = "IT-директор / CTO"
    elif branch_count > 5:
        secondary_lpr = "Руководитель IT-отдела"
    else:
        secondary_lpr = None

    return {
        "management_type": management_type,
        "decision_level": decision_level,
        "lpr_role": lpr_role,
        "lpr_name": lpr_name,
        "secondary_lpr": secondary_lpr,
        "founders_count": len(founders),
        "branch_count": branch_count,
        "founders": founders[:5],  # первые 5
        "approach_recommendation": _decision_approach(decision_level),
        "score_impact": {"owner": 15, "director": 10, "board": 5}.get(decision_level, 10),
    }


def analyze_vendor_landscape(profile: dict) -> dict:
    """
    Анализ 3: Вендор-ландшафт
    Источники: BuiltWith (текущие инструменты)
    Вывод: встроимся/заменим/дополним → как позиционировать
    """
    tech = profile.get("tech", {}) or {}
    all_techs = [t.lower() for t in (tech.get("all_technologies") or [])]
    crm_tools = tech.get("crm") or []
    by_cat = tech.get("by_category") or {}

    # Наши конкуренты в стеке
    competitors = {
        "replace": [],
        "integrate": [],
        "complement": [],
    }
    our_competitors = {
        "servicenow": "replace",
        "jira service": "replace",
        "zendesk": "replace",
        "freshdesk": "replace",
        "microsoft teams": "integrate",
        "slack": "integrate",
        "google workspace": "integrate",
        "azure ad": "complement",
        "active directory": "complement",
    }
    for tech_name, position in our_competitors.items():
        if any(tech_name in t for t in all_techs):
            competitors[position].append(tech_name)

    if competitors["replace"]:
        strategy = "replace"
        positioning = f"Заменить: {', '.join(competitors['replace'])}"
    elif competitors["integrate"]:
        strategy = "integrate"
        positioning = f"Интегрироваться с: {', '.join(competitors['integrate'])}"
    else:
        strategy = "complement"
        positioning = "Дополнить текущую инфраструктуру"

    gaps = []
    if not tech.get("has_crm"):
        gaps.append("Нет CRM системы")
    if not any("monitor" in t for t in all_techs):
        gaps.append("Нет мониторинга инфраструктуры")
    if not any("antivirus" in t or "security" in t for t in all_techs):
        gaps.append("Нет видимых инструментов безопасности")

    return {
        "strategy": strategy,
        "positioning": positioning,
        "competitors_found": competitors,
        "gaps": gaps,
        "current_crm": crm_tools,
        "total_tools": len(all_techs),
        "score_impact": {"replace": 20, "complement": 15, "integrate": 10}.get(strategy, 10),
    }


def analyze_growth_trajectory(profile: dict) -> dict:
    """
    Анализ 4: Траектория роста
    Источники: ФНС (динамика финансов), новости (инвестиции/найм), тендеры
    Вывод: растут/стабильны/падают → какой аргумент работает
    """
    fin = profile.get("financials", {}) or {}
    news = profile.get("news", []) or []

    trend = fin.get("revenue_trend", "unknown")
    revenue = fin.get("revenue")
    profit = fin.get("profit")

    # Сигналы роста из новостей
    growth_signals = []
    decline_signals = []
    for a in news:
        text = (a.get("title", "") + " " + a.get("description", "")).lower()
        if any(kw in text for kw in ("инвестиции", "раунд", "расширение", "найм", "открытие")):
            growth_signals.append(a.get("title", "")[:80])
        if any(kw in text for kw in ("банкротство", "увольнение", "сокращение", "долги", "убыток")):
            decline_signals.append(a.get("title", "")[:80])

    # Финальная оценка
    if trend == "growing" or len(growth_signals) >= 2:
        trajectory = "growing"
        argument = "Масштабирование: нужны инструменты для роста без увеличения команды"
    elif trend == "declining" or len(decline_signals) >= 1:
        trajectory = "declining"
        argument = "Оптимизация: сократить расходы и повысить эффективность IT"
    else:
        trajectory = "stable"
        argument = "Зрелость: пора обновить устаревшие инструменты, не теряя стабильности"

    return {
        "trajectory": trajectory,
        "revenue": revenue,
        "profit": profit,
        "revenue_trend": trend,
        "growth_signals": growth_signals[:3],
        "decline_signals": decline_signals[:2],
        "sales_argument": argument,
        "score_impact": {"growing": 20, "stable": 10, "declining": 5}.get(trajectory, 10),
    }


def analyze_security_compliance(profile: dict) -> dict:
    """
    Анализ 5: Безопасность и комплаенс
    Источники: ФНС (лицензии), BuiltWith (защита), новости (инциденты)
    Вывод: базовая/сертифицированная → какой продукт
    """
    fin = profile.get("financials", {}) or {}
    tech = profile.get("tech", {}) or {}
    news = profile.get("news", []) or []
    company = profile.get("company", {}) or {}

    licenses = fin.get("licenses", []) or []
    security_tools = tech.get("security") or []
    okved = company.get("okved", "")

    # Регулируемые отрасли — требуют сертификации
    regulated_okveds = ["64", "65", "66", "86", "84", "85"]  # финансы, здравоохранение, госструктуры
    is_regulated = any(okved.startswith(r) for r in regulated_okveds)

    # Инциденты безопасности в новостях
    security_incidents = [
        a.get("title", "")[:80] for a in news
        if any(kw in (a.get("title", "") + a.get("description", "")).lower()
               for kw in ("утечка", "взлом", "кибератак", "хакер", "инцидент"))
    ]

    if is_regulated or licenses or len(security_tools) > 3:
        level = "certified"
        product_rec = "ManageEngine PAM360, Log360 (SIEM), DataSecurity Plus"
    elif security_incidents:
        level = "incident_driven"
        product_rec = "Log360 + Incident Management — срочно нужна защита"
    else:
        level = "basic"
        product_rec = "Desktop Central + Endpoint Security — базовый старт"

    return {
        "compliance_level": level,
        "is_regulated_industry": is_regulated,
        "licenses_found": licenses,
        "security_tools": security_tools,
        "security_incidents": security_incidents[:2],
        "product_recommendation": product_rec,
        "score_impact": {"certified": 15, "incident_driven": 20, "basic": 5}.get(level, 5),
    }


def compute_profile_analyses(profile: dict) -> dict:
    """Запускает все 5 анализов и возвращает суммарный impact на скор."""
    it_maturity = analyze_it_maturity(profile)
    decision_struct = analyze_decision_structure(profile)
    vendor_landscape = analyze_vendor_landscape(profile)
    growth = analyze_growth_trajectory(profile)
    security = analyze_security_compliance(profile)

    total_impact = (
        it_maturity["score_impact"]
        + decision_struct["score_impact"]
        + vendor_landscape["score_impact"]
        + growth["score_impact"]
        + security["score_impact"]
    )

    return {
        "it_maturity": it_maturity,
        "decision_structure": decision_struct,
        "vendor_landscape": vendor_landscape,
        "growth_trajectory": growth,
        "security_compliance": security,
        "profile_score_impact": min(total_impact, 40),  # макс +40 к базовому скору
    }


def _decision_approach(level: str) -> str:
    mapping = {
        "owner": "Прямое обращение к собственнику: акцент на ROI и контроле бизнеса",
        "director": "Директор: акцент на снижении рисков и операционной эффективности",
        "board": "Совет: нужен внутренний чемпион, подготовь материалы для презентации",
    }
    return mapping.get(level, "Найди ЛПР перед контактом")
