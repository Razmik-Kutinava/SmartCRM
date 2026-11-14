"""
LangGraph оркестратор — supervisor выбирает fanout, граф запускает агентов.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from agents.base import AgentState, make_initial_state
from agents.graph import run_fanout_graph
from agents.supervisor import (
    AGENT_INTENTS as _AGENT_INTENTS,
    INTENT_DEFAULTS as _INTENT_TO_AGENTS,
    select_fanout_plan,
)

logger = logging.getLogger(__name__)

# Обратная совместимость тестов
_AGENT_INTENTS = _AGENT_INTENTS
_INTENT_TO_AGENTS = _INTENT_TO_AGENTS


async def run_agents(
    intent: str,
    slots: dict[str, Any],
    transcript: str = "",
    trace_id: str = "",
    hermes_agents: list[str] | None = None,
    hermes_parallel: bool = False,
) -> dict[str, Any]:
    """
    Главная точка входа оркестратора.
    hermes_agents — список от Hermes; supervisor выбирает подмножество для fanout.
    """
    if intent not in _AGENT_INTENTS:
        return _empty_result(slots)

    from rag.retrieve import attach_rag_to_slots

    plan = select_fanout_plan(intent, slots, hermes_agents, hermes_parallel=hermes_parallel)
    slots_enriched = await attach_rag_to_slots({**slots}, transcript)
    state = make_initial_state(intent, slots_enriched, transcript, trace_id)
    state["slots"] = {
        **slots_enriched,
        "_base_reply": slots.get("reply", ""),
        "_hermes_parallel": hermes_parallel,
    }
    state["hermes_agents"] = list(hermes_agents or [])

    t_total = time.monotonic()
    logger.info(
        "Оркестратор: intent=%s plan=%s agents=%s",
        intent, plan.route, plan.parallel_agents,
    )

    if plan.route == "leadgen":
        if plan.parallel_fanout:
            from agents.fanout_parallel import run_parallel_fanout

            state = await run_parallel_fanout(state, list(plan.parallel_agents))
        state = await _run_leadgen(state, intent)
        if plan.parallel_fanout:
            state["fanout_parallel"] = True
            state["fanout_agent_count"] = len(plan.parallel_agents)
            state["agents_selected"] = list(plan.parallel_agents)
    elif plan.route == "search":
        state = await _run_search_web(state, slots.get("query") or transcript)
    elif plan.route == "email":
        state = await _run_write_email(state)
    elif plan.route == "voice_single":
        state = await _run_voice_single(state, plan.parallel_agents[0])
    elif plan.route == "parallel":
        state = await run_fanout_graph(state)
    else:
        return _empty_result(slots)

    total_ms = round((time.monotonic() - t_total) * 1000)
    return _result_from_state(state, slots, total_ms)


def _empty_result(slots: dict[str, Any]) -> dict[str, Any]:
    return {
        "agents_ran": False,
        "final_reply": slots.get("reply", ""),
        "recommendation": "",
        "analyst_output": None,
        "strategist_output": None,
        "timings_ms": {},
    }


def _result_from_state(state: AgentState, slots: dict[str, Any], total_ms: int) -> dict[str, Any]:
    plan = state.get("fanout_plan") or {}
    analyst_summary = (state.get("analyst_output") or {}).get("summary", "") or ""
    return {
        "agents_ran": True,
        "final_reply": state.get("final_reply") or analyst_summary or slots.get("reply", ""),
        "recommendation": state.get("recommendation", ""),
        "analyst_output": state.get("analyst_output"),
        "strategist_output": state.get("strategist_output"),
        "economist_output": state.get("economist_output"),
        "marketer_output": state.get("marketer_output"),
        "tech_output": state.get("tech_output"),
        "agents_selected": state.get("agents_selected") or plan.get("parallel_agents") or [],
        "fanout_source": plan.get("source", ""),
        "fanout_parallel": bool(state.get("fanout_parallel") or plan.get("parallel_fanout")),
        "fanout_agent_count": state.get("fanout_agent_count")
        or len(state.get("agents_selected") or plan.get("parallel_agents") or []),
        "fanout_elapsed_ms": state.get("fanout_elapsed_ms"),
        "timings_ms": {**state.get("agent_timings", {}), "total": total_ms},
        "errors": state.get("errors", []),
        "actions_taken": state.get("actions_taken", []),
    }


async def _run_voice_single(state: AgentState, agent_id: str) -> AgentState:
    """Один агент по голосу (ask_*), без fanout."""
    slots = state.get("slots", {})
    question = slots.get("question") or slots.get("query") or state.get("transcript", "")
    company = slots.get("company", "")
    context = slots.get("context", "")
    t0 = time.monotonic()

    search_context = ""
    if question or company:
        try:
            from rag.search import free_search
            search_q = f"{company} {question}".strip() if company else question
            search_result = await free_search(search_q, summarize=False, max_results=8)
            search_context = search_result.get("formatted_block", "")
        except Exception as e:
            logger.warning("voice_single поиск ошибка: %s", e)

    prompt_ctx = f"Вопрос: {question}"
    if company:
        prompt_ctx += f"\nКомпания: {company}"
    if slots.get("period"):
        prompt_ctx += f"\nПериод: {slots['period']}"
    if slots.get("industry"):
        prompt_ctx += f"\nОтрасль: {slots['industry']}"
    if context:
        prompt_ctx += f"\nДополнительный контекст: {context}"
    if search_context:
        prompt_ctx += f"\n\nДанные из интернета:\n{search_context}"

    state["slots"] = {**slots, "voice_query": prompt_ctx, "_search_context": search_context}
    prompts = {
        "economist": "Ты — финансовый аналитик. Дай чёткий ответ с цифрами.",
        "marketer": "Ты — старший маркетолог B2B. Дай конкретный ответ.",
        "tech_specialist": "Ты — технический директор. Дай технический ответ.",
        "strategist": "Ты — бизнес-стратег B2B. Дай план действий.",
        "analyst": "Ты — CRM-аналитик. Дай структурированный ответ.",
    }
    try:
        from core.llm import chat
        answer = await chat(
            [
                {"role": "system", "content": prompts.get(agent_id, "Ты — эксперт.")},
                {"role": "user", "content": prompt_ctx},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        elapsed_ms = round((time.monotonic() - t0) * 1000)
        state["final_reply"] = answer
        state["agent_timings"] = {**state.get("agent_timings", {}), agent_id: elapsed_ms}
        key = "tech_output" if agent_id == "tech_specialist" else f"{agent_id}_output"
        state[key] = {"summary": answer, "search_context": search_context}
        state["agents_selected"] = [agent_id]
    except Exception as e:
        logger.error("voice_single %s: %s", agent_id, e)
        state["errors"] = list(state.get("errors", [])) + [str(e)]
        state["final_reply"] = f"Агент {agent_id} не смог ответить: {e}"
    return state


async def _run_leadgen(state: AgentState, intent: str) -> AgentState:
    """Голосовая/текстовая лидогенерация через pipeline."""
    slots = state.get("slots", {})
    try:
        if intent == "generate_lead":
            from leadgen.pipeline import run_pipeline
            result = await run_pipeline(
                inn=slots.get("inn", ""),
                company_name=slots.get("company_name", "") or slots.get("company", ""),
                website=slots.get("website", ""),
                save_to_crm=slots.get("save", False),
            )
            score = result.get("final_score", 0)
            company = result.get("company_name", "компания")
            lpr = (result.get("lpr") or {}).get("name", "")
            action = result.get("action", "research_more")
            action_ru = {
                "call_now": "звони сейчас",
                "schedule_call": "планируй звонок",
                "research_more": "нужно больше данных",
                "monitor": "мониторь",
            }.get(action, action)
            reply = f"Анализ {company} завершён. Скор: {score}/100. Рекомендация: {action_ru}."
            if lpr:
                reply += f" ЛПР: {lpr}."
            state["final_reply"] = reply
            state["analyst_output"] = {"summary": reply, "leadgen_card": result}

        elif intent == "find_leads_portrait":
            from leadgen.pipeline import search_by_portrait
            portrait = slots.get("portrait", "") or state.get("transcript", "")
            result = await search_by_portrait(portrait, limit=5)
            total = result.get("total", 0)
            state["final_reply"] = f"Нашёл {total} компаний по твоему портрету. Открой вкладку Лидогенерация для просмотра."
            state["analyst_output"] = {"summary": state["final_reply"], "portrait_results": result}

        elif intent == "cluster_company":
            from leadgen.pipeline import run_cluster
            inn = slots.get("inn", "")
            result = await run_cluster(inn)
            related = result.get("total_companies", 1) - 1
            state["final_reply"] = f"Найдено {related} связанных компаний. Открой вкладку Лидогенерация → Кластер для просмотра."
            state["analyst_output"] = {"summary": state["final_reply"], "cluster_result": result}

    except Exception as e:
        logger.error("Leadgen orchestrator error (intent=%s): %s", intent, e)
        state["errors"] = list(state.get("errors", [])) + [str(e)]
        state["final_reply"] = f"Ошибка лидогенерации: {e}"
    return state


async def _run_search_web(state: AgentState, query: str) -> AgentState:
    """Поиск в интернете + LLM-ответ."""
    try:
        from rag.search import free_search
        result = await free_search(query, summarize=True, max_results=10)
        state["final_reply"] = result.get("answer") or result.get("formatted_block") or "Ничего не найдено."
        state["analyst_output"] = {
            "summary": state["final_reply"],
            "search_results": result.get("raw_results", []),
        }
    except Exception as e:
        logger.error("search_web ошибка: %s", e)
        state["final_reply"] = f"Ошибка поиска: {e}"
    return state


async def _run_write_email(state: AgentState) -> AgentState:
    """Маркетолог пишет письмо по слотам (голос write_email → modal)."""
    slots = dict(state.get("slots", {}))
    target = slots.get("target") or slots.get("company") or ""
    if target and not slots.get("company"):
        slots["company"] = target
    if target and not slots.get("contact"):
        slots["contact"] = str(target)
    topic = slots.get("topic") or slots.get("instruction") or "сотрудничество"
    slots.setdefault("instruction", f"Напиши B2B письмо на тему: {topic}")

    try:
        from agents.marketer import _analyze

        output = await _analyze("write_email", slots)
        state["marketer_output"] = output
        fe = output.get("first_email") if isinstance(output.get("first_email"), dict) else {}
        summary = output.get("summary") or ""
        if fe.get("subject") or fe.get("body"):
            state["final_reply"] = summary or "Черновик письма готов."
        else:
            state["final_reply"] = summary or slots.get("_base_reply", "Черновик письма готов.")
    except Exception as e:
        logger.error("write_email ошибка: %s", e)
        state["final_reply"] = f"Ошибка при написании письма: {e}"
    return state
