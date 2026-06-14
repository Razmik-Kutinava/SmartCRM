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


def dialogue_llm_enabled() -> bool:
    return os.getenv("RAG_DIALOGUE_LLM", "0").strip().lower() in ("1", "true", "yes")


def _merge_facts(primary: list[str], extra: list[str]) -> list[str]:
    seen = {f[:80].lower() for f in primary}
    out = list(primary)
    for line in extra:
        key = line[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out


async def extract_deal_facts_llm(
    output: dict[str, Any],
    *,
    transcript: str = "",
) -> list[str]:
    """LLM-извлечение фактов (RAG_DIALOGUE_LLM=1)."""
    import json
    import re

    from core.llm import chat

    blob = json.dumps(output, ensure_ascii=False)[:3500]
    tr = (transcript or "").strip()[:500]
    raw = await chat(
        [{
            "role": "user",
            "content": (
                "Из JSON-ответа агента CRM извлеки 2–6 конкретных фактов о сделке/лиде.\n"
                f"Диалог: {tr or '—'}\n"
                f"Ответ агента: {blob}\n\n"
                "Верни строго JSON-массив строк. Только проверяемые факты, без выдумок."
            ),
        }],
        temperature=0.1,
        max_tokens=400,
        json_mode=False,
    )
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        return []
    parsed = json.loads(match.group(0))
    facts: list[str] = []
    for item in parsed:
        s = str(item).strip()
        if len(s) >= 12 and not any(p in s.lower() for p in _SKIP):
            facts.append(s[:800])
    return facts


async def collect_deal_facts(
    output: dict[str, Any] | None,
    *,
    transcript: str = "",
) -> list[str]:
    facts = extract_deal_facts(output)
    if dialogue_llm_enabled() and output and isinstance(output, dict):
        try:
            llm_facts = await extract_deal_facts_llm(output, transcript=transcript)
            facts = _merge_facts(facts, llm_facts)
        except Exception as e:
            logger.warning("RAG_DIALOGUE_LLM fallback: %s", e)
    return facts


async def ingest_dialogue_facts(
    agent_id: str,
    output: dict[str, Any] | None,
    *,
    transcript: str = "",
    slots: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    slots = slots or {}
    facts = await collect_deal_facts(output, transcript=transcript)
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


async def ingest_orchestrator_dialogues(
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
                await ingest_dialogue_facts(
                    agent_id,
                    payload,
                    transcript=transcript,
                    slots=slots,
                    dry_run=dry_run,
                )
            )
    return out
