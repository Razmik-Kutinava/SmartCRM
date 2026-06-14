"""Supervisor — выборочный fanout агентов (Ф2 §2)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from agents.scenarios.analysis_email import AGENTS as ANALYSIS_EMAIL_AGENTS
from agents.scenarios.analysis_email import INTENT as ANALYSIS_EMAIL_INTENT
from agents.scenarios.tender_evaluation import AGENTS as TENDER_EVAL_AGENTS
from agents.scenarios.tender_evaluation import INTENT as TENDER_EVAL_INTENT
from agents.scenarios.weekly_report import AGENTS as WEEKLY_REPORT_AGENTS
from agents.scenarios.weekly_report import INTENT as WEEKLY_REPORT_INTENT
from agents.scenarios.similar_clients import AGENTS as SIMILAR_CLIENTS_AGENTS
from agents.scenarios.similar_clients import INTENT as SIMILAR_CLIENTS_INTENT

logger = logging.getLogger(__name__)

MIN_PARALLEL_AGENTS = 2

VALID_AGENTS = frozenset({
    "analyst", "economist", "marketer", "tech_specialist", "strategist",
})

PARALLEL_AGENTS = frozenset({"analyst", "economist", "marketer", "tech_specialist"})

AGENT_INTENTS = frozenset({
    "create_lead", "update_lead", "delete_lead", "list_leads", "analyze_lead",
    "run_analysis", "ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
    "search_web", "write_email",
    ANALYSIS_EMAIL_INTENT,
    TENDER_EVAL_INTENT,
    WEEKLY_REPORT_INTENT,
    SIMILAR_CLIENTS_INTENT,
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
    ANALYSIS_EMAIL_INTENT: list(ANALYSIS_EMAIL_AGENTS),
    TENDER_EVAL_INTENT: list(TENDER_EVAL_AGENTS),
    WEEKLY_REPORT_INTENT: list(WEEKLY_REPORT_AGENTS),
    SIMILAR_CLIENTS_INTENT: list(SIMILAR_CLIENTS_AGENTS),
    "delete_lead": ["analyst"],
    "list_leads": ["analyst"],
}

VOICE_SINGLE = frozenset({
    "ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
})
LEADGEN = frozenset({"generate_lead", "find_leads_portrait", "cluster_company"})
CRM_PARALLEL = frozenset({
    "create_lead", "update_lead", "analyze_lead", "delete_lead", "run_analysis",
    ANALYSIS_EMAIL_INTENT,
    TENDER_EVAL_INTENT,
    WEEKLY_REPORT_INTENT,
    SIMILAR_CLIENTS_INTENT,
})


@dataclass(frozen=True)
class FanoutPlan:
    route: str
    parallel_agents: tuple[str, ...]
    run_strategist: bool
    source: str
    parallel_fanout: bool = False


def is_parallel_fanout(agent_ids: list[str] | tuple[str, ...]) -> bool:
    return len(agent_ids) >= 2


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
    hermes_parallel: bool = False,
) -> FanoutPlan:
    """Выбор подмножества агентов: Hermes agents[] → иначе дефолт по intent."""
    slots = slots or {}
    picked = normalize_agent_ids(hermes_agents)
    defaults = normalize_agent_ids(INTENT_DEFAULTS.get(intent, ["analyst"]))
    source = "hermes" if picked else "default"
    agents = picked or defaults

    def _plan(route: str, ids: list[str], strategist: bool) -> FanoutPlan:
        tup = tuple(ids)
        pf = is_parallel_fanout(tup)
        if hermes_parallel and len(tup) < MIN_PARALLEL_AGENTS:
            logger.warning(
                "Hermes parallel=true но агентов %s для intent=%s",
                len(tup), intent,
            )
        return FanoutPlan(route, tup, strategist, source, parallel_fanout=pf)

    if intent in LEADGEN:
        ids = agents or ["analyst"]
        return _plan("leadgen", list(ids), False)

    if intent in VOICE_SINGLE:
        one = agents[:1] or ["analyst"]
        return _plan("voice_single", list(one), False)

    if intent == "ask_strategist":
        return _plan("voice_single", ["strategist"], False)

    if intent == "search_web":
        return _plan("search", ["analyst"], False)

    if intent == "write_email":
        return _plan("email", ["marketer"], False)

    if intent == "list_leads":
        return _plan("parallel", ["analyst"], False)

    if intent in CRM_PARALLEL:
        if intent == "delete_lead" and not picked:
            agents = ["analyst"]
        return _plan("parallel", list(agents), True)

    return FanoutPlan("skip", (), False, source, False)
