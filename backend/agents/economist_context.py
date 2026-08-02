"""Явный фин/паспорт/веб-контекст для экономиста (не «пожелание оператора»)."""
from __future__ import annotations

from typing import Any


def _clean(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text in ("", "—", "-") else text


def finance_brief_from_slots(slots: dict[str, Any], *, max_chars: int = 700) -> str:
    """Выжимка фин.блока из checko / financials / budget."""
    lines: list[str] = []
    checko = slots.get("checko") if isinstance(slots.get("checko"), dict) else {}
    fin = checko.get("financials") if isinstance(checko.get("financials"), dict) else {}
    if not fin and isinstance(slots.get("financials"), dict):
        fin = slots["financials"]
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}

    budget = _clean(slots.get("budget"))
    if budget:
        lines.append(f"Бюджет/сумма в карточке: {budget}")
    emp = _clean(slots.get("employees")) or _clean(company.get("employees_count")) or _clean(
        company.get("employees")
    )
    if emp:
        lines.append(f"Численность: {emp}")
    if fin:
        parts = []
        for k, v in list(fin.items())[:8]:
            if v not in (None, "", "—", {}, []):
                parts.append(f"{k}={v}")
        if parts:
            lines.append("Паспорт financials: " + "; ".join(parts))
    for key in ("revenue", "turnover", "выручка", "оборот"):
        if _clean(company.get(key)):
            lines.append(f"{key}: {company[key]}")
    brief = _clean(slots.get("web_research_brief") or "")
    if brief and any(
        m in brief.lower()
        for m in ("выручка", "оборот", "млн", "млрд", "revenue", "фин")
    ):
        # кусок brief с финансами
        snippet = brief
        for marker in ("выручка", "оборот", "финанс", "## 4", "## 3"):
            idx = brief.lower().find(marker)
            if idx >= 0:
                snippet = brief[max(0, idx - 40) : idx + 320]
                break
        lines.append(f"Из веб-исследования: {snippet.strip()[:400]}")
    text = "\n".join(lines)
    return text[:max_chars]


def build_economist_context_lines(slots: dict[str, Any]) -> list[str]:
    """Строки user-промпта: карточка + явный фин/паспорт/🔍."""
    lines: list[str] = []
    company = _clean(slots.get("company"))
    if company:
        lines.append(f"Компания: {company}")
    industry = _clean(slots.get("industry"))
    if industry:
        lines.append(f"Отрасль: {industry}")
    city = _clean(slots.get("city"))
    if city:
        lines.append(f"Город: {city}")
    stage = _clean(slots.get("stage"))
    if stage:
        lines.append(f"Этап воронки: {stage}")

    fin_block = finance_brief_from_slots(slots)
    if fin_block:
        lines.append("ФИНАНСЫ / ПАСПОРТ (приоритетнее эвристик):")
        lines.extend(f"  {ln}" if not ln.startswith(" ") else ln for ln in fin_block.split("\n"))
    else:
        lines.append("ФИНАНСЫ / ПАСПОРТ: явных цифр нет — оценка-эвристика по отрасли/численности")

    brief = _clean(slots.get("web_research_brief") or "")
    if brief and "Из веб-исследования" not in (fin_block or ""):
        lines.append(f"ВЕБ-ИССЛЕДОВАНИЕ (кратко): {brief[:500]}")

    passport = ""
    checko = slots.get("checko") if isinstance(slots.get("checko"), dict) else {}
    co = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    for key, label in (("inn", "ИНН"), ("okved", "ОКВЭД"), ("okved_name", "ОКВЭД")):
        if _clean(co.get(key)):
            lines.append(f"{label}: {co[key]}")
            break

    desc = _clean(slots.get("description") or "")
    if desc:
        lines.append(f"Заметки карточки: {desc[:500]}")

    return lines
