"""
Веб-поиск для SmartCRM: Serper + Brave + Tavily параллельно.
Умные запросы под каждого агента, дедупликация, фильтр даты,
LLM-ранжирование, 24h кэш.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ── Кэш (in-memory, TTL в секундах) ─────────────────────────────────────────
_cache: dict[str, dict[str, Any]] = {}  # key → {ts, results}


def _cache_key(company: str, agent: str) -> str:
    return hashlib.md5(f"{company.lower().strip()}:{agent}".encode()).hexdigest()


def _cache_get(key: str, ttl_h: float) -> list[dict] | None:
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > ttl_h * 3600:
        del _cache[key]
        return None
    return entry["results"]


def _cache_set(key: str, results: list[dict]) -> None:
    _cache[key] = {"ts": time.time(), "results": results}


def cache_clear() -> int:
    n = len(_cache)
    _cache.clear()
    return n


def cache_list() -> list[dict]:
    now = time.time()
    out = []
    for k, v in _cache.items():
        age_min = round((now - v["ts"]) / 60)
        out.append({"key": k, "age_min": age_min, "count": len(v["results"])})
    return out


# ── Конфиг ───────────────────────────────────────────────────────────────────
_DEFAULT_CONFIG: dict[str, Any] = {
    "providers": {
        "serper": {"enabled": True, "weight": 1.0, "max_results": 10},
        "brave":  {"enabled": True, "weight": 0.8, "max_results": 8},
        "tavily": {"enabled": True, "weight": 1.2, "max_results": 5},
    },
    "reranking":          {"enabled": True,  "top_k": 7},
    "date_filter_months": 24,
    "cache_ttl_hours":    24,
    "query_templates": {
        "analyst": [
            "{company} CRM продажи автоматизация",
            "{company} выручка финансы рост 2024 2025",
            "{company} отдел продаж менеджеры клиенты",
        ],
        "economist": [
            "{company} бюджет инвестиции сделки финансы",
            "{company} финансовый отчет выручка прибыль",
            "{company} тендер госзакупки контракты",
        ],
        "marketer": [
            "{company} новости 2024 2025",
            "{company} маркетинг конкуренты партнеры клиенты",
            "{company} отраслевые события выставки",
        ],
        "tech_specialist": [
            "{company} IT стек технологии разработка",
            "{company} вакансии программист разработчик",
            "{company} интеграция API автоматизация",
        ],
        "default": [
            "{company} официальный сайт контакты",
            "{company} новости 2024 2025",
        ],
    },
}

_CONFIG_PATH: str | None = None


def _config_path() -> str:
    global _CONFIG_PATH
    if _CONFIG_PATH:
        return _CONFIG_PATH
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base, "data", "search_config.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    _CONFIG_PATH = p
    return p


def load_config() -> dict[str, Any]:
    try:
        p = _config_path()
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                saved = json.load(f)
            # Мерж с дефолтом чтобы новые поля появлялись автоматически
            cfg = json.loads(json.dumps(_DEFAULT_CONFIG))
            _deep_merge(cfg, saved)
            return cfg
    except Exception as e:
        logger.warning("search_config: не удалось загрузить: %s", e)
    return json.loads(json.dumps(_DEFAULT_CONFIG))


def save_config(cfg: dict[str, Any]) -> None:
    with open(_config_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ── Провайдеры ────────────────────────────────────────────────────────────────

async def _search_serper(query: str, max_results: int) -> list[dict]:
    key = os.getenv("SERPER_API_KEY", "")
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": query, "num": max_results, "gl": "ru", "hl": "ru"},
            )
            r.raise_for_status()
            data = r.json()
        results = []
        for item in data.get("organic", [])[:max_results]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url":     item.get("link", ""),
                "date":    item.get("date", ""),
                "source":  "serper",
            })
        # Новости
        for item in data.get("news", [])[:3]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url":     item.get("link", ""),
                "date":    item.get("date", ""),
                "source":  "serper_news",
            })
        return results
    except Exception as e:
        logger.warning("Serper ошибка: %s", e)
        return []


async def _search_brave(query: str, max_results: int) -> list[dict]:
    key = os.getenv("BRAVE_API_KEY", "")
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "X-Subscription-Token": key},
                params={"q": query, "count": max_results, "search_lang": "ru", "country": "ru"},
            )
            r.raise_for_status()
            data = r.json()
        results = []
        for item in (data.get("web", {}).get("results") or [])[:max_results]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("description", ""),
                "url":     item.get("url", ""),
                "date":    item.get("page_age", ""),
                "source":  "brave",
            })
        return results
    except Exception as e:
        logger.warning("Brave ошибка: %s", e)
        return []


async def _search_tavily(query: str, max_results: int) -> list[dict]:
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": False,
                },
            )
            r.raise_for_status()
            data = r.json()
        results = []
        # Если есть AI-ответ — добавляем как первый результат
        answer = (data.get("answer") or "").strip()
        if answer:
            results.append({
                "title":   f"AI-ответ по запросу: {query}",
                "snippet": answer[:800],
                "url":     "",
                "date":    "",
                "source":  "tavily_answer",
            })
        for item in (data.get("results") or [])[:max_results]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("content", "")[:600],
                "url":     item.get("url", ""),
                "date":    item.get("published_date", ""),
                "source":  "tavily",
            })
        return results
    except Exception as e:
        logger.warning("Tavily ошибка: %s", e)
        return []


# ── Постобработка ─────────────────────────────────────────────────────────────

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return url[:30]


def _deduplicate(results: list[dict]) -> list[dict]:
    """Убирает дубли по домену + первым 80 символам сниппета."""
    seen_domains: dict[str, int] = {}
    seen_snippets: set[str] = set()
    out = []
    for r in results:
        domain = _domain(r.get("url", ""))
        snippet_key = r.get("snippet", "")[:80].lower().strip()
        # Не больше 2 результатов с одного домена
        if domain and seen_domains.get(domain, 0) >= 2:
            continue
        if snippet_key and snippet_key in seen_snippets:
            continue
        if domain:
            seen_domains[domain] = seen_domains.get(domain, 0) + 1
        if snippet_key:
            seen_snippets.add(snippet_key)
        out.append(r)
    return out


def _filter_by_date(results: list[dict], months: int) -> list[dict]:
    """Убирает результаты старше N месяцев (если дата известна)."""
    if months <= 0:
        return results
    now = datetime.now(timezone.utc)
    out = []
    for r in results:
        date_str = r.get("date", "")
        if not date_str:
            out.append(r)  # нет даты — оставляем
            continue
        # Пробуем распарсить год
        years = re.findall(r"20\d{2}", date_str)
        if years:
            year = int(years[-1])
            if now.year - year > months // 12 + 1:
                continue
        out.append(r)
    return out


async def _rerank_with_llm(
    results: list[dict],
    company: str,
    agent: str,
    top_k: int,
) -> list[dict]:
    """LLM выбирает топ-K самых релевантных результатов."""
    if len(results) <= top_k:
        return results
    try:
        from core.llm import chat
        numbered = []
        for i, r in enumerate(results):
            numbered.append(
                f"[{i+1}] {r.get('title','')}\n{r.get('snippet','')[:200]}"
            )
        block = "\n\n".join(numbered)
        prompt = (
            f"Ты помогаешь CRM-агенту '{agent}' анализировать компанию '{company}'.\n"
            f"Из {len(results)} результатов поиска выбери номера {top_k} самых полезных "
            f"для B2B CRM-анализа (финансы, контакты, новости, технологии, боли).\n\n"
            f"{block}\n\n"
            f"Ответь строго JSON-массивом номеров, например: [1,3,5,7,9]"
        )
        raw = await chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
            json_mode=False,
        )
        nums = [int(x) for x in re.findall(r"\d+", raw) if 1 <= int(x) <= len(results)]
        if nums:
            seen = set()
            ranked = []
            for n in nums[:top_k]:
                if n not in seen:
                    ranked.append(results[n - 1])
                    seen.add(n)
            # Добираем оставшиеся если нужно
            for i, r in enumerate(results):
                if len(ranked) >= top_k:
                    break
                if (i + 1) not in seen:
                    ranked.append(r)
            return ranked
    except Exception as e:
        logger.warning("Reranking ошибка: %s", e)
    return results[:top_k]


def _format_results(results: list[dict]) -> str:
    """Форматирует результаты в чистый блок фактов для LLM-промпта."""
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        title   = r.get("title", "").strip()
        snippet = r.get("snippet", "").strip()
        url     = r.get("url", "").strip()
        date    = r.get("date", "").strip()
        src     = r.get("source", "").strip()

        parts = []
        if title:
            parts.append(f"**{title}**")
        if snippet:
            parts.append(snippet)
        meta = []
        if date:
            meta.append(date)
        if src:
            meta.append(src)
        if url:
            meta.append(url)
        if meta:
            parts.append(f"({' · '.join(meta)})")
        lines.append(f"[{i}] " + " — ".join(parts))
    return "\n\n".join(lines)


# ── Главная функция ───────────────────────────────────────────────────────────

async def search_company(
    company: str,
    agent: str = "default",
    industry: str = "",
    extra_context: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """
    Полный цикл поиска по компании для агента.
    Возвращает: {formatted_block, raw_results, cached, providers_used}
    """
    cfg = load_config()
    ttl_h: float = cfg.get("cache_ttl_hours", 24)
    providers_cfg: dict = cfg.get("providers", {})
    rerank_cfg: dict = cfg.get("reranking", {})
    date_months: int = cfg.get("date_filter_months", 24)

    # Кэш
    ckey = _cache_key(company + industry, agent)
    if not force:
        cached = _cache_get(ckey, ttl_h)
        if cached is not None:
            return {
                "formatted_block": _format_results(cached),
                "raw_results": cached,
                "cached": True,
                "providers_used": [],
            }

    # Генерируем запросы для агента
    templates = cfg.get("query_templates", {})
    agent_templates = templates.get(agent) or templates.get("default") or ["{company}"]
    queries = []
    ctx_suffix = f" {industry}" if industry else ""
    ctx_suffix += f" {extra_context}" if extra_context else ""
    for tpl in agent_templates:
        q = tpl.replace("{company}", company) + ctx_suffix
        queries.append(q.strip())

    # Параллельный сбор от всех провайдеров
    all_raw: list[dict] = []
    providers_used: list[str] = []
    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []

    for provider, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", True):
            continue
        max_r = pcfg.get("max_results", 8)
        # Для каждого запроса — отдельная корутина
        for q in queries[:2]:  # не более 2 запросов на провайдер
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, max_r)))
            elif provider == "brave":
                tasks.append(asyncio.create_task(_search_brave(q, max_r)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, max_r)))
            else:
                continue
            task_meta.append(provider)

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for provider, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                logger.warning("Провайдер %s ошибка: %s", provider, res)
                continue
            if res:
                all_raw.extend(res)
                if provider not in providers_used:
                    providers_used.append(provider)

    # Постобработка
    filtered  = _filter_by_date(all_raw, date_months)
    deduped   = _deduplicate(filtered)

    # Реранкинг
    if rerank_cfg.get("enabled", True) and len(deduped) > rerank_cfg.get("top_k", 7):
        top_k = rerank_cfg.get("top_k", 7)
        final = await _rerank_with_llm(deduped, company, agent, top_k)
    else:
        final = deduped[:rerank_cfg.get("top_k", 7)]

    # Кэшируем
    _cache_set(ckey, final)

    return {
        "formatted_block":      _format_results(final),
        "raw_results":          final,
        "cached":               False,
        "providers_used":       providers_used,
        "queries_used":         queries,
        "total_raw":            len(all_raw),
        "total_after_dedup":    len(deduped),
        "total_before_rerank":  len(deduped),
        "total_after_rerank":   len(final),
    }


# ── Свободный поиск ───────────────────────────────────────────────────────────

async def free_search(
    query: str,
    summarize: bool = True,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Произвольный запрос по всем провайдерам.
    Если summarize=True, LLM формирует единый ответ.
    """
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})

    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []

    for provider, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", True):
            continue
        mr = min(pcfg.get("max_results", 8), max_results)
        if provider == "serper":
            tasks.append(asyncio.create_task(_search_serper(query, mr)))
        elif provider == "brave":
            tasks.append(asyncio.create_task(_search_brave(query, mr)))
        elif provider == "tavily":
            tasks.append(asyncio.create_task(_search_tavily(query, mr)))
        else:
            continue
        task_meta.append(provider)

    all_raw: list[dict] = []
    providers_used: list[str] = []
    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)[:max_results]
    formatted_block = _format_results(deduped)

    answer = ""
    if summarize and deduped:
        try:
            from core.llm import chat
            prompt = (
                f"Вопрос/задача: {query}\n\n"
                f"Данные из веба:\n{formatted_block}\n\n"
                "На основе этих данных дай чёткий, структурированный ответ на русском языке. "
                "Приводи факты, цифры, источники (номер результата). "
                "Если данных недостаточно — скажи об этом."
            )
            answer = await chat(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as e:
            logger.warning("free_search summarize ошибка: %s", e)
            answer = ""

    return {
        "answer":          answer,
        "formatted_block": formatted_block,
        "raw_results":     deduped,
        "providers_used":  providers_used,
    }


# ── Проспектинг ───────────────────────────────────────────────────────────────

async def prospect_companies(
    icp: str,
    industry: str = "",
    city: str = "",
    count: int = 10,
) -> dict[str, Any]:
    """
    По описанию ICP генерирует поисковые запросы,
    находит потенциальные компании и возвращает список с базовым скором.
    """
    from core.llm import chat

    # Генерируем поисковые запросы под ICP
    geo = f" {city}" if city else ""
    ind = f" в сфере {industry}" if industry else ""
    try:
        raw_queries = await chat(
            [{
                "role": "user",
                "content": (
                    f"Тебе нужно найти потенциальных B2B-клиентов{ind}{geo}.\n"
                    f"Описание идеального клиента (ICP): {icp}\n\n"
                    f"Сгенерируй ровно 3 поисковых запроса в Google для поиска таких компаний. "
                    "Запросы должны находить конкретные компании, а не статьи.\n"
                    "Ответь строго JSON-массивом строк, например: [\"запрос 1\",\"запрос 2\",\"запрос 3\"]"
                ),
            }],
            temperature=0.4,
            max_tokens=200,
            json_mode=False,
        )
        queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries) if len(q) > 5][:3]
    except Exception:
        queries = []

    if not queries:
        queries = [
            f"компании{ind}{geo} {icp[:60]}",
            f"B2B клиенты{ind}{geo} список",
        ]

    # Поиск по каждому запросу
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []
    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if not pcfg.get("enabled", True):
                continue
            mr = min(pcfg.get("max_results", 8), 8)
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            else:
                continue
            task_meta.append(provider)

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)

    # LLM извлекает компании из результатов и базово скорит
    formatted = _format_results(deduped[:20])
    companies: list[dict] = []
    try:
        raw_companies = await chat(
            [{
                "role": "user",
                "content": (
                    f"Из результатов поиска выяви конкретные компании{ind}{geo}, "
                    f"которые подходят под ICP: {icp}\n\n"
                    f"Результаты поиска:\n{formatted}\n\n"
                    f"Верни JSON-массив объектов (до {count} штук):\n"
                    '[{"name":"Название ООО","snippet":"краткое описание","url":"https://...","fit_score":75,"fit_reason":"почему подходит"}]\n'
                    "fit_score от 0 до 100. Если компания не подходит — не включай."
                ),
            }],
            temperature=0.2,
            max_tokens=1500,
            json_mode=False,
        )
        # Парсим JSON из ответа
        match = re.search(r"\[[\s\S]*\]", raw_companies)
        if match:
            companies = json.loads(match.group(0))
            companies = sorted(companies, key=lambda x: x.get("fit_score", 0), reverse=True)[:count]
    except Exception as e:
        logger.warning("prospect_companies parse ошибка: %s", e)

    return {
        "companies":      companies,
        "queries_used":   queries,
        "providers_used": providers_used,
        "raw_results":    deduped,
    }


