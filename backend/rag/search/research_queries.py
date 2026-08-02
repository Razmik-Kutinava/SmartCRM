"""Поисковые запросы для 🔍: каталоги по ИНН → свежие новости → профиль.

Порядок важен: сначала реестры/каталоги (Checko, list-org…), потом новости года.
"""
from __future__ import annotations

import re
from typing import Any

# Каталоги юрлиц РФ — приоритет над новостными сайтами
_CATALOG_SITES = (
    "checko.ru",
    "list-org.com",
    "rusprofile.ru",
    "sbis.ru",
    "spark-interfax.ru",
    "egrul.nalog.ru",
)


def _digits_inn(raw: Any) -> str:
    inn = re.sub(r"\D", "", str(raw or ""))
    return inn if len(inn) in (10, 12) else ""


def _dedupe_queries(queries: list[str], *, limit: int = 8) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        text = " ".join(str(q or "").split()).strip()
        if len(text) < 5:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def catalog_queries_for_inn(inn: str, company: str = "") -> list[str]:
    """Запросы в каталоги компаний по ИНН (+ имя как подстраховка)."""
    inn = _digits_inn(inn)
    if not inn:
        return []
    name = (company or "").strip()
    qs = [
        f"ИНН {inn}",
        f'ИНН {inn} компания',
        f"site:checko.ru {inn}",
        f"site:list-org.com {inn}",
        f"site:rusprofile.ru {inn}",
        f"site:sbis.ru {inn}",
    ]
    if name and name not in ("—", "-"):
        qs.append(f'"{name}" ИНН {inn}')
    return qs


def news_queries(company: str, year: str, inn: str = "") -> list[str]:
    """Свежие новости: год + слова новости/пресс."""
    name = (company or "").strip() or "компания"
    qs = [
        f'"{name}" новости {year}',
        f'"{name}" новости за {year} пресс-релиз',
        f'"{name}" {year} сделка OR контракт OR запуск',
    ]
    inn = _digits_inn(inn)
    if inn:
        qs.append(f"ИНН {inn} новости {year}")
    return qs


def profile_queries(company: str, industry: str = "", website: str = "") -> list[str]:
    name = (company or "").strip() or "компания"
    qs = [
        f'"{name}" официальный сайт',
        f'"{name}" чем занимается деятельность',
    ]
    if industry and industry not in ("—", "-"):
        qs.append(f'"{name}" {industry}')
    if website and website not in ("—", "-"):
        qs.append(f'"{name}" {website}')
    return qs


def build_research_web_queries(
    company: str,
    lead: dict[str, Any] | None = None,
    *,
    year: str,
    max_queries: int = 7,
) -> list[str]:
    """Детерминированный набор: каталоги(ИНН) → новости → профиль."""
    lead = lead or {}
    inn = _digits_inn(lead.get("inn") or lead.get("INN"))
    industry = str(lead.get("industry") or "").strip()
    website = str(lead.get("website") or "").strip()

    ordered: list[str] = []
    if inn:
        ordered.extend(catalog_queries_for_inn(inn, company)[:4])
    ordered.extend(news_queries(company, year, inn)[:2])
    ordered.extend(profile_queries(company, industry, website)[:2])
    return _dedupe_queries(ordered, limit=max_queries)


def merge_with_llm_queries(
    base: list[str],
    llm_queries: list[str],
    *,
    year: str,
    company: str = "",
    max_queries: int = 8,
) -> list[str]:
    """База (каталоги+новости) первой; LLM дополняет без вытеснения ИНН/каталогов."""
    year = str(year or "")[:4]
    name = (company or "").strip() or "компания"
    llm_extra: list[str] = []
    for q in llm_queries or []:
        low = q.lower()
        if "netherlands" in low and "инн" not in low:
            continue
        llm_extra.append(q)
    has_fresh = any(
        year in q and ("новост" in q.lower() or "пресс" in q.lower())
        for q in (base + llm_extra)
    )
    merged = list(base) + llm_extra
    if not has_fresh and year:
        insert_at = min(4, len(merged))
        merged.insert(insert_at, f'"{name}" новости {year}')
    return _dedupe_queries(merged, limit=max_queries)


def llm_query_prompt(*, task: str, context: str, year: str, has_inn: bool) -> str:
    """Промпт для Groq: каталоги по ИНН + свежие новости."""
    inn_line = (
        f"Обязательно 2–3 запроса по ИНН в каталоги: site:checko.ru, site:list-org.com, "
        f"site:rusprofile.ru, site:sbis.ru, «ИНН …». "
        if has_inn
        else "ИНН нет — запросы по названию компании и каталогам (checko, list-org). "
    )
    return (
        f"Ты — B2B-аналитик. Задача:\n{task}\nКонтекст: {context}\n\n"
        f"Сгенерируй 4–6 поисковых запросов (Google).\n"
        f"Порядок смысла: (1) каталоги юрлиц / реестры, (2) свежие новости {year}, (3) профиль.\n"
        f"{inn_line}"
        f"Хотя бы два запроса про новости {year} / пресс-релиз / за {year}.\n"
        f"Не делай общие запросы без названия компании или ИНН.\n"
        'Ответь строго JSON-массивом: ["запрос 1", ...]'
    )
