"""Persist lead card to CRM."""
from __future__ import annotations

import logging
from typing import Any

from .utils import _fmt_money

logger = logging.getLogger(__name__)

async def _save_to_crm(card: dict) -> int | None:
    """Сохраняет карточку лида в CRM — все поля включая Checko JSON."""
    import json as _json
    try:
        from db.session import get_db_session
        from db.models import Lead

        lpr = card.get("lpr", {}) or {}
        fin = card.get("financials", {}) or {}
        tech = card.get("tech_stack", {}) or {}

        # Описание — краткий дайджест
        notes_parts = []
        if card.get("inn"):
            notes_parts.append(f"ИНН: {card['inn']}  ОГРН: {card.get('ogrn', '—')}")
        if card.get("address"):
            notes_parts.append(f"Адрес: {card['address']}")
        if card.get("okved_name"):
            notes_parts.append(f"ОКВЭД: {card['okved']} — {card['okved_name']}")
        if fin.get("revenue"):
            notes_parts.append(f"Выручка: {_fmt_money(fin['revenue'])} ({fin.get('finance_year', '—')} г.)")
        if card.get("hook"):
            notes_parts.append(f"Крючок: {card['hook']}")
        if card.get("script"):
            notes_parts.append(f"Скрипт:\n{card['script']}")
        if card.get("triggers"):
            notes_parts.append(f"Триггеры: {', '.join(str(t) for t in card['triggers'])}")

        phone = lpr.get("phone") or (lpr.get("dadata_phones") or ["—"])[0]

        lead_data = {
            "company": card.get("company_name", ""),
            "contact": lpr.get("name", "—"),
            "email": lpr.get("email") or (lpr.get("dadata_emails") or ["—"])[0],
            "phone": phone,
            "position": lpr.get("role", "—"),
            "website": card.get("website", "—"),
            "industry": card.get("industry", "—"),
            "city": card.get("city", "—"),
            "score": card.get("final_score", 50),
            "source": "Лидогенератор",
            "stage": "Новый",
            "description": "\n\n".join(notes_parts),
            # Новые поля
            "inn": card.get("inn", ""),
            "ogrn": card.get("ogrn", ""),
            "checko_json": _json.dumps(
                {
                    "company": {
                        "kpp": card.get("kpp"),
                        "address": card.get("address"),
                        "registration_date": card.get("registration_date"),
                        "okved": card.get("okved"),
                        "okved_name": card.get("okved_name"),
                        "smb_category": card.get("smb_category"),
                        "employees_count": card.get("employees_count"),
                        "status": card.get("company_status"),
                        "management_type": card.get("management_type"),
                        "branch_count": card.get("branch_count"),
                        "founders": card.get("founders", []),
                        "related_companies": card.get("related_companies", []),
                        "risk_flags": card.get("risk_flags", {}),
                        "licenses": fin.get("licenses", []),
                        "phones": lpr.get("dadata_phones", []),
                        "emails": lpr.get("dadata_emails", []),
                    },
                    "financials": fin,
                    "tech": tech,
                    "analyses": card.get("analyses", {}),
                    "agent_outputs": card.get("agent_outputs", {}),
                    "news": card.get("news", []),
                },
                ensure_ascii=False,
                default=str,
            ),
            "tech_json": _json.dumps(tech, ensure_ascii=False, default=str),
            "financials_json": _json.dumps(fin, ensure_ascii=False, default=str),
        }

        async with get_db_session() as db:
            lead = Lead(**lead_data)
            db.add(lead)
            await db.commit()
            await db.refresh(lead)
            return lead.id
    except Exception as e:
        logger.error("Не удалось сохранить лид в CRM: %s", e)
        return None



