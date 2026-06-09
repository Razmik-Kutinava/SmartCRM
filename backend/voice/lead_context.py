"""Контекст лида для голосового пайплайна (история без fanout агентов)."""
from __future__ import annotations

from typing import Any

from agents.tools import (
    read_lead_audit,
    read_lead_by_company,
    read_lead_by_id,
    read_lead_comments,
    read_lead_communications,
)


async def resolve_lead(slots: dict[str, Any]) -> dict | None:
    lid = slots.get("lead_id") or slots.get("id")
    if lid is not None:
        s = str(lid).strip()
        if s.isdigit():
            return await read_lead_by_id(int(s))
    company = slots.get("company")
    if company:
        return await read_lead_by_company(str(company))
    return None


async def fetch_lead_history(slots: dict[str, Any]) -> dict[str, Any]:
    lead = await resolve_lead(slots)
    if not lead:
        return {
            "agents_ran": False,
            "final_reply": "Лид не найден — уточни компанию или номер.",
            "history": {"audit": [], "comments": [], "communications": []},
        }

    lid = int(lead.get("lead_id") or lead.get("id"))
    audit = await read_lead_audit(lid)
    comments = await read_lead_comments(lid)
    comms = await read_lead_communications(lid)
    company = lead.get("company") or slots.get("company") or f"#{lid}"
    n = len(audit) + len(comments) + len(comms)

    return {
        "agents_ran": True,
        "final_reply": f"История лида {company}: {n} записей.",
        "lead_id": lid,
        "company": company,
        "history": {
            "audit": audit[:30],
            "comments": comments[:20],
            "communications": comms[:20],
        },
    }