# ── Обогащение лида ───────────────────────────────────────────────────────────

_ENRICHABLE_FIELDS = {
    "phone":        "контактный телефон компании",
    "email":        "контактный email компании",
    "website":      "официальный сайт компании",
    "address":      "юридический или фактический адрес офиса",
    "employees":    "количество сотрудников",
    "revenue":      "годовая выручка или оборот",
    "description":  "краткое описание деятельности компании",
    "linkedin":     "страница компании в LinkedIn",
    "decision_maker": "имя и должность ЛПР / CEO",
}


async def enrich_lead(lead: dict) -> dict[str, Any]:
    """
    Определяет пустые поля лида, ищет данные в вебе и возвращает заполненные значения.
    lead: словарь с полями компании (company, phone, email, website, ...)
    """
    company = (lead.get("company") or lead.get("name") or "").strip()
    if not company:
        return {"enriched": {}, "raw_results": [], "missing_fields": []}

    industry = lead.get("industry", "")

    # Определяем какие поля нужно обогатить
    missing: list[str] = []
    for field, desc in _ENRICHABLE_FIELDS.items():
        val = lead.get(field)
        if not val or str(val).strip() in ("", "null", "None", "0", "-"):
            missing.append(field)

    if not missing:
        return {"enriched": {}, "raw_results": [], "missing_fields": []}

    # Генерируем целевые запросы под каждое поле
    queries: list[tuple[str, str]] = []  # (query, field)
    for field in missing[:5]:  # не более 5 полей
        desc = _ENRICHABLE_FIELDS[field]
        q = f"{company} {desc}"
        if industry:
            q += f" {industry}"
        queries.append((q, field))

    # Общий поиск по компании
    queries.append((f"{company} официальный сайт контакты реквизиты", "general"))

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    tasks: list[asyncio.Task] = []
    task_meta: list[tuple[str, str]] = []
    for q, field in queries:
        for provider, pcfg in providers_cfg.items():
            if not pcfg.get("enabled", True):
                continue
            mr = 5
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            else:
                continue
            task_meta.append((provider, field))

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for (prov, _field), res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)
    formatted = _format_results(deduped[:20])

    # LLM извлекает значения для пустых полей
    enriched: dict[str, str] = {}
    try:
        from core.llm import chat
        missing_desc = ", ".join(f"{f} ({_ENRICHABLE_FIELDS[f]})" for f in missing[:5])
        raw_enriched = await chat(
            [{
                "role": "user",
                "content": (
                    f"Из результатов поиска извлеки данные о компании '{company}'.\n"
                    f"Нужно найти: {missing_desc}\n\n"
                    f"Результаты:\n{formatted}\n\n"
                    "Верни строго JSON-объект с найденными полями, например:\n"
                    '{"phone":"+7 495 ...", "website":"https://...", "employees":"500"}\n'
                    "Включай только поля, для которых нашёл конкретную информацию. "
                    "Не выдумывай. Если не нашёл — не включай поле."
                ),
            }],
            temperature=0.1,
            max_tokens=400,
            json_mode=False,
        )
        match = re.search(r"\{[\s\S]*\}", raw_enriched)
        if match:
            enriched = json.loads(match.group(0))
    except Exception as e:
        logger.warning("enrich_lead parse ошибка: %s", e)

    return {
        "enriched":       enriched,
        "missing_fields": missing,
        "raw_results":    deduped,
        "providers_used": providers_used,
    }


