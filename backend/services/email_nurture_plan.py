"""План 20 касаний: шаблоны маркетолога + персонализация по лиду."""
from __future__ import annotations

import os
from typing import Any

from db.models import Lead

_CHANNELS = ("email", "phone", "linkedin", "email")


def personalize_touch(text: str, lead: Lead, product: str = "") -> str:
    """Подстановка имени компании/контакта при отправке (как в campaigns)."""
    prod = product or os.getenv("NURTURE_PRODUCT_NAME", "новый продукт")
    contact = (lead.contact or "").strip()
    greeting = f"Здравствуйте, {contact}!" if contact else "Здравствуйте!"
    return (
        (text or "")
        .replace("{{greeting}}", greeting)
        .replace("{{company}}", lead.company or "ваша компания")
        .replace("{{contact}}", contact)
        .replace("{{product}}", prod)
    )


def build_20_touch_plan(lead: Lead, *, product: str | None = None) -> list[dict[str, Any]]:
    """20 касаний: email с {{company}}/{{contact}}, звонок/LinkedIn → задачи."""
    prod = product or os.getenv("NURTURE_PRODUCT_NAME", "новый продукт")
    steps: list[dict[str, Any]] = []
    for i in range(20):
        ch = _CHANNELS[i % len(_CHANNELS)]
        day = i * 3
        if ch == "email":
            subj = f"{{{{company}}}} — {prod} · касание {i + 1}"
            body = (
                "{{greeting}}\n\n"
                f"Пишем по поводу внедрения {prod} в {{{{company}}}} "
                f"(шаг {i + 1} из 20).\n"
                "Готовы коротко показать ценность и ответить на вопросы.\n\n"
                "С уважением,\nКоманда Agneko"
            )
            steps.append(
                {
                    "day": day,
                    "channel": ch,
                    "action": f"Email {i + 1}",
                    "subject": subj,
                    "body": body,
                    "product": prod,
                }
            )
        elif ch == "phone":
            steps.append(
                {
                    "day": day,
                    "channel": ch,
                    "action": f"Звонок — {{{{company}}}}",
                    "subject": "",
                    "body": "",
                    "product": prod,
                }
            )
        else:
            steps.append(
                {
                    "day": day,
                    "channel": ch,
                    "action": f"LinkedIn — {{{{company}}}} · касание {i + 1}",
                    "subject": "",
                    "body": "",
                    "product": prod,
                }
            )
    return steps
