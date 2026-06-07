"""
Composable prompt profiles for Hermes.
"""
from __future__ import annotations

PROMPT_MODULES = {
    "identity": "Ты — JSON-роутер CRM. Возвращай только валидный JSON.",
    "intents": (
        "Интенты: create_lead, update_lead, delete_lead, list_leads, "
        "create_task, list_tasks, update_task, delete_task, "
        "run_analysis, ask_economist, ask_marketer, ask_tech, ask_strategist, "
        "search_web, write_email, generate_lead, find_leads_portrait, cluster_company, noop"
    ),
    "routing": (
        "Маршрутизация: финансы->ask_economist; маркетинг->ask_marketer; "
        "IT/интеграции->ask_tech; стратегия->ask_strategist; "
        "анализ компании/лида->run_analysis."
    ),
    "constraints": "Не выдумывай слоты. Заполняй только явно найденные параметры.",
    "format": '{"intent":"...","agents":[...],"slots":{...},"parallel":false,"reply":"..."}',
}


def build_profile(name: str) -> str:
    key = (name or "").strip().lower()
    # compact-modular is shortest profile with enough routing constraints.
    if key in ("compact-modular", "modular", "compact"):
        parts = [
            PROMPT_MODULES["identity"],
            PROMPT_MODULES["intents"],
            PROMPT_MODULES["routing"],
            PROMPT_MODULES["constraints"],
            f'Формат: {PROMPT_MODULES["format"]}',
        ]
        return "\n".join(parts)
    return ""

