"""Персонализация шаблона массовой рассылки."""
from __future__ import annotations

from db.models import Lead


def render_campaign_text(
    template: str,
    lead: Lead,
    *,
    product: str = "",
    sender_name: str = "Иван Б.",
    sender_email: str = "ib@agneko.com",
) -> str:
    contact = (lead.contact or "").strip()
    greeting = f"Здравствуйте, {contact}!" if contact and contact != "—" else "Здравствуйте!"
    sender = f"{sender_name}, {sender_email}, Agneko"
    repl = {
        "{{company}}": (lead.company or "").strip() or "ваша компания",
        "{{contact}}": contact,
        "{{product}}": product,
        "{{greeting}}": greeting,
        "{{sender}}": sender,
    }
    out = template or ""
    for k, v in repl.items():
        out = out.replace(k, v)
    return out
