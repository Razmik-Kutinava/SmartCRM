"""
NewsAPI — новости о компании и рынке.
API: https://newsapi.org/v2/everything
ENV: NEWS_API_KEY

Функции:
  fetch_news(company_name)      — свежие новости о компании (для пайплайна)
  fetch_news_topic(query, ...)  — поиск по теме (для вкладки "Новости рынка")
  fetch_news_historical(query)  — расширенный поиск для агентов (макс. диапазон)
  extract_triggers(articles)    — триггеры из новостей
"""
from __future__ import annotations
import logging
import os
from datetime import datetime, timedelta, timezone
import httpx

logger = logging.getLogger(__name__)

NEWSAPI_URL     = "https://newsapi.org/v2/everything"
NEWSAPI_TOP_URL = "https://newsapi.org/v2/top-headlines"
TIMEOUT         = 12.0

# Лимиты: free plan — только последние 30 дней, paid — без ограничений.
# Используем sortBy=publishedAt и не передаём "from" чтобы не нарваться на 426.
DISPLAY_AGE_DAYS  = 30   # показываем пользователю статьи до 30 дней
AGENT_AGE_DAYS    = 30   # агенты тоже видят за 30 дней (free plan ограничен)


def _key() -> str:
    return os.getenv("NEWS_API_KEY", "")


def _available() -> bool:
    return bool(_key())


# ── Новости о компании (для пайплайна анализа) ────────────────────────────────

async def fetch_news(company_name: str, limit: int = 10) -> list[dict]:
    """Получить свежие новости о компании."""
    if not _available() or not company_name:
        return []
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                NEWSAPI_URL,
                params={
                    "q": company_name,
                    "sortBy": "publishedAt",
                    "language": "ru",
                    "pageSize": min(limit, 100),
                    "apiKey": _key(),
                },
            )
            if r.status_code == 426:
                logger.info("NewsAPI: free plan — платная функция недоступна")
                return []
            r.raise_for_status()
            data = r.json()
            articles = data.get("articles", []) or []
            return [_parse_article(a) for a in articles if a.get("title")]
    except Exception as e:
        logger.warning("NewsAPI company news failed for %s: %s", company_name, e)
        return []


# ── Поиск по теме/рынку (для вкладки "Новости рынка") ────────────────────────

async def fetch_news_topic(
    query: str,
    language: str = "ru",
    limit: int = 20,
    sort_by: str = "publishedAt",
    from_date: str | None = None,
    domains: str | None = None,
) -> list[dict]:
    """
    Поиск новостей по теме (ITOM, SIEM, ManageEngine, кибербезопасность и т.д.).
    Возвращает статьи для отображения пользователю (свежие).

    Стратегия:
    1. Пробуем с указанным языком
    2. Если 0 результатов — повторяем без языкового фильтра (NewsAPI плохо индексирует ru)
    3. Если ещё 0 — пробуем с language=en
    """
    if not _available() or not query.strip():
        return []

    async def _do_request(lang: str | None) -> list[dict]:
        params: dict = {
            "q": query.strip(),
            "sortBy": sort_by,
            "pageSize": min(limit, 100),
            "apiKey": _key(),
        }
        if lang:
            params["language"] = lang
        if from_date:
            params["from"] = from_date
        if domains:
            params["domains"] = domains

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(NEWSAPI_URL, params=params)
            if r.status_code == 426:
                params.pop("from", None)
                r = await client.get(NEWSAPI_URL, params=params)
            if r.status_code != 200:
                logger.warning("NewsAPI topic search (lang=%s) %s → %s: %s",
                               lang, query, r.status_code, r.text[:300])
                return []
            data = r.json()
            total = data.get("totalResults", 0)
            logger.info("NewsAPI topic search (lang=%s) q=%r → totalResults=%s", lang, query, total)
            try:
                from core.stats import track_api
                track_api("newsapi")
            except Exception:
                pass
            articles = data.get("articles", []) or []
            return [_parse_article(a) for a in articles if a.get("title")]

    try:
        # Попытка 1: с языком пользователя
        results = await _do_request(language if language != "any" else None)
        if results:
            return results

        # Попытка 2: без языкового фильтра (самый широкий охват)
        if language and language != "any":
            logger.info("NewsAPI: 0 results for lang=%s, retrying without language filter", language)
            results = await _do_request(None)
        if results:
            return results

        # Попытка 3: english как fallback
        if language != "en":
            logger.info("NewsAPI: 0 results without filter, trying en")
            results = await _do_request("en")
        return results

    except Exception as e:
        logger.warning("NewsAPI topic search failed for %s: %s", query, e)
        return []


