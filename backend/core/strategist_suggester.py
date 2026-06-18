"""Авто-суфлёр Стратега: слабые ответы агентов → предложения правок промптов."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from sqlalchemy import select

from core import traces
from core.agent_eval.gate_artifacts import load_latest_gate

logger = logging.getLogger(__name__)

AGENT_IDS = ("analyst", "strategist", "economist", "marketer", "tech_specialist")


def collect_hermes_bad_traces(max_items: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in traces.get_traces(limit=300):
        if t.get("feedback") != "bad" and not t.get("error"):
            continue
        text = (t.get("text") or "").strip()
        if not text:
            continue
        out.append({
            "source": "hermes_trace",
            "text": text[:200],
            "intent": t.get("intent"),
            "error": (t.get("error") or "")[:120],
        })
        if len(out) >= max_items:
            break
    return out


def collect_gate_failures(max_items: int = 12) -> list[dict[str, Any]]:
    _, report = load_latest_gate()
    if not report:
        return []
    out: list[dict[str, Any]] = []
    for agent, block in (report.get("agents") or {}).items():
        if agent not in AGENT_IDS and agent != "hermes":
            continue
        for row in block.get("results") or []:
            if row.get("passed"):
                continue
            out.append({
                "source": "gate_fail",
                "agent": agent,
                "case_id": row.get("id"),
                "reason": (row.get("reason") or row.get("error") or "")[:200],
            })
            if len(out) >= max_items:
                return out
    return out


async def collect_bad_agent_runs(max_items: int = 12) -> list[dict[str, Any]]:
    from db.models.agent_run_log import AgentRunLog
    from db.session import SessionLocal

    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(AgentRunLog)
                .where(AgentRunLog.feedback == "bad")
                .order_by(AgentRunLog.created_at.desc())
                .limit(max_items)
            )
        ).scalars().all()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = r.to_dict()
        out.append({
            "source": "agent_run",
            "agent": d.get("agentName"),
            "task": (d.get("task") or "")[:160],
            "note": (d.get("feedbackNote") or "")[:200],
            "summary": (d.get("summary") or "")[:200],
        })
    return out


async def gather_weak_signals(
    *,
    max_traces: int = 8,
    max_runs: int = 12,
    max_gate: int = 12,
) -> dict[str, Any]:
    hermes = collect_hermes_bad_traces(max_traces)
    gate = collect_gate_failures(max_gate)
    runs = await collect_bad_agent_runs(max_runs)
    return {
        "hermes_bad_traces": hermes,
        "gate_failures": gate,
        "agent_bad_runs": runs,
        "total": len(hermes) + len(gate) + len(runs),
    }


def _format_signals_for_llm(signals: dict[str, Any]) -> str:
    parts: list[str] = []
    for t in signals.get("hermes_bad_traces") or []:
        parts.append(f'[Hermes 👎] "{t.get("text")}" → {t.get("intent")} err={t.get("error") or "-"}')
    for g in signals.get("gate_failures") or []:
        parts.append(f'[Gate fail {g.get("agent")}] case={g.get("case_id")} {g.get("reason")}')
    for r in signals.get("agent_bad_runs") or []:
        parts.append(
            f'[Agent 👎 {r.get("agent")}] task={r.get("task")} note={r.get("note")} summary={r.get("summary")}'
        )
    return "\n".join(parts) if parts else "(нет сигналов)"


async def suggest_prompt_fixes(
    signals: dict[str, Any],
    *,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    """Стратег (Groq) анализирует слабые ответы и предлагает правки промптов."""
    if signals.get("total", 0) == 0:
        return {
            "ok": True,
            "has_suggestions": False,
            "message": "Нет слабых сигналов: 👎 на трейсах/агентах или провалы gate.",
            "signals": signals,
            "suggestions": [],
        }

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return {
            "ok": False,
            "error": "no_groq_key",
            "message": "GROQ_API_KEY не задан — суфлёр недоступен.",
            "signals": signals,
            "suggestions": [],
        }

    from groq import AsyncGroq

    from agents.strategist import STRATEGIST_SYSTEM_PROMPT

    weak_block = _format_signals_for_llm(signals)
    user_msg = f"""Ты — Стратег SmartCRM. Проанализируй слабые ответы системы и предложи точечные правки промптов агентов.

СИГНАЛЫ ({signals.get("total")} шт.):
{weak_block}

Агенты: analyst, economist, marketer, tech_specialist, strategist, hermes (голосовой роутер).

Верни JSON:
{{
  "summary": "краткий вывод по-русски (2-3 предложения)",
  "suggestions": [
    {{
      "agent_id": "marketer",
      "pattern": "что повторяется в ошибках",
      "explanation": "что добавить в промпт и зачем",
      "prompt_append": "текст для вставки в конец промпта (русский, конкретный)",
      "priority": "high|medium|low"
    }}
  ]
}}

Не больше {max_suggestions} предложений. Только агенты с реальными сигналами. prompt_append — 2-6 предложений."""

    client = AsyncGroq(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": STRATEGIST_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
    finally:
        try:
            await client.close()
        except Exception:
            pass

    raw = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"summary": raw, "suggestions": []}

    suggestions = []
    for s in parsed.get("suggestions") or []:
        aid = (s.get("agent_id") or "").strip()
        append = (s.get("prompt_append") or "").strip()
        if not aid or len(append) < 20:
            continue
        if aid not in AGENT_IDS and aid != "hermes":
            continue
        suggestions.append({
            "agent_id": aid,
            "pattern": s.get("pattern", ""),
            "explanation": s.get("explanation", ""),
            "prompt_append": append,
            "priority": s.get("priority", "medium"),
        })
        if len(suggestions) >= max_suggestions:
            break

    return {
        "ok": True,
        "has_suggestions": bool(suggestions),
        "summary": parsed.get("summary", ""),
        "signals": signals,
        "suggestions": suggestions,
    }
