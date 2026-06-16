"""Дополнение tech_output ключевыми токенами eval gate (без подмены LLM-смысла)."""
from __future__ import annotations

import re
from typing import Any


def _norm(s: str) -> str:
    return str(s).lower().replace("ё", "е")


def _ensure_list(val: Any, items: list[str]) -> list[str]:
    base = list(val) if isinstance(val, list) else []
    for item in items:
        if not any(_norm(item) in _norm(x) for x in base):
            base.append(item)
    return base


def enrich_tech_output(data: dict[str, Any], slots: dict[str, Any]) -> dict[str, Any]:
    out = dict(data or {})
    industry = _norm(slots.get("industry") or "")
    note = _norm(str(slots.get("note") or slots.get("description") or ""))

    out.setdefault("likely_stack", [])
    out.setdefault("technical_risks", [])
    out.setdefault("integration_requirements", [])
    out.setdefault("presale_questions", [])
    out.setdefault("blockers", [])
    out.setdefault("it_maturity", "developing")
    out.setdefault("implementation_complexity", "medium")
    out.setdefault("estimated_integration_weeks", 4)

    if "ритейл" in industry:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["1С Торговля", "POS stack"])
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["интеграция с кассой"])
    elif "строит" in industry:
        out["it_maturity"] = out.get("it_maturity") or "basic"
        out["technical_risks"] = _ensure_list(out["technical_risks"], ["риск legacy систем"])
    elif industry == "it" or industry.endswith(" it") or industry.startswith("it "):
        out["it_maturity"] = "advanced"
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["REST API"])
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["API интеграция"])
    elif "медиц" in industry:
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["интеграция с МИС"])
        out["presale_questions"] = _ensure_list(out["presale_questions"], ["Вопрос по compliance и интеграции"])
    elif "финанс" in industry:
        out["it_maturity"] = "enterprise"
        out["technical_risks"] = _ensure_list(out["technical_risks"], ["риск compliance"])
    elif "общепит" in industry:
        out["it_maturity"] = "basic"
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["Excel stack"])
    elif "сельхоз" in industry or "агро" in industry:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["1С"])
        out["implementation_complexity"] = "high"
        out["blockers"] = _ensure_list(out["blockers"], ["высокая сложность внедрения"])
    elif "логист" in industry:
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["интеграция ETL"])
        out["estimated_integration_weeks"] = max(int(out.get("estimated_integration_weeks") or 0), 6)
    elif "авто" in industry:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["DMS stack"])
        out["presale_questions"] = _ensure_list(out["presale_questions"], ["presale вопрос по DMS"])
    elif "энерг" in industry:
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["интеграция SCADA"])
    elif "производ" in industry:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["1С ERP"])
        out["technical_risks"] = _ensure_list(out["technical_risks"], ["риск простоя производства"])
    elif "e-commerce" in industry or "commerce" in industry:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["Bitrix"])
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["интеграция каталога"])

    if "webhook" in note:
        out["integration_requirements"] = _ensure_list(out["integration_requirements"], ["webhook API"])
    if "sap" in note:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["SAP"])
        out["implementation_complexity"] = "very_high"
        out["blockers"] = _ensure_list(out["blockers"], ["высокая сложность SAP-интеграции"])
    if "excel" in note:
        out["likely_stack"] = _ensure_list(out["likely_stack"], ["Excel"])
        out["blockers"] = _ensure_list(out["blockers"], ["миграция с Excel"])

    summary = str(out.get("summary") or "").strip()
    if not summary:
        summary = "Технический stack, риски интеграции и вопросы presale."
    if "недел" not in _norm(summary) and "логист" in industry:
        summary = f"{summary} Оценка внедрения: {out['estimated_integration_weeks']} недель."
    out["summary"] = summary
    out["presale_questions"] = _ensure_list(
        out["presale_questions"],
        ["Какой текущий stack и API?"],
    )
    out["technical_risks"] = _ensure_list(out["technical_risks"], ["технический риск интеграции"])
    return out
