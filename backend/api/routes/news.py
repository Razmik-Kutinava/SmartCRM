"""
News API:
  POST /api/news/search   — поиск новостей по теме + анализ 5 агентов
  GET  /api/news/headlines — актуальные заголовки технологического рынка

Источники:
  1. NewsAPI (english/global) — переводим запрос через LLM если нужно
  2. Tavily web search — умеет искать по-русски, находит свежие материалы
  3. Brave Search — ещё один бесплатный fallback
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news"])

# IT направления и продукты — контекст для агентов
IT_DIRECTIONS_CONTEXT = """
## IT направления (что анализируем у клиентов)
- ITOM/NPM — мониторинг IT-инфраструктуры и сетей
- SIEM — управление событиями безопасности, SOC
- IAM/AD — управление учётными записями и доступом
- ITSM — управление IT-сервисами (helpdesk, CMDB)
- UEM — управление конечными устройствами (endpoint management)
- BI — аналитика данных и бизнес-интеллект
- Backup/DR — резервное копирование и восстановление
- APM — мониторинг производительности приложений
- Compliance — соответствие требованиям (ФСТЭК, ФСБ, 152-ФЗ, GDPR)
- DLP — предотвращение утечек данных
- PAM — управление привилегированным доступом
- VPN/ZTNA — защита удалённого доступа

## Продукты которые мы продаём
- ManageEngine — комплекс IT-управления (ITOM, ITSM, IAM, UEM, BI, Backup, PAM, DLP, SIEM)
- Positive Technologies — кибербезопасность (SIEM MaxPatrol, VM, PT NAD, PT Sandbox, PT AF)

