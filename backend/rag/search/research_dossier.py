"""Досье веб-исследования: LLM-синтез (Groq→Ollama) + fallback для агентов."""
from __future__ import annotations

import json
import logging
import os
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


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def is_error_summary(text: str) -> bool:
    s = (text or "").strip().lower()
    if not s:
        return True
    if (
        s.startswith("ошибка синтеза")
        or s.startswith("ошибка исследования")
        or "connection attempts failed" in s
        or "all connection attempts failed" in s
    ):
        return True
    # Отказы / «переводчик» вместо досье (типично для tiny-моделей)
    refuse = (
        "извините, но я не могу",
        "i cannot",
        "i can't",
        "as an ai",
        "как языковая модель",
        "предоставьте текст",
        "не могу перевести",
    )
    return any(x in s for x in refuse)


def is_usable_dossier(text: str) -> bool:
    """Ответ LLM годится как досье: есть структура разделов, не отказ."""
    if is_error_summary(text):
        return False
    t = text or ""
    # Минимум два заголовка разделов — иначе это не досье
    hits = sum(1 for h in _SECTION_HEADERS if h in t)
    if hits >= 2:
        return True
    # Модели иногда пишут без «## » — считаем нумерованные/текстовые маркеры
    soft = sum(
        1
        for m in (
            "профиль компании",
            "продукты",
            "источники",
            "контакты",
            "масштаб",
            "новости",
        )
        if m in t.lower()
    )
    return soft >= 3 and len(t) >= 400


def build_synthesis_prompt(
    *,
    company: str,
    today: str,
    year: str,
    context: str,
    formatted_hits: str,
    page_texts: str = "",
    pages_limit: int | None = None,
) -> str:
    limit = pages_limit if pages_limit is not None else _env_int("RESEARCH_PAGES_CHARS", 6000)
    pages_block = ""
    if page_texts.strip():
        pages_block = f"\n\nТексты страниц (фрагменты):\n{page_texts[:limit]}\n"

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
        "игнорируй посольства/чужие страны без связи с компанией.\n"
        "Формат: заголовки разделов — ровно как выше, с «## » и номером. "
        f"Раздел «{PASSPORT_JSON_HEADER}» обязателен и идёт последним.\n\n"
        f"Источники поиска:\n{formatted_hits}"
        f"{pages_block}"
    )


def estimate_tokens(text: str) -> int:
    """Грубая оценка токенов. Кириллица дороже латиницы — считаем консервативно.

    Точный токенайзер Groq недоступен локально; занижать нельзя (иначе 413),
    поэтому берём меньшее число символов на токен через env.
    """
    if not text:
        return 0
    chars_per_token = _env_float("LLM_CHARS_PER_TOKEN", 2.2)
    if chars_per_token <= 0:
        chars_per_token = 2.2
    return int(len(text) / chars_per_token) + 1


def groq_tpm_budget() -> int:
    """Сколько токенов за минуту можно потратить на один вызов досье.

    Free tier Groq для llama-3.1-8b-instant — 6000 TPM на организацию,
    поэтому держим запас под параллельные вызовы (генерация запросов и т.п.).
    """
    return _env_int("RESEARCH_GROQ_TPM_BUDGET", 5200)


def fit_prompt_to_token_budget(
    *,
    company: str,
    today: str,
    year: str,
    context: str,
    formatted_hits: str,
    page_texts: str = "",
    tpm_budget: int,
    max_tokens: int,
) -> str:
    """Собирает промпт досье, урезая источники под лимит `tpm_budget - max_tokens`."""
    allowed = max(tpm_budget - max_tokens, 400)
    hits = formatted_hits or ""
    pages = page_texts or ""

    def build(h: str, p: str) -> str:
        return build_synthesis_prompt(
            company=company,
            today=today,
            year=year,
            context=context,
            formatted_hits=h,
            page_texts=p,
            pages_limit=len(p) or None,
        )

    prompt = build(hits, pages)
    if estimate_tokens(prompt) <= allowed:
        return prompt

    # Сначала жертвуем текстами страниц, потом сниппетами — заголовок разделов нужен целым
    overhead = estimate_tokens(build("", ""))
    room_chars = int(max(allowed - overhead, 200) * _env_float("LLM_CHARS_PER_TOKEN", 2.2))

    hits_share = _env_float("RESEARCH_HITS_SHARE", 0.6)
    hits_chars = int(room_chars * hits_share)
    hits = hits[:hits_chars]
    pages = pages[: max(room_chars - len(hits), 0)]

    prompt = build(hits, pages)
    # Страховка от промаха оценки: дожимаем короткими шагами
    while estimate_tokens(prompt) > allowed and (hits or pages):
        if pages:
            pages = pages[: int(len(pages) * 0.8)]
        else:
            hits = hits[: int(len(hits) * 0.8)]
        prompt = build(hits, pages)
    return prompt


