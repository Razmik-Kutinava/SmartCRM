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

    if re.search(r"\b(привет|как настроение|что нового|кто ты|ты кто)\b", t):
        return out("noop", [], "Это не CRM команда.")

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

    from agents.scenarios.tender_evaluation import (
        AGENTS as TENDER_AGENTS,
        INTENT as TENDER_INTENT,
        matches_rescue,
        tender_slots_from_text,
    )
    from agents.scenarios.tender_search import (
        INTENT as TENDER_SEARCH_INTENT,
        list_tenders_slots,
        matches_list,
        matches_search,
        tender_search_slots,
    )

    if matches_list(text):
        return enrich_module_ui({
            "intent": "list_tenders",
            "agents": ["analyst"],
            "slots": list_tenders_slots(),
            "parallel": False,
            "reply": "Открываю мои тендеры.",
            "_model": "rescue",
        })

    if ("найди" in t or "поищи" in t or "загугли" in t) and (
        "интернет" in t or "в сети" in t or "новост" in t
    ):
        m_q = re.search(r"(?:про|о|об)\s+(.+)$", t, re.I)
        query = m_q.group(1).strip()[:200] if m_q else t[:200]
        return out("search_web", ["analyst"], "Ищу в интернете.", {"query": query})

    if matches_search(text) and "интернет" not in t and "в сети" not in t:
        slots_ts = tender_search_slots(text)
        q = slots_ts.get("query", "")
        suffix = f" по «{q}»" if q else ""
        return enrich_module_ui({
            "intent": TENDER_SEARCH_INTENT,
            "agents": ["analyst"],
            "slots": slots_ts,
            "parallel": False,
            "reply": f"Ищу тендеры{suffix}.",
            "_model": "rescue",
        })

    if matches_rescue(text):
        slots_te = tender_slots_from_text(text)
        title = slots_te.get("title", "")
        suffix = f" «{title}»" if title else ""
        return enrich_module_ui({
            "intent": TENDER_INTENT,
            "agents": list(TENDER_AGENTS),
            "slots": slots_te,
            "parallel": True,
            "reply": f"Оцениваю тендер{suffix}: тех.спец и экономист.",
            "_model": "rescue",
        })

    from agents.scenarios.weekly_report import (
        AGENTS as WEEKLY_AGENTS,
        INTENT as WEEKLY_INTENT,
        matches_rescue as weekly_matches_rescue,
        weekly_report_slots_from_text,
    )

    if weekly_matches_rescue(text):
        slots_wr = weekly_report_slots_from_text(text)
        return enrich_module_ui({
            "intent": WEEKLY_INTENT,
            "agents": list(WEEKLY_AGENTS),
            "slots": slots_wr,
            "parallel": True,
            "reply": "Собираю еженедельный отчёт: аналитик, экономист и маркетолог.",
            "_model": "rescue",
        })

    from agents.scenarios.leadgen_voice import (
        CLUSTER_INTENT,
        GENERATE_AGENTS,
        GENERATE_INTENT,
        PORTRAIT_AGENTS,
        PORTRAIT_INTENT,
        cluster_slots_from_text,
        generate_slots_from_text,
        matches_cluster,
        matches_generate,
        matches_portrait,
        portrait_slots_from_text,
    )

    if matches_generate(text):
        slots_lg = generate_slots_from_text(text)
        inn = slots_lg.get("inn", "")
        suffix = f" ИНН {inn}" if inn else ""
        return enrich_module_ui({
            "intent": GENERATE_INTENT,
            "agents": list(GENERATE_AGENTS),
            "slots": slots_lg,
            "parallel": True,
            "reply": f"Запускаю лидоген{suffix}.",
            "_model": "rescue",
        })

    if matches_portrait(text):
        slots_lp = portrait_slots_from_text(text)
        return enrich_module_ui({
            "intent": PORTRAIT_INTENT,
            "agents": list(PORTRAIT_AGENTS),
            "slots": slots_lp,
            "parallel": False,
            "reply": "Ищу компании по портрету на /leadgen.",
            "_model": "rescue",
        })

    if matches_cluster(text):
        slots_cl = cluster_slots_from_text(text)
        return enrich_module_ui({
            "intent": CLUSTER_INTENT,
            "agents": list(PORTRAIT_AGENTS),
            "slots": slots_cl,
            "parallel": False,
            "reply": "Открываю кластер-поиск на /leadgen.",
            "_model": "rescue",
        })

    from agents.scenarios.enrich_voice import (
        AGENTS as ENRICH_AGENTS,
        INTENT as ENRICH_INTENT,
        enrich_slots_from_text,
        matches_rescue as enrich_matches_rescue,
    )

    if enrich_matches_rescue(text):
        slots_en = enrich_slots_from_text(text)
        anchor = slots_en.get("company") or slots_en.get("lead_id") or ""
        suffix = f" {anchor}" if anchor else ""
        return enrich_module_ui({
            "intent": ENRICH_INTENT,
            "agents": list(ENRICH_AGENTS),
            "slots": slots_en,
            "parallel": False,
            "reply": f"Обогащаю карточку{suffix} — подтверди запись.",
            "_model": "rescue",
        })

    from agents.scenarios.similar_clients import (
        AGENTS as SIMILAR_AGENTS,
        INTENT as SIMILAR_INTENT,
        matches_rescue as similar_matches_rescue,
        similar_slots_from_text,
    )

    if similar_matches_rescue(text):
        slots_sc = similar_slots_from_text(text)
        anchor = slots_sc.get("company") or slots_sc.get("inn") or ""
        suffix = f" ({anchor})" if anchor else ""
        return enrich_module_ui({
            "intent": SIMILAR_INTENT,
            "agents": list(SIMILAR_AGENTS),
            "slots": slots_sc,
            "parallel": True,
            "reply": f"Ищу похожих клиентов{suffix}: аналитик и маркетолог.",
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
        ("задач" in t or "таск" in t)
        and ("какие" in t or "список" in t or "покажи" in t or "открыт" in t or "просроч" in t or "сегодня" in t)
        and "создай" not in t
        and "напоминал" not in t
        and "отметь" not in t
        and "удали" not in t
        and "убери" not in t
        and "перенес" not in t
    ):
        filt = (
            "today"
            if "сегодня" in t
            else "overdue"
            if "просроч" in t
            else "open"
            if "открыт" in t
            else "all"
        )
        return out("list_tasks", ["analyst"], "Список задач.", {"filter": filt})

    if ("удали" in t or "убери" in t) and ("задач" in t or "таск" in t) and "лид" not in t:
        slots_dt: dict = {}
        m_id = re.search(r"(?:номер|#|id)\s*(\d+)", t)
        if m_id:
            slots_dt["task_id"] = m_id.group(1)
        m_title = re.search(r"[«\"']([^»\"']+)[»\"']", text)
        if m_title:
            slots_dt["title"] = m_title.group(1).strip()
        else:
            m_plain = re.search(r"с названием\s+(.+)$", t)
            if m_plain:
                slots_dt["title"] = m_plain.group(1).strip()[:120]
        return out("delete_task", ["analyst"], "Удаляю задачу.", slots_dt)

    if ("отметь" in t or "выполнен" in t) and ("задач" in t or "таск" in t or "звонок" in t):
        slots_ut: dict = {"status": "выполнен"}
        m_title = re.search(r"задач[уа]?\s+про\s+(.+?)\s+отметь", t)
        if not m_title:
            m_title = re.search(r"задач[уа]?\s+(.+?)\s+отметь", t)
        if m_title:
            slots_ut["title"] = m_title.group(1).strip()[:120]
        return out("update_task", ["analyst"], "Обновляю задачу.", slots_ut)

    if "перенес" in t and ("дедлайн" in t or "задач" in t or "таск" in t):
        slots_ud: dict = {}
        m_title = re.search(r"[«\"']([^»\"']+)[»\"']", text)
        if m_title:
            slots_ud["title"] = m_title.group(1).strip()
        if "понедельник" in t:
            slots_ud["due"] = "понедельник"
        return out("update_task", ["analyst"], "Переношу дедлайн.", slots_ud)

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

    # Выбор лида по порядковому числителю/номеру: «первый», «второй», «лид № 3», «номер 2»
    # Должно срабатывать ДО общего паттерна «открой её»
    _WORD_TO_NUM = {
        "первый": 1, "второй": 2, "третий": 3, "четвёртый": 4, "четвертый": 4,
        "пятый": 5, "шестой": 6, "седьмой": 7, "восьмой": 8, "девятый": 9, "десятый": 10,
    }

    def _word_to_num(word: str) -> int:
        w = word.lower()
        if w in _WORD_TO_NUM:
            return _WORD_TO_NUM[w]
        try:
            return int(w)
        except ValueError:
            return 0

    m_ord = re.search(r"\b(первый|второй|третий|четвёртый|четвертый|пятый|шестой|седьмой|восьмой|девятый|десятый)\b", t)
    m_num = re.search(r"\b(?:лид\s*№?\s*|номер\s*)(\d{1,2})\b", t)
    if (m_ord or m_num):
        n = _word_to_num(m_ord.group(1)) if m_ord else int(m_num.group(1))
        if n >= 1:
            idx = n - 1
            slots = {"selected_index": idx}
            from core.agent_memory import get_last_search_candidates
            candidates = get_last_search_candidates()
            if candidates and len(candidates) >= n:
                slots["lead_id"] = candidates[idx]["id"]
                return out("open_lead", ["analyst"], f"Открываю лид №{n}: {candidates[idx].get('company', '')}.", slots)
            return out("open_lead", ["analyst"], f"Открываю {m_ord.group(1) if m_ord else m_num.group(0)}.", slots)

    # «открой её / этот» — без имени → прошлый найденный лид
    if re.search(r"\b(открой|открыть)\b", t) and "почт" not in t and "email" not in t:
        if re.search(
            r"\b(её|ее|его|этот|эту|эту карточку|найденн\w*|последн\w*)\b",
            t,
        ) and not re.search(r"лид\w*\s+[a-zа-яё0-9]", t):
            return out("open_lead", ["analyst"], "Открываю найденный лид.", {"ref": "last"})
        if "лид" in t or "карточк" in t or "клиент" in t:
            from .slot_normalize import _extract_company

            comp = _extract_company(text)
            if not comp:
                m_ol = re.search(
                    r"(?:открой|открыть)\s+(?:лид(?:а|у)?|карточку|клиента)?\s*(.+)$",
                    t,
                    re.I,
                )
                if m_ol:
                    comp = m_ol.group(1).strip()[:80]
            if comp and comp not in ("её", "ее", "его", "этот", "эту"):
                return out(
                    "open_lead",
                    ["analyst"],
                    f"Открываю лид {comp}.",
                    {"company": comp},
                )
            return out("open_lead", ["analyst"], "Открываю найденный лид.", {"ref": "last"})

    # «найди другой лид» / «другой» → сброс памяти + новый поиск
    if ("найди" in t or "поищи" in t) and "другой" in t and ("лид" in t or "клиент" in t):
        slots_reset: dict = {"filter": "all", "_clear_voice_memory": True}
        return out("list_leads", ["analyst"], "Ищу другой лид.", slots_reset)

    # «найди лид …» → фильтр списка (не веб и не тендеры)
    if ("найди" in t or "найти" in t or "поищи" in t) and (
        "лид" in t or "клиент" in t
    ) and "интернет" not in t and "тендер" not in t and "закуп" not in t:
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        if not comp:
            m_fl = re.search(
                r"(?:найди|найти|поищи)\s+(?:лид(?:а|у)?|клиента)?\s*(.+)$",
                t,
                re.I,
            )
            if m_fl:
                comp = m_fl.group(1).strip()[:80]
        slots_find: dict = {"filter": "all"}
        if comp:
            slots_find["query"] = comp
        return out("list_leads", ["analyst"], f"Ищу лид {comp or ''}.".strip(), slots_find)

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
        or "отправлен" in t or "архив" in t
    ) and "напиш" not in t and "состав" not in t and "отправь" not in t and "отправить" not in t:
        if "отправлен" in t:
            filt = "sent"
        elif "архив" in t:
            filt = "archive"
        else:
            filt = "unread" if "непрочит" in t else "inbox"
        return out("list_emails", ["marketer"], "Открываю почту.", {"filter": filt})

    if ("отправь" in t or "отправить" in t or re.search(r"\bsend\b", t)) and (
        "письм" in t or "email" in t or "почт" in t
    ):
        slots_se: dict = {}
        m_em = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", text, re.I)
        if m_em:
            slots_se["target"] = m_em.group(1)
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        if comp and not slots_se.get("target"):
            slots_se["company"] = comp
        return out("send_email", ["marketer"], "Подтверди отправку письма.", slots_se)

    if ("найди" in t or "поищи" in t or "загугли" in t) and (
        "интернет" in t or "в сети" in t or "новост" in t
    ):
        m_q = re.search(r"(?:про|о|об)\s+(.+)$", t, re.I)
        query = m_q.group(1).strip()[:200] if m_q else t[:200]
        return out("search_web", ["analyst"], "Ищу в интернете.", {"query": query})

    if "загугли" in t or re.search(r"\bгугл", t):
        m_q = re.search(r"(?:про|о|об|конкурент\w*)\s+(.+)$", t, re.I)
        query = (m_q.group(1).strip()[:200] if m_q else re.sub(r"^загугли\s*", "", t))[:200]
        return out("search_web", ["analyst"], "Ищу в интернете.", {"query": query})

    if ("скинь" in t or "дай сводку" in t or "сводк" in t) and (
        "воронк" in t or "конверси" in t or "аналит" in t
    ) and "лид" not in t and "компан" not in t:
        return out("run_analysis", ["analyst"], "Запускаю анализ.", {"question": text[:500]})

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
        from .slot_normalize import _extract_company

        slots_we: dict = {}
        comp = _extract_company(text)
        if comp:
            slots_we["target"] = comp
            slots_we["company"] = comp
        m_client = re.search(r"клиент[уа]?\s+([a-zа-яё0-9\-]+)", t, re.I)
        if m_client and not slots_we.get("company"):
            name = m_client.group(1).strip()
            slots_we["target"] = name
            slots_we["company"] = name
        m_topic = re.search(r"(?:про|о|об|на тему)\s+(.+)$", t, re.I)
        if m_topic:
            slots_we["topic"] = m_topic.group(1).strip()[:200]
        if "срочн" in t:
            slots_we["tone"] = "urgent"
        elif "дружел" in t:
            slots_we["tone"] = "friendly"
        else:
            slots_we["tone"] = "formal"
        return out("write_email", ["marketer"], "Маркетолог пишет письмо.", slots_we)

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
    if re.search(r"создай\s+(?:два|2|три|3)\s+лид", t):
        return out("noop", [], "Уточни данные для каждого лида.")
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
    if intent == "save_to_rag" and ("закинь" in t or "зарегай" in t) and re.search(r"\+?\d{7,}", text):
        out["intent"] = "create_lead"
    if intent.startswith("analytics_") and ("скинь" in t or "сводк" in t or "дай сводку" in t):
        if "лид" not in t and "компан" not in t:
            out["intent"] = "run_analysis"
    if intent in ("find_leads_portrait", "list_leads", "generate_lead") and (
        "загугли" in t or "гугл" in t or "в интернет" in t
    ):
        out["intent"] = "search_web"
    if intent in ("generate_lead", "ask_economist", "noop", "create_lead") and "стратег" in t:
        out["intent"] = "ask_strategist"
        slots = out.get("slots") if isinstance(out.get("slots"), dict) else {}
        if "question" not in slots:
            slots["question"] = text[:500]
        out["slots"] = slots
    if intent == "noop" and "создай два" in t:
        out["intent"] = "noop"
    from .module_contract import enrich_module_ui

    return enrich_module_ui(out)