# ── Поиск для RAG ─────────────────────────────────────────────────────────────

async def search_for_rag(
    query: str,
    content_type: str = "any",
) -> dict[str, Any]:
    """
    Ищет статьи, документы, PDF для пополнения RAG-базы.
    content_type: 'any' | 'pdf' | 'article' | 'docs'
    Возвращает результаты с preview для ручного одобрения.
    """
    # Модифицируем запрос под тип контента
    type_suffix = {
        "pdf":     " filetype:pdf",
        "article": " статья обзор",
        "docs":    " документация руководство",
    }.get(content_type, "")

    search_query = query + type_suffix

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []
    for provider, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", True):
            continue
        mr = pcfg.get("max_results", 8)
        if provider == "serper":
            tasks.append(asyncio.create_task(_search_serper(search_query, mr)))
        elif provider == "brave":
            tasks.append(asyncio.create_task(_search_brave(search_query, mr)))
        elif provider == "tavily":
            tasks.append(asyncio.create_task(_search_tavily(search_query, mr)))
        else:
            continue
        task_meta.append(provider)

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)

    # Помечаем PDF
    for r in deduped:
        url = r.get("url", "").lower()
        r["is_pdf"] = url.endswith(".pdf") or "filetype:pdf" in url or "/pdf/" in url

    return {
        "results":        deduped,
        "providers_used": providers_used,
        "query_used":     search_query,
    }