## Задача агентов по новостям рынка
Найти сигналы: какие IT-проблемы актуальны → какие продукты нужны → кому продавать.
"""


class NewsSearchRequest(BaseModel):
    query: str
    language: str = "any"       # ru / en / any (без фильтра)
    limit: int = 20
    agent_limit: int = 30
    run_agents: bool = True


# ── Утилиты ────────────────────────────────────────────────────────────────────

def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r'[а-яёА-ЯЁ]', text))


async def _translate_query(query: str) -> str:
    """
    Переводит русский запрос на короткие английские ключевые слова для NewsAPI.
    Сначала пробует словарный маппинг (быстро, без LLM),
    затем LLM как fallback.
    """
    if not _has_cyrillic(query):
        return query

    # Словарный маппинг частых IT-терминов
    DICT_MAP = {
        "мониторинг инфраструктуры": "infrastructure monitoring",
        "мониторинг": "monitoring",
        "кибербезопасность": "cybersecurity",
        "кибератака": "cyberattack",
        "утечка данных": "data breach",
        "утечка персональных данных": "personal data breach GDPR",
        "управление доступом": "identity access management",
        "управление учётными записями": "identity management",
        "резервное копирование": "backup disaster recovery",
        "резервное": "backup",
        "соответствие требованиям": "compliance",
        "предотвращение утечек": "data loss prevention DLP",
        "привилегированный доступ": "privileged access management PAM",
        "импортозамещение": "import substitution Russia IT",
        "импортозамещение it": "Russian IT import substitution",
    }

    q_low = query.lower().strip()
    for ru, en in DICT_MAP.items():
        q_low = q_low.replace(ru, en)

    # Если удалось перевести ключевые части — используем результат
    if not _has_cyrillic(q_low):
        logger.info("NewsAPI query (dict) translated: %r → %r", query, q_low)
        return q_low.strip()

    # Fallback: LLM
    try:
        from core.llm import chat
        raw = await chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You translate Russian IT search queries into short English keywords for a news API. "
                        "Output ONLY 2-4 English keywords, no explanations, no 'Russian' word, no punctuation."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=30,
            json_mode=False,
        )
        en = raw.strip().strip('"').strip("'").split('\n')[0]
        logger.info("NewsAPI query (LLM) translated: %r → %r", query, en)
        return en if en and not _has_cyrillic(en) else query
    except Exception as e:
        logger.warning("Query translation failed: %s", e)
        return query


def _tavily_to_article(item: dict) -> dict:
    """Конвертирует результат Tavily в формат article для фронтенда."""
    raw_date = item.get("date") or item.get("published_date") or ""
    age_days = None
    if raw_date:
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).days
        except Exception:
            pass
    return {
        "title":        item.get("title", ""),
        "description":  item.get("snippet") or item.get("content", "")[:300],
        "content":      item.get("snippet", "")[:500],
        "url":          item.get("url", ""),
        "image":        "",
        "source":       item.get("source", "web"),
        "author":       "",
        "published_at": raw_date,
        "age_days":     age_days,
        "is_fresh":     age_days is not None and age_days <= 7,
        "_provider":    "tavily",
    }


async def _search_tavily_news(query: str, limit: int = 15) -> list[dict]:
    """Поиск через Tavily (умеет русский язык и свежие результаты)."""
    import os
    import httpx
    key = os.getenv("TAVILY_API_KEY", "")
    if not key or key == "your_tavily_api_key":
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": key,
                    "query": query,
                    "max_results": min(limit, 20),
                    "search_depth": "advanced",
                    "topic": "news",
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results") or []
            logger.info("Tavily news search q=%r → %d results", query, len(results))
            from core.stats import track_api
            track_api("tavily")
            return [_tavily_to_article(item) for item in results if item.get("title")]
    except Exception as e:
        logger.warning("Tavily news search failed: %s", e)
        return []


async def _search_brave_news(query: str, limit: int = 10) -> list[dict]:
    """Поиск через Brave Search API."""
    import os
    import httpx
    key = os.getenv("BRAVE_API_KEY", "")
    if not key or key == "your_brave_api_key":
        return []
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/news/search",
                params={"q": query, "count": min(limit, 20), "freshness": "pw"},
                headers={"Accept": "application/json", "X-Subscription-Token": key},
            )
            if r.status_code != 200:
                logger.warning("Brave news %r → %s", query, r.status_code)
                return []
            data = r.json()
            items = data.get("results") or []
            logger.info("Brave news search q=%r → %d results", query, len(items))
            from core.stats import track_api
            track_api("brave")
            out = []
            for item in items:
                pub = item.get("age") or ""
                out.append({
                    "title":        item.get("title", ""),
                    "description":  item.get("description", "")[:300],
                    "content":      item.get("description", "")[:500],
                    "url":          item.get("url", ""),
                    "image":        (item.get("thumbnail") or {}).get("src", ""),
                    "source":       (item.get("meta_url") or {}).get("hostname", "web"),
                    "author":       "",
                    "published_at": pub,
                    "age_days":     None,
                    "is_fresh":     True,
                    "_provider":    "brave",
                })
            return out
    except Exception as e:
        logger.warning("Brave news search failed: %s", e)
        return []


def _dedup_articles(articles: list[dict]) -> list[dict]:
    """Дедупликация по URL."""
    seen: set[str] = set()
    out = []
    for a in articles:
        url = a.get("url", "")
        key = url.rstrip("/").lower() if url else id(a)
        if key and key not in seen:
            seen.add(key)
            out.append(a)
    return out


# ── Эндпоинты ──────────────────────────────────────────────────────────────────

@router.post("/search")
async def search_news(body: NewsSearchRequest):
    """
    Мультисорс поиск новостей:
    1. Tavily (русский + English, свежие)
    2. NewsAPI (English, переводим запрос если нужно)
    3. Brave Search (если есть ключ)
    4. 5 AI-агентов анализируют рынок
    """
    if not body.query.strip():
        raise HTTPException(400, "Укажи поисковый запрос")

    from leadgen.modules.newsapi import (
        fetch_news_topic, articles_to_agent_context, _available as news_available,
    )

    q = body.query.strip()

    # Шаг 1: переводим запрос (быстро — словарь, потом LLM если нужно)
    en_query = await _translate_query(q)

    # Шаг 2: все три источника параллельно
    newsapi_articles, tavily_articles, brave_articles = await asyncio.gather(
        fetch_news_topic(en_query, language="en", limit=body.limit) if news_available()
            else asyncio.sleep(0, result=[]),
        _search_tavily_news(q, limit=body.limit),
        _search_brave_news(q, limit=10),
    )

    # Объединяем: NewsAPI первым (приоритет), затем Tavily, Brave
    all_articles = _dedup_articles(
        list(newsapi_articles) + list(tavily_articles) + list(brave_articles)
    )

    logger.info(
        "News search q=%r: tavily=%d brave=%d newsapi=%d total=%d",
        q, len(tavily_articles), len(brave_articles), len(newsapi_articles), len(all_articles),
    )

    # Агенты анализируют объединённый пул
    agent_results: dict = {}
    if body.run_agents and all_articles:
        # Для агентов — дополнительно берём исторические из NewsAPI (relevancy sort)
        hist_articles = await fetch_news_topic(en_query, language="en", limit=body.agent_limit, sort_by="relevancy") if news_available() else []
        agent_pool = _dedup_articles(all_articles + list(hist_articles))
        agent_context = articles_to_agent_context(agent_pool[:body.agent_limit], label="НОВОСТИ РЫНКА")
        agent_results = await _run_news_agents(q, agent_context)
    elif body.run_agents:
        # Нет статей — агенты работают только с запросом
        agent_context = f"Поисковый запрос: {q}\n\nСтатьи не найдены в доступных источниках."
        agent_results = await _run_news_agents(q, agent_context)

    return {
        "status":             "ok",
        "query":              q,
        "query_en":           en_query if en_query != q else "",
        "articles":           all_articles[:body.limit],
        "total_fresh":        len(all_articles),
        "sources_used":       {
            "tavily":  len(tavily_articles),
            "brave":   len(brave_articles),
            "newsapi": len(newsapi_articles),
        },
        "agent_article_count": min(len(all_articles), body.agent_limit),
        "agents":             agent_results,
    }


@router.get("/headlines")
async def get_headlines(category: str = "technology", country: str = "ru", limit: int = 15):
    """Актуальные заголовки по категории."""
    from leadgen.modules.newsapi import fetch_top_headlines, _available as news_available
    if not news_available():
        raise HTTPException(503, "NEWS_API_KEY не задан")
    articles = await fetch_top_headlines(category=category, country=country, limit=limit)
    return {"status": "ok", "articles": articles, "category": category}


# ── Агенты ────────────────────────────────────────────────────────────────────

async def _run_news_agents(query: str, news_context: str) -> dict:
    """Запускает 5 агентов анализа новостей рынка."""
    from core.llm import chat

    base_context = f"""Тема поиска: «{query}»

