"""Сборка пакета voice_action для WebSocket → SvelteKit (ARCHITECTURE.md)."""
from __future__ import annotations

import re
from typing import Any

from core.hermes.lead_list_view import list_leads_view_from_slots

_UI_MODAL_INTENTS = frozenset({
    "write_email", "run_analysis", "ask_economist", "ask_marketer",
    "ask_tech", "ask_strategist", "analyze_lead", "search_web",
})

_ROUTE_BY_INTENT: dict[str, str] = {
    "list_leads": "/leads/list",
    "create_lead": "/leads/list",
    "update_lead": "/leads/list",
    "delete_lead": "/leads/list",
    "create_task": "/leads/tasks",
    "list_tasks": "/leads/tasks",
    "write_email": "/email",
    "search_web": "/search",
    "generate_lead": "/leadgen",
    "find_leads_portrait": "/leadgen",
    "cluster_company": "/leadgen",
    "analyze_lead": "/leads/list",
    "lead_history": "/leads/list",
    "add_communication": "/leads/list",
}


def build_voice_action(
    *,
    intent: str,
    slots: dict[str, Any] | None,
    reply: str,
    agents: list[str] | None = None,
    agent_result: dict[str, Any] | None = None,
    ui_action: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any] | None:
    """Формирует voice_action или None, если UI-реакция не нужна."""
    slots = dict(slots or {})
    agent_result = agent_result or {}
    agents = list(agents or [])

    ui = (ui_action or "").strip().lower() or None
    if not ui:
        ui = _infer_ui(intent, slots, agent_result)

    if not ui:
        return None

    base: dict[str, Any] = {
        "type": "voice_action",
        "intent": intent,
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
    elif ui == "filter":
        base["route"] = "/leads/list"
        base["payload"] = {"filter": _filter_payload(slots)}
    elif ui == "approve":
        base["payload"] = {
            "intent": intent,
            "slots": slots,
            "message": reply or _approve_message(intent, slots),
            "actions": ["confirm", "reject"],
        }
    elif ui == "modal":
        base["payload"] = _modal_payload(intent, agent_result, reply)
        lid = agent_result.get("lead_id")
        if intent == "lead_history" and lid is not None:
            base["route"] = f"/leads/{lid}"

    return base


def _infer_ui(intent: str, slots: dict, agent_result: dict) -> str | None:
    if intent == "navigate" or slots.get("target"):
        return "navigate"
    if intent == "delete_lead":
        return "approve"
    if intent == "list_leads":
        return "filter"
    if intent == "lead_history" and agent_result.get("history"):
        return "modal"
    if intent == "analyze_lead":
        return "modal"
    if intent in _UI_MODAL_INTENTS and _has_modal_content(agent_result):
        return "modal"
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
    return _ROUTE_BY_INTENT.get(intent, "/leads/list")


def _lead_route(slots: dict, agent_result: dict) -> str | None:
    for action in agent_result.get("actions_taken") or []:
        m = re.search(r"#(\d+)", str(action))
        if m:
            return f"/leads/{m.group(1)}"
    lid = slots.get("lead_id") or slots.get("id")
    if lid is not None:
        return f"/leads/{lid}"
    return None


def _filter_payload(slots: dict) -> dict[str, str]:
    return list_leads_view_from_slots(slots)


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

    actions = ["save", "reject"]
    if email.get("subject") or email.get("body"):
        actions = ["send", "save", "reject"]
    payload["actions"] = actions
    return payload


def _has_modal_content(agent_result: dict) -> bool:
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
    if ui == "approve" and intent == "delete_lead":
        return f"Удалить лид{': ' + company if company else ''}?"
    if ui == "modal" and intent == "write_email":
        return "Черновик письма"
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
    return "Подтвердите действие"
