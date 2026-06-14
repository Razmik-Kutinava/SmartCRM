"""Обогащение лида для голоса: enrich-lead без записи в CRM до апрува."""
from __future__ import annotations

from typing import Any

from voice.lead_context import resolve_lead


def enriched_to_patch(enriched: dict[str, Any]) -> dict[str, Any]:
    """Зеркало frontend enrichedToLeadPatch."""
    if not enriched:
        return {}
    patch: dict[str, Any] = {}
    for key, target in (
        ("phone", "phone"),
        ("email", "email"),
        ("website", "website"),
        ("employees", "employees"),
        ("decision_maker", "contact"),
    ):
        val = enriched.get(key)
        if val:
            patch[target] = val
    if enriched.get("revenue"):
        patch["budget"] = str(enriched["revenue"])
    desc_parts: list[str] = []
    if enriched.get("description"):
        desc_parts.append(str(enriched["description"]))
    if enriched.get("address"):
        desc_parts.append(f"Адрес: {enriched['address']}")
    if enriched.get("linkedin"):
        desc_parts.append(f"LinkedIn: {enriched['linkedin']}")
    if desc_parts:
        patch["description"] = "\n".join(desc_parts)
    return patch


def lead_to_enrich_payload(lead: dict[str, Any]) -> dict[str, Any]:
    return {
        "company": lead.get("company") or "",
        "industry": lead.get("industry") if lead.get("industry") not in (None, "", "—") else "",
        "inn": lead.get("inn") or None,
        "phone": lead.get("phone"),
        "email": lead.get("email"),
        "website": lead.get("website"),
        "address": lead.get("city"),
        "employees": lead.get("employees"),
        "description": lead.get("description"),
    }


async def fetch_enrich_preview(slots: dict[str, Any]) -> dict[str, Any]:
    lead = await resolve_lead(slots)
    if not lead:
        return {
            "agents_ran": False,
            "final_reply": "Лид не найден — назови компанию или номер (#id).",
        }

    company = (lead.get("company") or slots.get("company") or "").strip()
    if not company:
        return {
            "agents_ran": False,
            "final_reply": "У лида нет названия компании — обогащение невозможно.",
        }

    lid = int(lead.get("lead_id") or lead.get("id"))
    payload = lead_to_enrich_payload(lead)
    force = bool(slots.get("force"))

    from rag.search import enrich_lead

    result = await enrich_lead(payload, force=force)
    enriched = result.get("enriched") or {}
    patch = enriched_to_patch(enriched)
    keys = list(patch.keys())

    if not keys:
        msg = f"Для {company} новых полей не найдено."
        if result.get("cached"):
            msg += " (данные из кэша enrich)"
        return {
            "agents_ran": True,
            "final_reply": msg,
            "lead_id": lid,
            "company": company,
            "enrich_output": result,
            "enriched": enriched,
            "patch_preview": patch,
            "cached": bool(result.get("cached")),
        }

    msg = f"Нашёл поля для {company}: {', '.join(keys)}. Подтверди запись в карточку."
    if result.get("cached"):
        msg += " (из кэша enrich, 24 ч)"

    return {
        "agents_ran": True,
        "final_reply": msg,
        "lead_id": lid,
        "company": company,
        "enrich_output": result,
        "enriched": enriched,
        "patch_preview": patch,
        "cached": bool(result.get("cached")),
    }