{IT_DIRECTIONS_CONTEXT}

{news_context}
"""

    # Общая инструкция для всех агентов
    JSON_RULE = (
        "\nВАЖНО: все поля-массивы должны содержать ТОЛЬКО строки (string), "
        "не объекты и не вложенные структуры. score — целое число от 0 до 100."
    )

    agent_configs = {
        "market_analyst": {
            "system": (
                "Ты — аналитик IT-рынка. Изучи новости и сделай выводы о трендах.\n"
                "ФОРМАТ — строго JSON (все массивы = строки!):\n"
                '{"summary": "текст", "key_trends": ["строка1","строка2"], '
                '"market_signals": ["строка"], "growth_areas": ["строка"], '
                '"decline_areas": ["строка"], "score": 75}'
                + JSON_RULE
            ),
            "focus": "тренды рынка, рост/падение сегментов, ключевые сигналы для продаж",
        },
        "tech_expert": {
            "system": (
                "Ты — технический эксперт IT. Определи какие технологии и решения в тренде.\n"
                "ФОРМАТ — строго JSON (все массивы = строки!):\n"
                '{"summary": "текст", "hot_technologies": ["SIEM","ITOM"], '
                '"dying_technologies": ["строка"], "compliance_pressure": ["строка"], '
                '"recommended_solutions": ["ManageEngine OpManager","PT MaxPatrol"], "score": 75}'
                + JSON_RULE
            ),
            "focus": "технологические тренды, какие продукты актуальны (ManageEngine, Positive Tech)",
        },
        "sales_strategist": {
            "system": (
                "Ты — директор по продажам IT. Найди конкретные возможности для продаж.\n"
                "ФОРМАТ — строго JSON (все массивы = строки!):\n"
                '{"summary": "текст", "sales_opportunities": ["возможность1","возможность2"], '
                '"target_segments": ["сегмент1"], "urgency_triggers": ["триггер1"], '
                '"best_message": "конкретная фраза для холодного письма", "score": 75}'
                + JSON_RULE
            ),
            "focus": "конкретные возможности продаж ManageEngine и Positive Technologies, целевые сегменты",
        },
        "risk_analyst": {
            "system": (
                "Ты — аналитик рисков IT-безопасности. Оцени угрозы из новостей.\n"
                "ФОРМАТ — строго JSON (все массивы = строки!):\n"
                '{"summary": "текст", "threats": ["угроза1","угроза2"], '
                '"incidents": ["инцидент1"], "regulatory_changes": ["изменение1"], '
                '"action_items": ["действие1","действие2"], "score": 75}'
                + JSON_RULE
            ),
            "focus": "киберугрозы, инциденты, регуляторные изменения, что нужно срочно закрыть",
        },
        "content_creator": {
            "system": (
                "Ты — контент-маркетолог B2B IT. Предложи идеи контента на основе новостей.\n"
                "ФОРМАТ — строго JSON (все массивы = строки!):\n"
                '{"summary": "текст", "article_ideas": ["идея1","идея2"], '
                '"email_subjects": ["тема1","тема2"], "linkedin_hooks": ["крючок1"], '
                '"webinar_topics": ["тема вебинара1"], "score": 75}'
                + JSON_RULE
            ),
            "focus": "идеи контента для продвижения ManageEngine и Positive Technologies",
        },
    }

    import json as _json
    import re as _re

    async def run_one(agent_id: str, cfg: dict) -> tuple[str, dict]:
        try:
            raw = await chat(
                [
                    {"role": "system", "content": cfg["system"]},
                    {
                        "role": "user",
                        "content": (
                            f"Анализируй новости рынка. Акцент: {cfg['focus']}.\n\n"
                            f"{base_context}"
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=900,
                json_mode=True,
            )
            try:
                parsed = _json.loads(raw)
            except Exception:
                m = _re.search(r"\{.*\}", raw, _re.DOTALL)
                parsed = _json.loads(m.group()) if m else {"summary": raw[:300], "score": 55}
            # Нормализуем: все поля-массивы должны содержать строки, не объекты
            _STR_ARRAY_KEYS = {
                "recommended_solutions", "hot_technologies", "dying_technologies",
                "sales_opportunities", "target_segments", "urgency_triggers",
                "threats", "incidents", "action_items", "regulatory_changes",
                "article_ideas", "email_subjects", "linkedin_hooks", "webinar_topics",
                "key_trends", "market_signals", "growth_areas", "decline_areas",
                "compliance_pressure",
            }
            for key in _STR_ARRAY_KEYS:
                if key in parsed and isinstance(parsed[key], list):
                    normalized = []
                    for v in parsed[key]:
                        if isinstance(v, str):
                            normalized.append(v)
                        elif isinstance(v, dict):
                            # Пробуем типичные строковые ключи
                            s = (v.get("name") or v.get("title") or v.get("text")
                                 or v.get("product") or v.get("opportunity") or "")
                            if not s:
                                # Берём первые два значения и склеиваем
                                vals = [str(x) for x in v.values() if x and str(x) != "None"][:2]
                                s = " — ".join(vals) if vals else str(v)
                            normalized.append(s)
                        else:
                            normalized.append(str(v))
                    parsed[key] = normalized
            return agent_id, parsed
        except Exception as e:
            logger.warning("News agent %s failed: %s", agent_id, e)
            return agent_id, {"error": str(e), "summary": f"Ошибка: {e}", "score": 0}

    # Запускаем в 2 батча (3 + 2) чтобы не перегружать LLM rate limit
    items = list(agent_configs.items())
    batch1 = await asyncio.gather(*[run_one(aid, cfg) for aid, cfg in items[:3]])
    await asyncio.sleep(0.5)
    batch2 = await asyncio.gather(*[run_one(aid, cfg) for aid, cfg in items[3:]])
    return dict(list(batch1) + list(batch2))
