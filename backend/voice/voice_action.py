"""Сборка пакета voice_action для WebSocket → SvelteKit (ARCHITECTURE.md)."""
from __future__ import annotations

import re
from typing import Any

from core.hermes.lead_list_view import list_leads_view_from_slots
from core.hermes.module_contract import ANALYTICS_INTENTS, MODULE_ROUTES, RAG_INTENTS

_UI_MODAL_INTENTS = frozenset({
    "write_email", "run_analysis", "ask_economist", "ask_marketer",
    "ask_tech", "ask_strategist", "analyze_lead", "search_web", "ask_rag",
})

_ROUTE_BY_INTENT: dict[str, str] = {
    "list_leads": "/leads/list",
    "create_lead": "/leads/list",
    "update_lead": "/leads/list",
    "delete_lead": "/leads/list",
    "create_task": "/leads/tasks",
    "list_tasks": "/leads/tasks",
    "write_email": "/email",
    "list_emails": "/email",
    "send_email": "/email",
    "search_web": "/search",
    "enrich_lead": "/search",
    "generate_lead": "/leadgen",
    "find_leads_portrait": "/leadgen",
    "cluster_company": "/leadgen",
    "analyze_lead": "/leads/list",
    "lead_history": "/leads/list",
    "add_communication": "/leads/list",
    "analytics_funnel": "/leads/analytics",
    "analytics_conversion": "/leads/analytics",
    "analytics_cycle": "/leads/analytics",
    "analytics_score": "/leads/list",
    "analytics_report": "/leads/analytics",
    "ask_rag": "/search",
    "save_to_rag": "/search",
}

_ANALYTICS_TITLES = {
    "analytics_funnel": "Воронка за период",
    "analytics_conversion": "Конверсия по источнику",
    "analytics_cycle": "Цикл сделки и средний чек",
    "analytics_score": "Лиды по скору",
    "analytics_report": "Аналитика CRM",
}


def build_voice_action(
    *,
    intent: str,
    slots: dict[str, Any] | None,
    reply: str,
    agents: list[str] | None = None,
    agent_result: dict[str, Any] | None = None,
    ui_action: str | None = None,
    module: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any] | None:
    """Формирует voice_action или None, если UI-реакция не нужна."""
    slots = dict(slots or {})
    agent_result = agent_result or {}
    agents = list(agents or [])

    ui = (ui_action or "").strip().lower() or None
    if not ui:
        ui = _infer_ui(intent, slots, agent_result)

    if not module:
        from core.hermes.module_contract import INTENT_MODULE

        module = INTENT_MODULE.get(intent)

    if not ui:
        return None

    base: dict[str, Any] = {
        "type": "voice_action",
        "intent": intent,
        "module": module,
        "ui": ui,
        "route": None,
        "title": _title(intent, ui, slots),
        "payload": {},
        "agents_used": _agents_used(agents, agent_result),
        "reply": reply or "",
        "trace_id": trace_id,
        "slots": slots,
    }

    if ui == "navigate":
        base["route"] = _route(intent, slots, agent_result)
        if intent in ANALYTICS_INTENTS:
            base["payload"] = _analytics_payload(slots)
    elif ui == "filter":
        base["route"] = "/leads/list"
        base["payload"] = {"filter": _filter_payload(intent, slots)}
    elif ui == "approve":
        base["payload"] = {
            "intent": intent,
            "slots": slots,
            "message": reply or _approve_message(intent, slots),
            "actions": ["confirm", "reject"],
        }
        if intent == "send_email":
            base["route"] = "/email"
        elif intent == "save_to_rag":
            base["route"] = "/search"
    elif ui == "modal":
        base["payload"] = _modal_payload(intent, agent_result, reply)
        lid = agent_result.get("lead_id")
        if intent == "lead_history" and lid is not None:
            base["route"] = f"/leads/{lid}"
        elif intent == "search_web" and slots.get("query"):
            base["route"] = f"/search?q={_url_q(slots['query'])}"
        elif intent == "ask_rag":
            base["route"] = "/search"

    return base


def _infer_ui(intent: str, slots: dict, agent_result: dict) -> str | None:
    if intent == "navigate" or slots.get("target"):
        return "navigate"
    if intent in ("delete_lead", "send_email", "save_to_rag"):
        return "approve"
    if intent in ("list_leads", "analytics_score"):
        return "filter"
    if intent == "lead_history" and agent_result.get("history"):
        return "modal"
    if intent == "analyze_lead":
        return "modal"
    if intent == "ask_rag":
        return "modal"
    if intent in _UI_MODAL_INTENTS and _has_modal_content(agent_result, intent):
        return "modal"
    if intent in ANALYTICS_INTENTS:
        return "navigate"
    if intent in _ROUTE_BY_INTENT:
        return "navigate"
    return None


