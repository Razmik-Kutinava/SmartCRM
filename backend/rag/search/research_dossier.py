"""Досье веб-исследования: LLM-синтез (Groq→Ollama) + fallback для агентов."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Раздел 10 идёт одним проходом с досье — экономит второй LLM-вызов на паспорт
PASSPORT_JSON_HEADER = "## 10. JSON-паспорт"

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
        "Список [N] title + url из источников ниже.\n"
        f"{PASSPORT_JSON_HEADER}\n"
        "Последний раздел — ОДИН JSON-объект (без ``` и пояснений) с полями: "
        "phones[], emails[], contacts[{name, role, position, phones, emails}], "
        "industry, city, website, employees, revenue, director, director_post, address, okved_name. "
        "role: lpr | other. Нет данных → null или [].\n\n"
        "Правила: только факты из источников; ссылайся [N]; не выдумывай; на русском; "
        "игнорируй посольства/чужие страны без связи с компанией.\n\n"
        f"Источники поиска:\n{formatted_hits}"
        f"{pages_block}"
    )


_NO_DATA = "нет данных в источниках."

# Ключевые слова: сниппет → раздел досье (порядок = приоритет раздела)
_SECTION_KEYWORDS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (3, ("выручк", "прибыл", "оборот", "млрд", "млн руб", "сотрудник", "численност", "штат")),
    (1, ("производ", "продук", "услуг", "ассортимент", "бренд", "линейк", "поставля", "выпуска")),
    (2, ("рынок", "рынке", "клиент", "дистриб", "экспорт", "регион", "город", "росси", "завод", "филиал")),
    (5, ("сайт", "cms", "битрикс", "1с", "erp", "crm", "цифров", "it-", "ит-", "tadviser")),
    (6, ("телефон", "e-mail", "email", "почта", "директор", "контакт", "@")),
)


def _clean_snippet(hit: dict, limit: int = 240) -> str:
    snip = (hit.get("snippet") or hit.get("description") or "").strip().replace("\n", " ")
    if len(snip) > limit:
        snip = snip[:limit] + "…"
    return snip


def _classify_hits(hits: list[dict]) -> dict[int, list[str]]:
    """Раскладывает факты из сниппетов по разделам досье."""
    buckets: dict[int, list[str]] = {}
    for i, h in enumerate(hits[:12], 1):
        title = (h.get("title") or "").strip()
        snip = _clean_snippet(h)
        fact = f"• {snip} [{i}]" if snip else (f"• {title} [{i}]" if title else "")
        if not fact:
            continue
        blob = f"{title} {snip}".lower()
        placed = False
        for section_idx, words in _SECTION_KEYWORDS:
            if any(w in blob for w in words):
                buckets.setdefault(section_idx, []).append(fact)
                placed = True
                break
        if not placed:
            buckets.setdefault(0, []).append(fact)
    return buckets


def readable_fallback_dossier(company: str, hits: list[dict], today: str) -> str:
    """Выжимка без LLM: факты из сниппетов разложены по разделам, а не «нет данных» везде."""
    year = today[:4]
    hits = hits or []
    buckets = _classify_hits(hits)

    lines: list[str] = [
        f"Досье «{company}» на {today} — собрано из веб-поиска без LLM (факты по сниппетам).",
        "",
        _SECTION_HEADERS[0],
        f"Компания: {company}.",
    ]
    lines.extend(buckets.get(0, []) or ([] if hits else [_NO_DATA]))

    for section_idx in (1, 2, 3):
        lines.extend(["", _SECTION_HEADERS[section_idx]])
        lines.extend(buckets.get(section_idx) or [_NO_DATA])

    lines.extend(["", f"{_SECTION_HEADERS[4]} ({year})"])
    if not hits:
        lines.append("• Веб-результаты пусты — проверьте ключи Serper / Brave / Tavily.")
    else:
        for i, h in enumerate(hits[:12], 1):
            title = (h.get("title") or "без названия").strip()
            date = (h.get("date") or "").strip()
            head = f"[{i}] {title}" + (f" ({date})" if date else "")
            lines.append(head)
            snip = _clean_snippet(h)
            if snip:
                lines.append(f"    {snip}")

    for section_idx in (5, 6):
        lines.extend(["", _SECTION_HEADERS[section_idx]])
        lines.extend(buckets.get(section_idx) or [_NO_DATA])

    lines.extend(
        [
            "",
            _SECTION_HEADERS[7],
            "• Текст собран без LLM: факты не сверены между собой, цифры проверить по [N].",
            "• Для полного досье перезапустите «Исследовать» при живом Groq / Ollama.",
            "",
            _SECTION_HEADERS[8],
        ]
    )
    if not hits:
        lines.append("—")
    for i, h in enumerate(hits[:12], 1):
        url = (h.get("url") or h.get("link") or "").strip()
        title = (h.get("title") or "").strip() or url or "—"
        lines.append(f"[{i}] {title} — {url}" if url else f"[{i}] {title}")
    return "\n".join(lines)


def fallback_dossier_from_hits(company: str, hits: list[dict], today: str) -> str:
    """Совместимость: старое имя → читаемый fallback."""
    return readable_fallback_dossier(company, hits, today)


def split_dossier_and_passport_json(answer: str) -> tuple[str, dict[str, Any] | None]:
    """Делит ответ LLM на текст досье и JSON-паспорт (раздел 10)."""
    text = (answer or "").strip()
    if not text:
        return "", None
    idx = text.find(PASSPORT_JSON_HEADER)
    if idx < 0:
        return text, None
    head = text[:idx].rstrip()
    match = re.search(r"\{[\s\S]*\}", text[idx:])
    parsed: Any = None
    if match:
        try:
            parsed = json.loads(match.group(0))
        except Exception as e:  # мусорный JSON от LLM — не роняем досье
            logger.warning("research_dossier JSON-паспорт не распарсен: %s", e)
            parsed = None
    return (head or text), parsed if isinstance(parsed, dict) else None


def ensure_nonempty_summary(
    summary: str,
    *,
    company: str,
    hits: list[dict] | None = None,
    today: str,
) -> str:
    """Гарантия: в карточку никогда не уходит пустая или «ошибочная» выжимка."""
    text = (summary or "").strip()
    if text and not is_error_summary(text):
        return text
    return readable_fallback_dossier(company, hits or [], today)


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
                max_tokens=3200,
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
