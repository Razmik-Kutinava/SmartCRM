"""
LangGraph оркестратор — роутит задачи между агентами (параллельно).
Граф: analyst (и др.) параллельно → strategist → финальный ответ.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from agents.base import AgentState, make_initial_state

logger = logging.getLogger(__name__)

# Интенты, при которых запускается полная агентная цепочка
_AGENT_INTENTS = frozenset({
    "create_lead", "update_lead", "delete_lead", "list_leads", "analyze_lead",
    # Голосовые запросы к отдельным агентам и анализ
    "run_analysis", "ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
    "search_web", "write_email",
    # Лидогенерация
    "generate_lead", "find_leads_portrait", "cluster_company",
})

# Интенты, при которых достаточно только аналитика (без стратега)
_ANALYST_ONLY = frozenset({
    "list_leads",
})

# Маппинг: интент → какие агенты запускаются
_INTENT_TO_AGENTS: dict[str, list[str]] = {
    "ask_economist":   ["economist"],
    "ask_marketer":    ["marketer"],
    "ask_tech":        ["tech_specialist"],
    "ask_strategist":  ["strategist"],
    "search_web":      ["analyst"],
    "write_email":     ["marketer"],
    "run_analysis":    ["analyst", "economist", "marketer", "tech_specialist"],
    # Лидогенерация — роутим в специальный хэндлер
    "generate_lead":       ["analyst", "tech_specialist", "marketer", "strategist"],
    "find_leads_portrait": ["analyst"],
    "cluster_company":     ["analyst"],
}


async def run_agents(
    intent: str,
    slots: dict[str, Any],
    transcript: str = "",
    trace_id: str = "",
) -> dict[str, Any]:
    """
    Главная точка входа оркестратора.
    Возвращает dict с final_reply, recommendation, agent_outputs, timings.
    """
    if intent not in _AGENT_INTENTS:
        return {
            "agents_ran": False,
            "final_reply": slots.get("reply", ""),
            "recommendation": "",
            "analyst_output": None,
            "strategist_output": None,
            "timings_ms": {},
        }

    from rag.retrieve import attach_rag_to_slots

    slots_enriched = await attach_rag_to_slots({**slots}, transcript)
    state = make_initial_state(intent, slots_enriched, transcript, trace_id)
    # Сохраняем базовый reply от Hermes для фолбека стратега
    state["slots"] = {**slots_enriched, "_base_reply": slots.get("reply", "")}

    t_total = time.monotonic()
    logger.info("Оркестратор: запуск для intent=%s", intent)

    # Голосовые запросы к конкретному агенту или поиск — особый маршрут
    if intent in _INTENT_TO_AGENTS:
        state = await _run_voice_query(state, intent)
        total_ms = round((time.monotonic() - t_total) * 1000)
        return {
            "agents_ran": True,
            "final_reply": state.get("final_reply") or slots.get("reply", ""),
            "recommendation": state.get("recommendation", ""),
            "analyst_output": state.get("analyst_output"),
            "strategist_output": state.get("strategist_output"),
            "economist_output": state.get("economist_output"),
            "marketer_output": state.get("marketer_output"),
            "tech_output": state.get("tech_output"),
            "timings_ms": {**state.get("agent_timings", {}), "total": total_ms},
            "errors": state.get("errors", []),
            "actions_taken": state.get("actions_taken", []),
        }

    # Шаг 1: параллельные агенты (сейчас аналитик; позже +economist, +marketer)
    state = await _run_parallel_agents(state, intent)

    # Шаг 2: стратег (только если нужен)
    if intent not in _ANALYST_ONLY:
        state = await _run_strategist(state)
    else:
        # Для list_leads — финальный ответ берём из аналитика
        analyst_summary = (state.get("analyst_output") or {}).get("summary", "")
        state["final_reply"] = analyst_summary or slots.get("reply", "")

    total_ms = round((time.monotonic() - t_total) * 1000)
    logger.info(
        "Оркестратор завершил: intent=%s, итого %s мс, финальный ответ: %s",
        intent, total_ms, (state.get("final_reply") or "")[:80],
    )

    return {
        "agents_ran": True,
        "final_reply": state.get("final_reply") or slots.get("reply", ""),
        "recommendation": state.get("recommendation", ""),
        "analyst_output": state.get("analyst_output"),
        "strategist_output": state.get("strategist_output"),
        "economist_output": state.get("economist_output"),
        "marketer_output": state.get("marketer_output"),
        "timings_ms": {**state.get("agent_timings", {}), "total": total_ms},
        "errors": state.get("errors", []),
        "actions_taken": state.get("actions_taken", []),
    }


async def _run_voice_query(state: AgentState, intent: str) -> AgentState:
    """
    Обрабатывает голосовые запросы к конкретному агенту или поиск в интернете.
    Интенты: ask_economist, ask_marketer, ask_tech, ask_strategist, search_web,
             write_email, run_analysis.
    """
    agent_ids = _INTENT_TO_AGENTS.get(intent, ["analyst"])
    slots = state.get("slots", {})
    question = slots.get("question") or slots.get("query") or state.get("transcript", "")
    company = slots.get("company", "")
    context = slots.get("context", "")

    # Лидогенерация — делегируем в pipeline
    if intent in ("generate_lead", "find_leads_portrait", "cluster_company"):
        return await _run_leadgen(state, intent)

    # Для search_web — запускаем поиск и строим ответ через аналитика
    if intent == "search_web":
        return await _run_search_web(state, question)

    # Для write_email — маркетолог пишет письмо
    if intent == "write_email":
        return await _run_write_email(state)

    # run_analysis — все агенты параллельно + стратег итожит
    if intent == "run_analysis":
        tasks_to_run = []
        from agents import analyst, economist, marketer, tech_specialist
        for ag_id in agent_ids:
            if ag_id == "analyst":
                tasks_to_run.append(analyst.run(state))
            elif ag_id == "economist":
                tasks_to_run.append(economist.run(state))
            elif ag_id == "marketer":
                tasks_to_run.append(marketer.run(state))
            elif ag_id == "tech_specialist":
                tasks_to_run.append(tech_specialist.run(state))
        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("run_analysis агент #%s ошибка: %s", i, result)
                state["errors"] = list(state.get("errors", [])) + [str(result)]
            else:
                state = _merge_state(state, result)
        state = await _run_strategist(state)
        return state

    # ask_* — запускаем один агент + используем поиск для контекста
    agent_id = agent_ids[0]
    t0 = time.monotonic()

    # Обогащаем контекст поиском если есть вопрос
    search_context = ""
    if question or company:
        try:
            from rag.search import free_search
            search_q = f"{company} {question}".strip() if company else question
            search_result = await free_search(search_q, summarize=False, max_results=8)
            search_context = search_result.get("formatted_block", "")
        except Exception as e:
            logger.warning("voice_query поиск ошибка: %s", e)

    # Строим промпт для агента
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

    # Вставляем в slots для агента
    enriched_slots = {**slots, "voice_query": prompt_ctx, "_search_context": search_context}
    state["slots"] = enriched_slots

    try:
        from core.llm import chat
        AGENT_SYSTEM_PROMPTS = {
            "economist": "Ты — финансовый аналитик и экономист с глубокими знаниями рынков, финансовой отчётности и инвестиций. Дай чёткий ответ с цифрами и фактами.",
            "marketer": "Ты — старший маркетолог B2B с экспертизой в анализе рынков, конкурентов и трендов. Дай конкретный аналитический ответ.",
            "tech_specialist": "Ты — технический директор с глубокими знаниями IT-стеков, SaaS-решений и технологических трендов. Дай детальный технический ответ.",
            "strategist": "Ты — бизнес-стратег с опытом в B2B-продажах. Разработай конкретный, применимый план или стратегию.",
            "analyst": "Ты — старший CRM-аналитик с 15-летним опытом. Дай структурированный аналитический ответ.",
        }
        system = AGENT_SYSTEM_PROMPTS.get(agent_id, "Ты — эксперт. Дай точный ответ.")
        answer = await chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt_ctx},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        elapsed_ms = round((time.monotonic() - t0) * 1000)
        state["final_reply"] = answer
        state["agent_timings"] = {**state.get("agent_timings", {}), agent_id: elapsed_ms}
        # Кладём результат в нужное поле state
        output_key = f"{agent_id}_output"
        if agent_id == "tech_specialist":
            output_key = "tech_output"
        state[output_key] = {"summary": answer, "search_context": search_context}
        logger.info("voice_query %s ответил за %s мс", agent_id, elapsed_ms)
    except Exception as e:
        logger.error("voice_query агент %s ошибка: %s", agent_id, e)
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
    """Маркетолог пишет письмо по слотам."""
    slots = state.get("slots", {})
    target = slots.get("target", "клиенту")
    topic = slots.get("topic", "сотрудничество")
    tone = slots.get("tone", "formal")
    tone_desc = {"formal": "деловое", "friendly": "дружелюбное", "urgent": "срочное"}.get(tone, "деловое")

    # Обогащаем контекстом из поиска
    search_context = ""
    try:
        from rag.search import free_search
        r = await free_search(f"{target} {topic}", summarize=False, max_results=5)
        search_context = r.get("formatted_block", "")
    except Exception:
        pass

    try:
        from core.llm import chat
        prompt = (
            f"Напиши {tone_desc} B2B письмо для компании {target} на тему: {topic}.\n"
            f"Письмо должно быть конкретным, с ценностным предложением, без лишней воды.\n"
        )
        if search_context:
            prompt += f"\nКонтекст о компании:\n{search_context}\n"
        prompt += "\nСтруктура: тема письма, приветствие, суть, призыв к действию, подпись."
        answer = await chat(
            [{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
        )
        state["final_reply"] = answer
        state["marketer_output"] = {"summary": answer}
    except Exception as e:
        logger.error("write_email ошибка: %s", e)
        state["final_reply"] = f"Ошибка при написании письма: {e}"
    return state


async def _run_parallel_agents(state: AgentState, intent: str) -> AgentState:
    """Параллельно запускаем нужных агентов первого уровня."""
    from agents import analyst  # импорт здесь, чтобы избежать циклов

    tasks_to_run = [analyst.run(state)]

    # Полный контур: новый лид или глубокий анализ существующего из CRM
    if intent in ("create_lead", "analyze_lead"):
        from agents import economist, marketer, tech_specialist
        tasks_to_run.append(economist.run(state))
        tasks_to_run.append(marketer.run(state))
        tasks_to_run.append(tech_specialist.run(state))
    elif intent == "update_lead":
        from agents import economist, marketer, tech_specialist
        tasks_to_run.append(economist.run(state))
        tasks_to_run.append(marketer.run(state))
        tasks_to_run.append(tech_specialist.run(state))

    results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("Агент #%s вернул исключение: %s", i, result)
            state["errors"] = list(state.get("errors", [])) + [str(result)]
        else:
            # Мержим выходы агентов в общий state
            state = _merge_state(state, result)

    return state


async def _run_strategist(state: AgentState) -> AgentState:
    """Запускаем стратега после параллельных агентов."""
    from agents import strategist

    try:
        state = await strategist.run(state)
    except Exception as e:
        logger.error("Стратег вернул исключение: %s", e)
        state["errors"] = list(state.get("errors", [])) + [str(e)]
        state["final_reply"] = state.get("slots", {}).get("_base_reply", "Выполнено.")

    return state


def _merge_state(base: AgentState, update: AgentState) -> AgentState:
    """Слияние двух state: обновляем только непустые поля из update."""
    merged = dict(base)
    for key, val in update.items():
        if key in ("errors", "actions_taken"):
            base_list = list(merged.get(key, []))
            new_list = list(val or [])
            merged[key] = base_list + [x for x in new_list if x not in base_list]
        elif key == "agent_timings":
            merged[key] = {**merged.get(key, {}), **(val or {})}
        elif val is not None:
            merged[key] = val
    return AgentState(**merged)