async def fetch_news_historical(query: str, limit: int = 30) -> list[dict]:
    """
    Исторические новости для агентов (максимальный диапазон что позволяет план).
    На free plan — это ~30 дней. На paid — до 5 лет.
    Агенты получают больше статей с контекстом, пользователю они не показываются.
    """
    return await fetch_news_topic(query, limit=limit, sort_by="relevancy")


# ── Заголовки по категории (breaking news) ────────────────────────────────────

async def fetch_top_headlines(
    category: str = "technology",
    country: str = "ru",
    limit: int = 10,
) -> list[dict]:
    """
    GET /v2/top-headlines — актуальные заголовки по категории.
    category: business | technology | science | health | entertainment | sports
    """
    if not _available():
        return []
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                NEWSAPI_TOP_URL,
                params={
                    "category": category,
                    "country": country,
                    "pageSize": min(limit, 100),
                    "apiKey": _key(),
                },
            )
            if r.status_code != 200:
                return []
            articles = r.json().get("articles", []) or []
            return [_parse_article(a) for a in articles if a.get("title")]
    except Exception as e:
        logger.warning("NewsAPI top headlines failed: %s", e)
        return []


# ── Парсер / утилиты ──────────────────────────────────────────────────────────

def _parse_article(a: dict) -> dict:
    pub = a.get("publishedAt", "")
    age_days = _calc_age_days(pub)
    return {
        "title":       a.get("title", ""),
        "description": a.get("description", "") or "",
        "content":     (a.get("content", "") or "")[:500],
        "url":         a.get("url", ""),
        "image":       a.get("urlToImage", "") or "",
        "source":      (a.get("source") or {}).get("name", ""),
        "author":      a.get("author", "") or "",
        "published_at": pub,
        "age_days":    age_days,
        "is_fresh":    age_days is not None and age_days <= 7,
    }


def _calc_age_days(pub: str) -> int | None:
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return None


def extract_triggers(articles: list[dict]) -> list[str]:
    """Выделяет ключевые триггеры из новостей."""
    triggers = []
    keywords = {
        "инвестиции": "Привлечение инвестиций",
        "раунд":      "Инвестиционный раунд",
        "найм":       "Активный найм",
        "расширение": "Расширение",
        "тендер":     "Тендер/госзакупки",
        "партнёрство":"Новое партнёрство",
        "слияние":    "Слияние/поглощение",
        "скандал":    "Репутационный риск",
        "проблемы":   "Операционные проблемы",
        "рост":       "Рост бизнеса",
        "открытие":   "Открытие нового направления",
        "атак":       "Кибератака/инцидент",
        "утечк":      "Утечка данных",
        "регулятор":  "Регуляторное давление",
        "санкци":     "Санкции/ограничения",
    }
    for a in articles:
        text = (a.get("title", "") + " " + a.get("description", "")).lower()
        for kw, label in keywords.items():
            if kw in text and label not in triggers:
                triggers.append(label)
    return triggers


def articles_to_agent_context(articles: list[dict], label: str = "НОВОСТИ") -> str:
    """Форматирует список статей в текст для промпта агента."""
    if not articles:
        return f"=== {label} ===\nНовости не найдены.\n"
    lines = [f"=== {label} ({len(articles)} ст.) ==="]
    for i, a in enumerate(articles, 1):
        age = f"{a['age_days']} дн." if a.get("age_days") is not None else "?"
        lines.append(
            f"{i}. [{a.get('source', '?')}] {a.get('title', '')} ({age})\n"
            f"   {a.get('description', '')[:150]}"
        )
    return "\n".join(lines)
