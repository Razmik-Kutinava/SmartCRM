"""Supervisor — выборочный fanout агентов (Ф2 §2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_AGENTS = frozenset({
    "analyst", "economist", "marketer", "tech_specialist", "strategist",
})

PARALLEL_AGENTS = frozenset({"analyst", "economist", "marketer", "tech_specialist"})

AGENT_INTENTS = frozenset({
    "create_lead", "update_lead", "delete_lead", "list_leads", "analyze_lead",
    "run_analysis", "ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
    "search_web", "write_email",
    "generate_lead", "find_leads_portrait", "cluster_company",
})

INTENT_DEFAULTS: dict[str, list[str]] = {
    "ask_economist": ["economist"],
    "ask_marketer": ["marketer"],
    "ask_tech": ["tech_specialist"],
    "ask_strategist": ["strategist"],
    "search_web": ["analyst"],
    "write_email": ["marketer"],
    "run_analysis": ["analyst", "economist", "marketer", "tech_specialist"],
    "generate_lead": ["analyst", "tech_specialist", "marketer", "strategist"],
    "find_leads_portrait": ["analyst"],
    "cluster_company": ["analyst"],
    "create_lead": ["analyst", "economist", "marketer", "tech_specialist"],
    "update_lead": ["analyst", "economist", "marketer", "tech_specialist"],
    "analyze_lead": ["analyst", "economist", "marketer", "tech_specialist"],
    "delete_lead": ["analyst"],
    "list_leads": ["analyst"],
}

VOICE_SINGLE = frozenset({
    "ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
})
LEADGEN = frozenset({"generate_lead", "find_leads_portrait", "cluster_company"})
CRM_PARALLEL = frozenset({
    "create_lead", "update_lead", "analyze_lead", "delete_lead", "run_analysis",
})


@dataclass(frozen=True)
class FanoutPlan:
    route: str
    parallel_agents: tuple[str, ...]
    run_strategist: bool
    source: str


def normalize_agent_ids(raw: list[str] | None) -> list[str]:
    out: list[str] = []
    for a in raw or []:
        aid = str(a).strip().lower()
        if aid == "tech":
            aid = "tech_specialist"
        if aid in PARALLEL_AGENTS and aid not in out:
            out.append(aid)
    return out


def select_fanout_plan(
    intent: str,
    slots: dict[str, Any] | None = None,
    hermes_agents: list[str] | None = None,
) -> FanoutPlan:
    """Выбор подмножества агентов: Hermes agents[] → иначе дефолт по intent."""
    slots = slots or {}
    picked = normalize_agent_ids(hermes_agents)
    defaults = normalize_agent_ids(INTENT_DEFAULTS.get(intent, ["analyst"]))
    source = "hermes" if picked else "default"
    agents = picked or defaults

    if intent in LEADGEN:
        return FanoutPlan("leadgen", tuple(agents or ["analyst"]), False, source)

    if intent in VOICE_SINGLE:
        one = agents[:1] or ["analyst"]
        return FanoutPlan("voice_single", tuple(one), False, source)

    if intent == "ask_strategist":
        return FanoutPlan("voice_single", ("strategist",), False, source)

    if intent == "search_web":
        return FanoutPlan("search", ("analyst",), False, source)

    if intent == "write_email":
        return FanoutPlan("email", ("marketer",), False, source)

    if intent == "list_leads":
        return FanoutPlan("parallel", ("analyst",), False, source)

    if intent in CRM_PARALLEL:
        if intent == "delete_lead" and not picked:
            agents = ["analyst"]
        return FanoutPlan("parallel", tuple(agents), run_strategist=True, source=source)

    return FanoutPlan("skip", (), False, source)
