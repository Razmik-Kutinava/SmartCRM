"""Факты из диалога агента → RAG (коллекция того же агента)."""

from __future__ import annotations

import logging
import os
from typing import Any

from rag.ingest import ingest_manual_text, normalize_for_agent

logger = logging.getLogger(__name__)

AGENT_OUTPUT_KEYS: dict[str, str] = {
    "analyst": "analyst_output",
    "strategist": "strategist_output",
    "economist": "economist_output",
    "marketer": "marketer_output",
    "tech_specialist": "tech_output",
}

_SKIP = ("не указан", "нет данных", "ошибка агента")


def _company(slots: dict[str, Any]) -> str:
    return str(slots.get("company") or slots.get("query") or "").strip()


def extract_deal_facts(output: dict[str, Any] | None) -> list[str]:
    """Эвристика фактов о сделке (без live LLM в CI)."""
    if not output or not isinstance(output, dict):
        return []
    facts: list[str] = []
    seen: set[str] = set()

    def add(label: str, val: Any) -> None:
        if val is None:
            return
        s = str(val).strip()
        if len(s) < 12 or any(p in s.lower() for p in _SKIP):
            return
        line = f"{label}: {s}" if label else s
        key = line[:80].lower()
        if key in seen:
            return
        seen.add(key)
        facts.append(line[:800])

    for key in ("summary", "final_reply", "decision", "next_action", "rationale", "coach_tip"):
        add(key, output.get(key))
    if output.get("score") is not None:
        add("score", f"{output['score']}/100")
    bant = output.get("bant")
    if isinstance(bant, dict):
        for k, v in bant.items():
            add(f"BANT_{k}", v)
    for k in ("budget_estimate", "deal_segment", "deal_probability_pct"):
        add(k, output.get(k))
    stack = output.get("likely_stack")
    if isinstance(stack, list) and stack:
        add("likely_stack", ", ".join(str(x) for x in stack[:8]))
    for q in (output.get("presale_questions") or [])[:5]:
        add("presale_question", q)
    fe = output.get("first_email")
    if isinstance(fe, dict):
        subj = str(fe.get("subject") or "").strip()
        body = str(fe.get("body") or "").strip()[:400]
        if subj or body:
            add("email_draft", f"{subj} — {body}".strip(" —"))
    return facts


def dialogue_to_rag_text(
    transcript: str,
    facts: list[str],
    *,
    company: str = "",
    agent_id: str = "all",
) -> str:
    q = (transcript or "").strip() or (f"Анализ лида {company}" if company else "Диалог с агентом")
    parts = [f"Вопрос: {q}"]
    if company:
        parts.append(f"Компания: {company}")
    parts.append(f"Источник: dialogue/{agent_id}")
    for i, f in enumerate(facts, 1):
        parts.append(f"Ответ ({i}): {f}")
    return "\n\n".join(parts)


def min_facts_required() -> int:
    try:
        return max(1, int(os.getenv("RAG_DIALOGUE_MIN_FACTS", "2")))
    except ValueError:
        return 2


def is_dialogue_eligible(facts: list[str]) -> bool:
    return len(facts) >= min_facts_required()


def dialogue_auto_enabled() -> bool:
    return os.getenv("RAG_DIALOGUE_AUTO_INGEST", "1").strip().lower() in ("1", "true", "yes")


def ingest_dialogue_facts(
    agent_id: str,
    output: dict[str, Any] | None,
    *,
    transcript: str = "",
    slots: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    slots = slots or {}
    facts = extract_deal_facts(output)
    company = _company(slots)
    agent = normalize_for_agent(agent_id)
    if not is_dialogue_eligible(facts):
        return {
            "ok": True,
            "eligible": False,
            "facts_count": len(facts),
            "facts": facts,
            "ingested": 0,
            "chunks": 0,
            "for_agent": agent,
            "dry_run": dry_run,
        }
    text = dialogue_to_rag_text(transcript, facts, company=company, agent_id=agent)
    title = f"dialogue-{agent}-{company or 'lead'}"[:200]
    extra: dict[str, str] = {"source_type": "agent_dialogue", "agent_id": agent, "auto_ingest": "1"}
    if company:
        extra["company"] = company[:200]
    lid = slots.get("lead_id") if slots.get("lead_id") is not None else slots.get("id")
    if lid is not None:
        extra["lead_id"] = str(lid)
    out = ingest_manual_text(
        text,
        title=title,
        tags="dialogue",
        for_agent=agent,
        dry_run=dry_run,
        extra_metadata=extra,
    )
    err = out.get("error")
    return {
        "ok": not err,
        "eligible": True,
        "facts_count": len(facts),
        "facts": facts,
        "ingested": 0 if dry_run or err else 1,
        "chunks": int(out.get("chunks") or 0),
        "for_agent": agent,
        "dry_run": dry_run,
        "error": err,
        "preview": (out.get("chunk_previews") or [])[:3],
    }


def ingest_orchestrator_dialogues(
    agent_result: dict[str, Any],
    *,
    transcript: str = "",
    slots: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    slots = slots or {}
    out: list[dict[str, Any]] = []
    for agent_id, key in AGENT_OUTPUT_KEYS.items():
        payload = agent_result.get(key)
        if payload:
            out.append(
                ingest_dialogue_facts(
                    agent_id,
                    payload,
                    transcript=transcript,
                    slots=slots,
                    dry_run=dry_run,
                )
            )
    return out
