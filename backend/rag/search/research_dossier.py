"""Досье веб-исследования: LLM-синтез (Groq→Ollama) + fallback для агентов."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_SECTION_HEADERS = (
    "## 1. Профиль компании",
    "## 2. Продукты и услуги",
    "## 3. Рынок, клиенты, география",
    "## 4. Масштаб и финансы (сигналы)",
    "## 5. Новости и свежие сигналы",
    "## 6. Технологии / ИТ",
    "## 7. Контакты и точки входа",
    "## 8. Риски и пробелы",
    "## 9. Источники",
)


def is_error_summary(text: str) -> bool:
    s = (text or "").strip().lower()
    if not s:
        return True
    return (
        s.startswith("ошибка синтеза")
        or s.startswith("ошибка исследования")
        or "connection attempts failed" in s
        or "all connection attempts failed" in s
    )


def build_synthesis_prompt(
    *,
    company: str,
    today: str,
    year: str,
    context: str,
    formatted_hits: str,
    page_texts: str = "",
) -> str:
    pages_block = ""
    if page_texts.strip():
        pages_block = f"\n\nТексты страниц (фрагменты):\n{page_texts[:12000]}\n"

    return (
        f"Ты — B2B-исследователь SmartCRM. Дата сегодня: {today}.\n"
        f"Собери ПОЛНОЕ досье компании «{company}» для CRM-агентов "
        f"(аналитик, экономист, маркетолог, техспец, стратег).\n"
        "Агенты НЕ ходят в интернет — только по твоему тексту. Пиши полно и по делу.\n\n"
        f"Контекст карточки: {context}\n\n"
        "Структура (все разделы обязательны; нет данных → «нет данных в источниках»):\n"
        f"{_SECTION_HEADERS[0]}\n"
        "Чем занимаются, юр.форма/бренд, сайт, отрасль.\n"
        f"{_SECTION_HEADERS[1]}\n"
        "Линейки, услуги, позиционирование.\n"
        f"{_SECTION_HEADERS[2]}\n"
        "Кому продают, география, конкуренты (если есть).\n"
        f"{_SECTION_HEADERS[3]}\n"
        "Выручка/сотрудники/масштаб — только если есть в источниках.\n"
        f"{_SECTION_HEADERS[4]} ({year})\n"
        "Свежие новости и сигналы; отделяй устаревшее.\n"
        f"{_SECTION_HEADERS[5]}\n"
        "Стек, цифровизация — если есть.\n"
        f"{_SECTION_HEADERS[6]}\n"
        "ЛПР, телефоны, email, формы — если есть.\n"
        f"{_SECTION_HEADERS[7]}\n"
        "Что неясно, противоречия, что проверить.\n"
        f"{_SECTION_HEADERS[8]}\n"
        "Список [N] title + url из источников ниже.\n\n"
        "Правила: только факты из источников; ссылайся [N]; не выдумывай; на русском; "
        "игнорируй посольства/чужие страны без связи с компанией.\n\n"
        f"Источники поиска:\n{formatted_hits}"
        f"{pages_block}"
    )


def fallback_dossier_from_hits(company: str, hits: list[dict], today: str) -> str:
    """Структурированная выжимка без LLM — чтобы агенты всё равно имели опору."""
    year = today[:4]
    lines = [
        f"Досье «{company}» на {today} (собрано из поиска, без LLM).",
        "",
        _SECTION_HEADERS[0],
        f"Название: {company}. Детали — по сниппетам ниже.",
        "",
        _SECTION_HEADERS[1],
        "нет данных в источниках (нужен LLM/страницы) — см. сниппеты.",
        "",
        _SECTION_HEADERS[2],
        "нет данных в источниках.",
        "",
        _SECTION_HEADERS[3],
        "нет данных в источниках.",
        "",
        f"{_SECTION_HEADERS[4]} ({year})",
    ]
    if not hits:
        lines.append("• Веб-результаты пусты. Проверьте ключи Serper/Brave/Tavily.")
    else:
        for i, h in enumerate(hits[:12], 1):
            title = (h.get("title") or "без названия").strip()
            snip = (h.get("snippet") or h.get("description") or "").strip().replace("\n", " ")
            if len(snip) > 220:
                snip = snip[:220] + "…"
            date = (h.get("date") or "").strip()
            bit = f"[{i}] {title}"
            if date:
                bit += f" ({date})"
            lines.append(bit)
            if snip:
                lines.append(f"    {snip}")
    lines.extend(
        [
            "",
            _SECTION_HEADERS[5],
            "нет данных в источниках.",
            "",
            _SECTION_HEADERS[6],
            "нет данных в источниках.",
            "",
            _SECTION_HEADERS[7],
            "Выжимка без LLM — перезапустите «Исследовать» при живом Groq/Ollama.",
            "",
            _SECTION_HEADERS[8],
        ]
    )
    for i, h in enumerate(hits[:12], 1):
        url = (h.get("url") or h.get("link") or "").strip()
        title = (h.get("title") or "").strip() or url or "—"
        if url:
            lines.append(f"[{i}] {title} — {url}")
        else:
            lines.append(f"[{i}] {title}")
    return "\n".join(lines)


def agent_brief_from_summary(summary: str, *, max_chars: int = 4500) -> str:
    """Краткий блок для промптов агентов (без обрезки середины разделов грубо)."""
    text = (summary or "").strip()
    if not text or is_error_summary(text):
        return ""
    if len(text) <= max_chars:
        return text
    # Режем по последнему разделу, который влезает
    cut = text[:max_chars]
    last_hdr = cut.rfind("\n## ")
    if last_hdr > max_chars // 2:
        cut = cut[:last_hdr].rstrip()
    return cut + "\n\n[…досье обрезано; полное в checko.analyses.web_research.summary]"


async def synthesize_dossier_llm(
    *,
    company: str,
    today: str,
    year: str,
    context: str,
    formatted_hits: str,
    page_texts: str = "",
) -> tuple[str, str | None]:
    """
    Синтез досье: сначала Groq, затем Ollama.
    Возвращает (текст, провайдер) или ("", None) при полном провале.
    """
    from core.llm import chat

    prompt = build_synthesis_prompt(
        company=company,
        today=today,
        year=year,
        context=context,
        formatted_hits=formatted_hits,
        page_texts=page_texts,
    )
    messages = [{"role": "user", "content": prompt}]

    for model in ("groq", "ollama"):
        try:
            answer = await chat(
                messages,
                model=model,
                temperature=0.3,
                max_tokens=2800,
            )
            answer = (answer or "").strip()
            if answer and not is_error_summary(answer):
                logger.info("research_dossier синтез через %s (%s симв.)", model, len(answer))
                return answer, model
            logger.warning("research_dossier %s: пустой/ошибочный ответ", model)
        except Exception as e:
            logger.warning("research_dossier %s недоступен: %s: %s", model, type(e).__name__, e)

    return "", None


def extract_web_research_brief(lead: dict[str, Any] | None) -> str:
    """Достаёт agent_brief/summary из лида для агентов."""
    if not lead:
        return ""
    checko = lead.get("checko")
    if not isinstance(checko, dict):
        return ""
    analyses = checko.get("analyses")
    if not isinstance(analyses, dict):
        return ""
    wr = analyses.get("web_research")
    if not isinstance(wr, dict):
        return ""
    brief = str(wr.get("agent_brief") or wr.get("summary") or "").strip()
    if not brief or is_error_summary(brief):
        return ""
    at = wr.get("at") or ""
    header = f"Веб-исследование{f' ({at})' if at else ''} — пользоваться вместо поиска в сети:"
    return f"{header}\n{brief}"
