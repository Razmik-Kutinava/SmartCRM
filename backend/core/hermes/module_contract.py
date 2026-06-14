"""Контракт Hermes Ф2: module + intent + ui_action (PRD Voice Layer)."""
from __future__ import annotations

from typing import Any

MODULES = frozenset({
    "leads", "tasks", "email", "search", "analytics", "agents", "rag", "leadgen", "tenders",
})

UI_ACTIONS = frozenset({"navigate", "modal", "filter", "approve"})

INTENT_MODULE: dict[str, str] = {
    "create_lead": "leads",
    "update_lead": "leads",
    "delete_lead": "leads",
    "list_leads": "leads",
    "analyze_lead": "leads",
    "analyze_and_email": "agents",
    "evaluate_tender": "tenders",
    "weekly_report": "analytics",
    "lead_history": "leads",
    "add_communication": "leads",
    "create_task": "tasks",
    "list_tasks": "tasks",
    "update_task": "tasks",
    "delete_task": "tasks",
    "write_email": "email",
    "list_emails": "email",
    "send_email": "email",
    "search_web": "search",
    "enrich_lead": "search",
    "analytics_funnel": "analytics",
    "analytics_conversion": "analytics",
    "analytics_cycle": "analytics",
    "analytics_score": "analytics",
    "analytics_report": "analytics",
    "run_analysis": "agents",
    "ask_economist": "agents",
    "ask_marketer": "agents",
    "ask_tech": "agents",
    "ask_strategist": "agents",
    "ask_rag": "rag",
    "save_to_rag": "rag",
    "generate_lead": "leadgen",
    "find_leads_portrait": "leadgen",
    "cluster_company": "leadgen",
    "navigate": "leads",
    "noop": "leads",
}

INTENT_UI: dict[str, str] = {
    "delete_lead": "approve",
    "send_email": "approve",
    "save_to_rag": "approve",
    "list_leads": "filter",
    "list_tasks": "navigate",
    "write_email": "modal",
    "list_emails": "navigate",
    "search_web": "navigate",
    "enrich_lead": "navigate",
    "analytics_funnel": "navigate",
    "analytics_conversion": "navigate",
    "analytics_cycle": "navigate",
    "analytics_score": "filter",
    "analytics_report": "navigate",
    "run_analysis": "modal",
    "ask_economist": "modal",
    "ask_marketer": "modal",
    "ask_tech": "modal",
    "ask_strategist": "modal",
    "ask_rag": "modal",
    "analyze_lead": "modal",
    "analyze_and_email": "modal",
    "evaluate_tender": "modal",
    "weekly_report": "modal",
    "lead_history": "modal",
    "create_lead": "navigate",
    "update_lead": "navigate",
    "create_task": "navigate",
    "generate_lead": "navigate",
    "find_leads_portrait": "navigate",
    "cluster_company": "navigate",
    "navigate": "navigate",
}

MODULE_ROUTES: dict[str, str] = {
    "email": "/email",
    "search": "/search",
    "analytics": "/leads/analytics",
    "leadgen": "/leadgen",
    "tasks": "/leads/tasks",
    "rag": "/search",
    "tenders": "/tenders",
}

ANALYTICS_INTENTS = frozenset({
    "analytics_funnel", "analytics_conversion", "analytics_cycle",
    "analytics_score", "analytics_report",
})

RAG_INTENTS = frozenset({"ask_rag", "save_to_rag"})


def default_ui_for_intent(intent: str, slots: dict[str, Any] | None = None) -> str | None:
    slots = slots or {}
    if intent == "navigate" or slots.get("target"):
        return "navigate"
    return INTENT_UI.get(intent)


def enrich_module_ui(parsed: dict[str, Any]) -> dict[str, Any]:
    """Дополняет module/ui_action по intent; нормализует значения."""
    if not parsed:
        return parsed
    out = dict(parsed)
    intent = str(out.get("intent") or "noop").strip()
    slots = dict(out.get("slots") or {})

    module = str(out.get("module") or "").strip().lower()
    if module not in MODULES:
        module = INTENT_MODULE.get(intent, "leads")
    out["module"] = module

    ui = str(out.get("ui_action") or "").strip().lower()
    if ui not in UI_ACTIONS:
        ui = default_ui_for_intent(intent, slots) or ""
    out["ui_action"] = ui or None
    out["slots"] = slots
    return out