_RATE_LIMIT_MARKERS = ("rate_limit_exceeded", "413", "too large", "tokens per minute")


def is_rate_limit_error(err: BaseException) -> bool:
    text = f"{type(err).__name__}: {err}".lower()
    return any(m in text for m in _RATE_LIMIT_MARKERS)


def parse_requested_limit(err: BaseException) -> tuple[int | None, int | None]:
    """Достаёт `Limit N, Requested M` из ошибки Groq — чтобы урезать точно, а не наугад."""
    text = str(err)
    limit = re.search(r"Limit\s+(\d+)", text, re.IGNORECASE)
    requested = re.search(r"Requested\s+(\d+)", text, re.IGNORECASE)
    return (
        int(limit.group(1)) if limit else None,
        int(requested.group(1)) if requested else None,
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
        # Модели часто теряют «## » и пишут «**10. JSON-паспорт**» или «10. JSON-паспорт»
        soft = re.search(r"[#*\s]*10\.\s*JSON-паспорт", text, re.IGNORECASE)
        idx = soft.start() if soft else -1
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
    """Гарантия: в карточку уходит читаемое досье, не отказ/мусор LLM."""
    text = (summary or "").strip()
    if text and is_usable_dossier(text):
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

    Лимиты через env (без хардкода модели в коде):
    RESEARCH_GROQ_MAX_TOKENS, RESEARCH_OLLAMA_MAX_TOKENS,
    RESEARCH_OLLAMA_HITS_CHARS, RESEARCH_PAGES_CHARS, OLLAMA_CHAT_TIMEOUT.
    """
    import asyncio

    from core.llm import chat

    groq_tokens = _env_int("RESEARCH_GROQ_MAX_TOKENS", 2000)
    ollama_tokens = _env_int("RESEARCH_OLLAMA_MAX_TOKENS", 1600)
    ollama_hits_chars = _env_int("RESEARCH_OLLAMA_HITS_CHARS", 5000)
    pages_chars = _env_int("RESEARCH_PAGES_CHARS", 4000)
    ollama_timeout = _env_float("OLLAMA_CHAT_TIMEOUT", 180.0)
    retries = _env_int("RESEARCH_GROQ_RATE_RETRIES", 2)

    for model in ("groq", "ollama"):
        if model == "ollama":
            prompt = build_synthesis_prompt(
                company=company,
                today=today,
                year=year,
                context=context,
                formatted_hits=(formatted_hits or "")[:ollama_hits_chars],
                page_texts=(page_texts or "")[:pages_chars],
                pages_limit=pages_chars,
            )
            tokens = ollama_tokens
        else:
            tokens = groq_tokens
            budget = groq_tpm_budget()
            prompt = fit_prompt_to_token_budget(
                company=company,
                today=today,
                year=year,
                context=context,
                formatted_hits=formatted_hits,
                page_texts=page_texts,
                tpm_budget=budget,
                max_tokens=tokens,
            )

        attempt = 0
        while True:
            try:
                coro = chat(
                    [{"role": "user", "content": prompt}],
                    model=model,
                    temperature=0.3,
                    max_tokens=tokens,
                )
                if model == "ollama":
                    answer = await asyncio.wait_for(coro, timeout=ollama_timeout)
                else:
                    answer = await coro
                answer = (answer or "").strip()
                if answer and is_usable_dossier(answer):
                    logger.info("research_dossier синтез через %s (%s симв.)", model, len(answer))
                    return answer, model
                logger.warning(
                    "research_dossier %s: ответ не похож на досье (%s симв.)",
                    model,
                    len(answer or ""),
                )
                break
            except Exception as e:
                rate_limited = model == "groq" and is_rate_limit_error(e) and attempt < retries
                if not rate_limited:
                    logger.warning(
                        "research_dossier %s недоступен: %s: %s", model, type(e).__name__, e
                    )
                    break
                attempt += 1
                limit, requested = parse_requested_limit(e)
                # Groq сам сказал limit/requested — ужимаемся по этому отношению,
                # но каждая попытка обязана быть строго короче предыдущей
                if limit and requested and requested > limit:
                    ratio = min(limit / requested * 0.9, 0.85)
                else:
                    ratio = 0.7
                prev_allowed = max(budget - tokens, 400)
                tokens = max(int(tokens * 0.8), 700)
                budget = max(int(prev_allowed * ratio), 400) + tokens
                prompt = fit_prompt_to_token_budget(
                    company=company,
                    today=today,
                    year=year,
                    context=context,
                    formatted_hits=formatted_hits,
                    page_texts=page_texts,
                    tpm_budget=budget,
                    max_tokens=tokens,
                )
                logger.warning(
                    "research_dossier groq лимит TPM (limit=%s requested=%s) — попытка %s, "
                    "промпт %s симв., max_tokens=%s",
                    limit,
                    requested,
                    attempt,
                    len(prompt),
                    tokens,
                )

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