def _route(intent: str, slots: dict, agent_result: dict) -> str:
    target = slots.get("target") or slots.get("route")
    if target:
        return str(target)
    lead_route = _lead_route(slots, agent_result)
    if lead_route:
        return lead_route
    if intent in ANALYTICS_INTENTS:
        return MODULE_ROUTES["analytics"]
    if intent in RAG_INTENTS:
        return MODULE_ROUTES["rag"]
    if intent in ("list_emails", "write_email", "send_email"):
        return MODULE_ROUTES["email"]
    return _ROUTE_BY_INTENT.get(intent, "/leads/list")


def _url_q(text: str) -> str:
    from urllib.parse import quote

    return quote(str(text)[:200])


def _analytics_payload(slots: dict) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    period = slots.get("period")
    if period:
        payload["period"] = period
    source = slots.get("source")
    if source:
        payload["source"] = source
    return payload


def _lead_route(slots: dict, agent_result: dict) -> str | None:
    for action in agent_result.get("actions_taken") or []:
        m = re.search(r"#(\d+)", str(action))
        if m:
            return f"/leads/{m.group(1)}"
    lid = slots.get("lead_id") or slots.get("id")
    if lid is not None:
        return f"/leads/{lid}"
    return None


def _filter_payload(intent: str, slots: dict) -> dict[str, str]:
    view = list_leads_view_from_slots(slots)
    if intent == "analytics_score":
        min_sc = slots.get("min_score")
        if min_sc is not None:
            view["minScore"] = str(min_sc)
            view["sortBy"] = "score_desc"
    return view


def _modal_payload(intent: str, agent_result: dict, reply: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"reply": reply, "intent": intent}
    analyst = agent_result.get("analyst_output") or {}
    economist = agent_result.get("economist_output") or {}
    marketer = agent_result.get("marketer_output") or {}
    tech = agent_result.get("tech_output") or {}
    strategist = agent_result.get("strategist_output") or {}

    if analyst:
        payload["analysis"] = analyst
    if economist:
        payload["economics"] = economist
    if tech:
        payload["tech"] = tech
    if strategist:
        payload["strategy"] = strategist

    hist = agent_result.get("history")
    if hist:
        payload["history"] = hist
        payload["lead_id"] = agent_result.get("lead_id")

    email = marketer.get("email") if isinstance(marketer.get("email"), dict) else {}
    if not email and (marketer.get("subject") or marketer.get("body")):
        email = {
            "subject": marketer.get("subject", ""),
            "body": marketer.get("body", ""),
        }
    if email:
        payload["draft_email"] = email

    rag = agent_result.get("rag_answer")
    if rag:
        payload["rag_answer"] = rag
        payload["rag_hits"] = agent_result.get("rag_hits", 0)

    actions = ["save", "reject"]
    if email.get("subject") or email.get("body"):
        actions = ["send", "save", "reject"]
    payload["actions"] = actions
    return payload


def _has_modal_content(agent_result: dict, intent: str = "") -> bool:
    if intent == "ask_rag" and (agent_result.get("rag_answer") or agent_result.get("final_reply")):
        return True
    for key in (
        "analyst_output", "economist_output", "marketer_output",
        "tech_output", "strategist_output",
    ):
        if agent_result.get(key):
            return True
    return bool(agent_result.get("final_reply"))


def _agents_used(agents: list[str], agent_result: dict) -> list[str]:
    seen: list[str] = []
    for aid in agents:
        if aid not in seen:
            seen.append(aid)
    for key, aid in (
        ("analyst_output", "analyst"),
        ("economist_output", "economist"),
        ("marketer_output", "marketer"),
        ("tech_output", "tech_specialist"),
        ("strategist_output", "strategist"),
    ):
        if agent_result.get(key) and aid not in seen:
            seen.append(aid)
    return seen


def _title(intent: str, ui: str, slots: dict) -> str:
    company = slots.get("company") or slots.get("query") or ""
    if intent in _ANALYTICS_TITLES:
        return _ANALYTICS_TITLES[intent]
    if ui == "approve" and intent == "delete_lead":
        return f"Удалить лид{': ' + company if company else ''}?"
    if ui == "approve" and intent == "send_email":
        return "Отправить письмо?"
    if ui == "approve" and intent == "save_to_rag":
        return "Сохранить в базу знаний?"
    if ui == "modal" and intent == "write_email":
        return "Черновик письма"
    if ui == "modal" and intent == "ask_rag":
        return "База знаний"
    if ui == "modal" and intent == "lead_history":
        return f"История лида{': ' + company if company else ''}"
    if ui == "modal" and intent == "analyze_lead":
        return f"Анализ лида{': ' + company if company else ''}"
    if ui == "modal":
        return "Ответ агентов"
    if ui == "filter":
        return "Фильтр списка лидов"
    if ui == "navigate":
        return "Переход"
    return intent


def _approve_message(intent: str, slots: dict) -> str:
    if intent == "delete_lead":
        company = slots.get("company") or slots.get("lead_id") or "лид"
        return f"Подтверди удаление: {company}"
    if intent == "send_email":
        return "Подтверди отправку письма получателю"
    if intent == "save_to_rag":
        q = slots.get("question") or slots.get("query") or "материал"
        return f"Сохранить в RAG: {q[:120]}"
    return "Подтвердите действие"