# ── Задача агента через поиск (ReAct) ─────────────────────────────────────────

async def agent_task_search(
    task: str,
    agent_id: str = "analyst",
    context: str = "",
) -> dict[str, Any]:
    """
    ReAct-паттерн: агент генерирует поисковые запросы,
    выполняет их, синтезирует финальный ответ.
    """
    from core.llm import chat

    AGENT_ROLES = {
        "analyst":        "B2B-аналитик продаж и CRM",
        "economist":      "финансовый аналитик и экономист",
        "marketer":       "маркетолог и специалист по продвижению",
        "tech_specialist": "технический специалист по IT-решениям",
        "strategist":     "стратег и бизнес-консультант",
        "default":        "бизнес-аналитик",
    }
    role = AGENT_ROLES.get(agent_id, AGENT_ROLES["default"])

    # Шаг 1: агент генерирует запросы
    ctx_block = f"\nКонтекст: {context}" if context else ""
    try:
        raw_queries = await chat(
            [{
                "role": "user",
                "content": (
                    f"Ты — {role}. Тебе нужно выполнить задачу:\n{task}{ctx_block}\n\n"
                    "Чтобы ответить точно, сгенерируй 3-5 поисковых запросов в Google. "
                    "Запросы должны быть конкретными и найти факты, цифры, примеры.\n"
                    "Ответь строго JSON-массивом: [\"запрос 1\", \"запрос 2\", ...]"
                ),
            }],
            temperature=0.3,
            max_tokens=300,
        )
        queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries)][:5]
    except Exception as e:
        logger.warning("agent_task_search генерация запросов ошибка: %s", e)
        queries = [task[:100]]

    if not queries:
        queries = [task[:100]]

    # Шаг 2: выполняем поиск по всем запросам
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    search_tasks: list[asyncio.Task] = []
    task_meta: list[str] = []
    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if not pcfg.get("enabled", True):
                continue
            mr = min(pcfg.get("max_results", 8), 6)
            if provider == "serper":
                search_tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                search_tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                search_tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            else:
                continue
            task_meta.append(provider)

    if search_tasks:
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)
    rerank_cfg = cfg.get("reranking", {})
    if rerank_cfg.get("enabled", True) and len(deduped) > 12:
        final_results = await _rerank_with_llm(deduped, task[:40], agent_id, 12)
    else:
        final_results = deduped[:15]

    formatted = _format_results(final_results)

    # Шаг 3: агент синтезирует ответ
    answer = ""
    try:
        answer = await chat(
            [{
                "role": "user",
                "content": (
                    f"Ты — {role}. Задача:\n{task}{ctx_block}\n\n"
                    f"Данные из веба:\n{formatted}\n\n"
                    "Дай развёрнутый профессиональный ответ на русском языке. "
                    "Используй конкретные факты из результатов (ссылайся на номера [N]). "
                    "Структурируй ответ: вывод, детали, рекомендации."
                ),
            }],
            temperature=0.4,
            max_tokens=1200,
        )
    except Exception as e:
        logger.warning("agent_task_search синтез ошибка: %s", e)
        answer = f"Ошибка синтеза: {e}"

    return {
        "answer":         answer,
        "queries_used":   queries,
        "raw_results":    final_results,
        "providers_used": providers_used,
        "agent_id":       agent_id,
    }
