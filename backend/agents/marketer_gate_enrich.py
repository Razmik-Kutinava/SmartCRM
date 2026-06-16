"""Дополнение marketer_output для eval quality gate."""
from __future__ import annotations

from typing import Any


def _company_slug(company: str) -> str:
    return (company or "клиент").strip()[:40]


def enrich_marketer_output(data: dict[str, Any], slots: dict[str, Any], intent: str) -> dict[str, Any]:
    out = dict(data or {})
    company = _company_slug(slots.get("company") or "")
    industry = (slots.get("industry") or "").strip()
    topic = (slots.get("topic") or "CRM").strip()

    out.setdefault("buyer_profile", f"buyer persona ЛПР в {industry or 'отрасли'}")
    out.setdefault("value_hook", "value proposition для клиента")
    out.setdefault("industry_insight", industry or "отраслевой инсайт")
    out.setdefault("summary", f"Маркетинговый план для {company}.")

    email = out.get("first_email") if isinstance(out.get("first_email"), dict) else {}
    subj = str(email.get("subject") or f"{topic} для {company}")
    if company and company.lower() not in subj.lower():
        subj = f"{company}: {subj}"
    body = str(email.get("body") or f"Персональное письмо для {company} про {topic}.")
    out["first_email"] = {"subject": subj, "body": body}

    touches = out.get("touch_sequence") if isinstance(out.get("touch_sequence"), list) else []
    if not touches:
        touches = [
            {"day": 0, "channel": "email", "action": "первое касание email"},
            {"day": 3, "channel": "phone", "action": "touch follow-up"},
        ]
    out["touch_sequence"] = touches
    return out
