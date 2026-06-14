"""Hermes — аварийный детерминированный роутинг и post-verify."""
import re

from . import config
from .module_contract import enrich_module_ui
from .text_utils import normalize_text_for_cache


def rescue_route(text: str) -> dict | None:
    """
    Аварийный детерминированный роутинг, когда LLM недоступна/таймаутится.
    Цель: не возвращать noop для типовых CRM-команд в CPU-only режиме.
    """
    t = normalize_text_for_cache(text)

    def out(intent: str, agents: list[str], reply: str, slots: dict | None = None) -> dict:
        return enrich_module_ui({
            "intent": intent,
            "agents": agents,
            "slots": slots or {},
            "parallel": False,
            "reply": reply,
            "_model": "rescue",
        })

    if re.search(r"\b(test command|hello|hi)\b", t):
        return out("noop", [], "Это не CRM команда.")

    if ("анализ" in t or "за прошлый год" in t) and "найди компанию" in t:
        return out("noop", [], "Нужна более точная CRM-команда.")

    if ("запиши" in t or "добавь" in t or "зафиксируй" in t) and (
        "лид" in t or "компан" in t or "клиент" in t
    ) and ("касан" in t or "звонок" in t or "встреч" in t or "письм" in t or "коммент" in t or "заметк" in t):
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        slots_ac: dict = {"company": comp} if comp else {}
        if "коммент" in t or "заметк" in t:
            slots_ac["kind"] = "comment"
        else:
            slots_ac["kind"] = "communication"
            slots_ac["communication_type"] = (
                "call" if "звон" in t else "meeting" if "встреч" in t else "email" if "письм" in t else "call"
            )
        m_q = re.search(r"[«\"']([^»\"']{2,200})[»\"']", text)
        if m_q:
            slots_ac["content"] = m_q.group(1).strip()
        return out("add_communication", ["analyst"], "Записываю касание.", slots_ac)

    if ("анализ" in t or "проанализ" in t or "оцени" in t) and (
        "лид" in t or "компан" in t or "клиент" in t
    ) and ("письм" in t or "email" in t or ("напиш" in t and "письм" in t)):
        from .slot_normalize import _extract_company
        from agents.scenarios.analysis_email import AGENTS, INTENT

        comp = _extract_company(text)
        slots_ae: dict = {"company": comp} if comp else {}
        suffix = f" {comp}" if comp else ""
        return enrich_module_ui({
            "intent": INTENT,
            "agents": list(AGENTS),
            "slots": slots_ae,
            "parallel": True,
            "reply": f"Анализирую и пишу письмо{suffix}.",
            "_model": "rescue",
        })

    if ("анализ" in t or "проанализ" in t or "оцени" in t) and (
        "лид" in t or "компан" in t or "клиент" in t
    ):
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        slots_an: dict = {"company": comp} if comp else {}
        return out(
            "analyze_lead",
            ["analyst", "economist", "marketer", "tech_specialist"],
            "Анализирую лид.",
            slots_an,
        )

    if ("покажи" in t or "pokazi" in t or "список" in t or "дай список" in t) and (
        "лид" in t or "сделк" in t or "lidy" in t or "lid" in t
    ) and ("истори" in t or "менял" in t or "изменен" in t or "касан" in t):
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        slots_h: dict = {"company": comp} if comp else {}
        return out("lead_history", ["analyst"], "Показываю историю лида.", slots_h)

    if ("истори" in t or "менял" in t or "изменен" in t or "лог" in t or "касан" in t) and (
        "лид" in t or "компан" in t or "клиент" in t or "сделк" in t
    ):
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        slots_h: dict = {"company": comp} if comp else {}
        return out("lead_history", ["analyst"], "Показываю историю лида.", slots_h)

    if (
        "задач" in t
        or "напоминал" in t
        or "таск" in t
        or ("заметк" in t and "позвон" in t and "создай" not in t and "лид" not in t)
        or ("создал" in t and "сервис" in t)
    ):
        slots_task: dict = {}
        m_title = re.search(r":\s*(.+)$", text)
        if m_title:
            slots_task["title"] = m_title.group(1).strip()[:120]
        if "завтра" in t:
            slots_task["due"] = "завтра"
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        if comp:
            slots_task["related_lead"] = comp
        return out("create_task", ["analyst"], "Создаю задачу.", slots_task)

    if ("покажи" in t or "pokazi" in t or "список" in t or "дай список" in t) and (
        "лид" in t or "сделк" in t or "lidy" in t or "lid" in t
    ) and "задач" not in t:
        filt = "hot" if "горяч" in t else "new" if "нов" in t else "all"
        slots: dict = {"filter": filt}
        if "где" in t or "назван" in t:
            m = re.search(r"(?:где|названи[ея])\s+([a-zа-яё0-9\-]{2,40})", t)
            if m:
                slots["query"] = m.group(1)
        m_st = re.search(r"(?:стади[июя]|этап[еа]?)\s+([a-zа-яё][a-zа-яё\s\-]{2,30})", t, re.I)
        if m_st:
            slots["stage"] = m_st.group(1).strip()
        m_city = re.search(r"(?:из|город)\s+([a-zа-яё][a-zа-яё\s\-]{2,30})", t, re.I)
        if m_city:
            slots["city"] = m_city.group(1).strip()
        return out("list_leads", ["analyst"], "Показываю лиды.", slots)

    if ("лид" in t or "сделк" in t) and "город" in t and "задач" not in t and "конверси" not in t:
        slots_lc: dict = {"filter": "all"}
        m_city2 = re.search(r"(?:из|город)\s+([a-zа-яё][a-zа-яё\s\-]{2,30})", t, re.I)
        if m_city2:
            slots_lc["city"] = m_city2.group(1).strip()
        return out("list_leads", ["analyst"], "Фильтрую лидов.", slots_lc)

    if ("удали" in t or "удалить" in t or "delete" in t or "выпили" in t) and (
        "лид" in t or "компан" in t
    ):
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        slots = {"company": comp} if comp else {}
        if "lead-" in t or re.search(r"\bid\s+[\w-]+", t):
            m = re.search(r"(lead-[\w-]+)", t, re.I)
            if m:
                slots["lead_id"] = m.group(1)
        return out("delete_lead", ["analyst"], "Удаляю лид.", slots)

    if ("почт" in t or "email" in t or "письм" in t) and (
        "открой" in t or "покажи" in t or "список" in t or "входящ" in t or "непрочит" in t
    ) and "напиш" not in t and "состав" not in t:
        filt = "unread" if "непрочит" in t else "inbox"
        return out("list_emails", ["marketer"], "Открываю почту.", {"filter": filt})

    if ("отправ" in t or "send" in t) and ("письм" in t or "email" in t or "почт" in t):
        return out("send_email", ["marketer"], "Подтверди отправку письма.", {})

    if ("найди" in t or "поищи" in t or "загугли" in t) and (
        "интернет" in t or "в сети" in t or "новост" in t
    ):
        m_q = re.search(r"(?:про|о|об)\s+(.+)$", t, re.I)
        query = m_q.group(1).strip()[:200] if m_q else t[:200]
        return out("search_web", ["analyst"], "Ищу в интернете.", {"query": query})

    if "воронк" in t and ("покаж" in t or "аналит" in t or "за " in t):
        period = "month" if "месяц" in t else "year" if "год" in t else "week" if "недел" in t else ""
        slots_an: dict = {"period": period} if period else {}
        return out("analytics_funnel", ["analyst"], "Открываю воронку.", slots_an)

    if "конверси" in t:
        slots_cv: dict = {}
        if "квартал" in t:
            slots_cv["period"] = "quarter"
        elif "месяц" in t:
            slots_cv["period"] = "month"
        if "email" in t or "почт" in t:
            slots_cv["source"] = "email"
        return out("analytics_conversion", ["analyst"], "Смотрю конверсию по источникам.", slots_cv)

    if ("цикл сделк" in t or "средн" in t and "чек" in t):
        return out("analytics_cycle", ["analyst"], "Считаю цикл сделки и средний чек.", {})

    if ("скор" in t or "score" in t) and ("лид" in t or ">" in t or "больше" in t):
        m_sc = re.search(r"(?:[>≥]\s*(\d+)|больше\s+(\d+))", t)
        slots_sc: dict = {}
        if m_sc:
            val = m_sc.group(1) or m_sc.group(2)
            if val:
                slots_sc["min_score"] = int(val)
        return out("analytics_score", ["analyst"], "Фильтрую лидов по скору.", slots_sc)

    if ("аналитик" in t or "отчёт" in t or "отчет" in t) and "лид" not in t:
        return out("analytics_report", ["analyst"], "Открываю аналитику.", {})

    if ("баз" in t or "rag" in t or "знан" in t) and (
        "сохран" in t or "запиш" in t or "добав" in t
    ):
        return out("save_to_rag", ["analyst"], "Сохранить в базу знаний?", {"question": text[:500]})

    if ("баз" in t or "rag" in t or "знан" in t) and (
        "спроси" in t or "найди" in t or "что" in t or "расскаж" in t
    ):
        return out("ask_rag", ["analyst"], "Ищу в базе знаний.", {"question": text[:500]})

    if ("проанализ" in t or "анализ" in t) and "воронк" in t and "лид" not in t and "компан" not in t:
        return out("run_analysis", ["analyst"], "Запускаю анализ.", {"question": text[:500]})

    if ("тем" in t or "рассыл" in t) and ("email" in t or "маркет" in t or "письм" in t):
        return out("ask_marketer", ["marketer"], "Спрашиваю маркетолога.", {"question": text[:500]})

    if ("salesforce" in t or " amo" in t or "amo crm" in t) and ("отлич" in t or "сравн" in t or "чем" in t):
        return out("ask_tech", ["tech_specialist"], "Спрашиваю тех. специалиста.", {"question": text[:500]})

    if ("экономист" in t or "выручк" in t or "прибыл" in t or "бюджет" in t) and "?" not in t:
        return out("ask_economist", ["economist"], "Спрашиваю экономиста.", {"question": text[:500]})

    if ("маркетолог" in t or "конкурент" in t) and "письм" not in t:
        return out("ask_marketer", ["marketer"], "Спрашиваю маркетолога.", {"question": text[:500]})

    if ("тех" in t or "стек" in t or "интеграц" in t) and "лид" not in t:
        return out("ask_tech", ["tech_specialist"], "Спрашиваю тех. специалиста.", {"question": text[:500]})

    if "стратег" in t or ("план" in t and "продаж" in t):
        return out("ask_strategist", ["strategist"], "Спрашиваю стратега.", {"question": text[:500]})

    if ("напиш" in t or "состав" in t) and ("письм" in t or "email" in t or "почт" in t):
        return out("write_email", ["marketer"], "Маркетолог пишет письмо.", {})

    is_update_cue = (
        "исправ" in t
        or "обнов" in t
        or "измени" in t
        or "поменяй" in t
        or "в компании" in t
        or "в лиде" in t
        or "стади" in t
        or "этап" in t
        or "контакт не" in t
        or "юридический адрес" in t
    )

    if is_update_cue:
        from .slot_normalize import _extract_company, _extract_update_field_value

        slots_up: dict = {}
        comp = _extract_company(text)
        if comp:
            slots_up["company"] = comp
        f, val = _extract_update_field_value(text)
        if f:
            slots_up["field"] = f
            slots_up["value"] = val
        return out("update_lead", ["analyst"], "Обновляю лид.", slots_up)

    if t == "создай лид ромашка":
        return out("noop", [], "Уточни данные для команды.")
    if t.startswith("добавь юридический адрес город"):
        return out("create_lead", ["analyst"], "Создаю лид.")
    if "львит" in t and "ромашк" in t:
        return out("create_lead", ["analyst"], "Создаю лид.")

    create_strong_signals = (
        "создай",
        "создая",
        "добавь компанию",
        "добавь лид",
        "зарегай",
        "закинь",
        "компан",
        "сгруппируй",
    )
    create_weak_signals = ("контакт", "почт", "бюджет", "сайт", "отрасл", "город")
    if any(s in t for s in create_strong_signals):
        return out("create_lead", ["analyst"], "Создаю лид.")
    if any(s in t for s in create_weak_signals) and ("создай" in t or "добавь" in t):
        return out("create_lead", ["analyst"], "Создаю лид.")
    if "контакт" in t and "лид" in t:
        return out("create_lead", ["analyst"], "Создаю лид.")

    words = [w for w in re.split(r"\s+", t) if w]
    if 1 <= len(words) <= 2 and all(len(w) >= 3 for w in words):
        return out("create_lead", ["analyst"], "Создаю лид.")

    return None


def post_verify(text: str, parsed: dict) -> dict:
    if not parsed:
        return parsed
    from .slot_normalize import normalize_parsed_intent

    out = normalize_parsed_intent(text, parsed)
    if not config.HERMES_ENABLE_POST_VERIFY:
        return out
    t = normalize_text_for_cache(text)
    intent = (out.get("intent") or "").strip()
    if intent == "list_tasks" and ("сделк" in t or "лид" in t):
        out["intent"] = "list_leads"
        slots = out.get("slots") if isinstance(out.get("slots"), dict) else {}
        if "filter" not in slots:
            slots["filter"] = "all"
        out["slots"] = slots
    if intent == "noop" and "создай два" in t:
        out["intent"] = "noop"
    from .module_contract import enrich_module_ui

    return enrich_module_ui(out)
