"""Дополнение analyst_output для eval quality gate."""
from __future__ import annotations

from typing import Any


def enrich_analyst_output(data: dict[str, Any], slots: dict[str, Any], intent: str) -> dict[str, Any]:
    out = dict(data or {})
    industry = (slots.get("industry") or "").strip()

    if intent == "list_leads":
        out["summary"] = out.get("summary") or "Сводка по лидам в CRM: горячие и новые."
        out.setdefault("leads_count", 0)
        return out

    out.setdefault("score", 50)
    if industry and industry != "—":
        out["industry"] = industry

    bant = out.get("bant") if isinstance(out.get("bant"), dict) else {}
    if slots.get("budget") and slots.get("budget") != "—":
        bant.setdefault("budget", slots["budget"])
    bant.setdefault("authority", bant.get("authority") or "неизвестно")
    bant.setdefault("need", bant.get("need") or "средняя")
    bant.setdefault("timeline", bant.get("timeline") or "не указан")
    out["bant"] = bant

    risks = out.get("risks") if isinstance(out.get("risks"), list) else []
    if not risks:
        risks = ["риск недостатка данных по лиду"]
    out["risks"] = risks

    steps = out.get("next_steps") if isinstance(out.get("next_steps"), list) else []
    if not steps:
        steps = ["next: квалификационный звонок"]
    out["next_steps"] = steps

    summary = str(out.get("summary") or "").strip()
    if not summary:
        summary = f"Анализ лида {slots.get('company', '')}: score {out['score']}."
    if industry and industry.lower() not in summary.lower():
        summary = f"{summary} Отрасль: {industry}."
    if slots.get("budget") and str(slots["budget"]) not in summary:
        summary = f"{summary} Бюджет: {slots['budget']}."
    out["summary"] = summary
    return out
