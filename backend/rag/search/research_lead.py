"""Исследование лида: 3 веб-поисковика + актуальное досье + enrich полей."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .config import load_config
from .enrich_sources import fetch_urls_from_hits
from .merge import _deduplicate, _format_results
from .prospect import enrich_lead
from .providers import _search_brave, _search_duckduckgo, _search_serper, _search_tavily
from .research_dossier import (
    agent_brief_from_summary,
    ensure_nonempty_summary,
    fallback_dossier_from_hits,
    is_error_summary,
    is_usable_dossier,
    split_dossier_and_passport_json,
    synthesize_dossier_llm,
)
from .research_passport import (
    extract_passport_from_research_sources,
    merge_research_passport,
)
from .research_queries import (
    build_research_web_queries,
    llm_query_prompt,
    merge_with_llm_queries,
)
from .research_status import done_status, research_status_label
from .resolve_inn import resolve_inn

logger = logging.getLogger(__name__)

_WEB_PROVIDERS = frozenset({"serper", "brave", "tavily", "duckduckgo"})


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


async def _deadline(coro, seconds: float, label: str):
    """Жёсткий дедлайн: по истечении сразу TimeoutError, не ждём отмены httpx/Ollama."""
    task = asyncio.create_task(coro)
    done, _pending = await asyncio.wait({task}, timeout=seconds)
    if task in done:
        return task.result()
    task.cancel()
    logger.warning("%s: дедлайн %.0fс — отдаём управление, фоновая отмена", label, seconds)
    return TimeoutError(f"{label} deadline {seconds:.0f}s")

# Явный мусор (ложные срабатывания на «Russland» / Netherlands и т.п.)
_JUNK_HOST_PARTS = (
    "netherlandsworldwide",
    "netherlandsandyou",
    "wikipedia.org/wiki/netherlands",
    "embassy",
    "consulate",
)

# Каталоги юрлиц — поднимаем в выдаче 🔍
_CATALOG_HOST_PARTS = (
    "checko.ru",
    "list-org.com",
    "rusprofile.ru",
    "sbis.ru",
    "spark-interfax",
    "egrul.nalog",
    "bo.nalog",
)


def _compact_hits(hits: list[dict], limit: int = 20) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for h in hits[:limit]:
        out.append(
            {
                "title": h.get("title") or "",
                "url": h.get("url") or h.get("link") or "",
                "snippet": (h.get("snippet") or h.get("description") or "")[:400],
                "source": h.get("source") or h.get("provider") or "",
                "date": h.get("date") or h.get("published") or "",
            }
        )
    return out


def _company_tokens(company: str) -> list[str]:
    raw = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]{3,}", (company or "").lower().replace("ё", "е"))
    stop = {"ооо", "ао", "зао", "пао", "ltd", "llc", "inc", "gmbh", "the", "and"}
    return [t for t in raw if t not in stop][:6]


def _hit_text(h: dict) -> str:
    return " ".join(
        [
            str(h.get("title") or ""),
            str(h.get("snippet") or h.get("description") or ""),
            str(h.get("url") or h.get("link") or ""),
        ]
    ).lower().replace("ё", "е")


def filter_relevant_hits(company: str, hits: list[dict], *, limit: int = 18) -> list[dict]:
    """Убирает явный мусор и поднимает хиты с токенами компании."""
    tokens = _company_tokens(company)
    scored: list[tuple[int, dict]] = []
    for h in hits:
        text = _hit_text(h)
        url = (h.get("url") or h.get("link") or "").lower()
        host = urlparse(url).netloc if url else ""
        if any(j in url or j in host for j in _JUNK_HOST_PARTS):
            continue
        if not url and h.get("source") == "tavily_answer":
            if tokens and not any(t in text for t in tokens):
                continue
        score = 0
        for t in tokens:
            if t in text:
                score += 3
        if any(c in host or c in url for c in _CATALOG_HOST_PARTS):
            score += 6
        if re.search(r"\b\d{10}(\d{2})?\b", text):
            score += 2  # ИНН в сниппете/URL
        if any(x in host for x in ("official", "company", ".ru", ".com")):
            score += 1
        if h.get("date"):
            score += 1
        # свежие новости в title/snippet
        yr = datetime.now(timezone.utc).year
        if any(w in text for w in ("новост", "пресс-релиз", str(yr), str(yr - 1))):
            score += 1
        scored.append((score, h))
    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [h for s, h in scored if s > 0]
    other = [h for s, h in scored if s == 0]
    out = (relevant + other)[:limit]
    return out if out else hits[:limit]


def fallback_summary_from_hits(company: str, hits: list[dict], today: str) -> str:
    """Совместимость: структурированное досье без LLM."""
    return fallback_dossier_from_hits(company, hits, today)


async def _narrative_web_research(company: str, lead: dict[str, Any]) -> dict[str, Any]:
    """Поиск через Serper/Brave/Tavily + досье (LLM Groq→Ollama или fallback).

    Запросы: каталоги по ИНН → свежие новости года → профиль компании.
    """
    from core.llm import chat

    today = datetime.now(timezone.utc).date().isoformat()
    year = today[:4]
    industry = (lead.get("industry") or "").strip()
    inn = re.sub(r"\D", "", str(lead.get("inn") or ""))
    has_inn = len(inn) in (10, 12)
    website = (lead.get("website") or "").strip()
    ctx_bits = [f"компания: {company}", f"дата исследования: {today}"]
    if industry and industry != "—":
        ctx_bits.append(f"отрасль: {industry}")
    if has_inn:
        ctx_bits.append(f"ИНН: {inn}")
    if website and website != "—":
        ctx_bits.append(f"сайт: {website}")
    context = "; ".join(ctx_bits)

    task = (
        f"Исследуй компанию «{company}» на актуальную дату {today}. "
        f"Сначала каталоги юрлиц по ИНН (Checko, list-org, rusprofile), "
        f"затем свежие новости {year}, продукты, рынок, риски."
    )

    # База всегда: ИНН-каталоги + свежие новости (даже если LLM молчит)
    base_queries = build_research_web_queries(company, lead, year=year, max_queries=7)

    llm_queries: list[str] = []
    query_mode = (os.getenv("RESEARCH_LLM_QUERIES") or "auto").strip().lower()
    if query_mode not in ("0", "false", "no", "never", "off"):
        try:
            raw_queries = await asyncio.wait_for(
                chat(
                    [
                        {
                            "role": "user",
                            "content": llm_query_prompt(
                                task=task,
                                context=context,
                                year=year,
                                has_inn=has_inn,
                            ),
                        }
                    ],
                    model="groq",
                    temperature=0.3,
                    max_tokens=300,
                ),
                timeout=_env_float("RESEARCH_QUERY_LLM_TIMEOUT", 8.0),
            )
            llm_queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries or "")][:6]
        except Exception as e:
            logger.warning("research_lead генерация запросов (groq): %s", e)

    queries = merge_with_llm_queries(
        base_queries, llm_queries, year=year, company=company, max_queries=8
    )

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []
    search_tasks: list[asyncio.Task] = []
    task_meta: list[str] = []

    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if provider not in _WEB_PROVIDERS or not pcfg.get("enabled", True):
                continue
            mr = min(int(pcfg.get("max_results", 6) or 6), 6)
            if provider == "serper":
                search_tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                search_tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                search_tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            elif provider == "duckduckgo":
                search_tasks.append(asyncio.create_task(_search_duckduckgo(q, mr)))
            else:
                continue
            task_meta.append(provider)

    if search_tasks:
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception) or not res:
                continue
            all_raw.extend(res)
            if prov not in providers_used:
                providers_used.append(prov)

    deduped = filter_relevant_hits(company, _deduplicate(all_raw), limit=18)
    formatted = _format_results(deduped)

    page_texts = ""
    pages_fetched = 0
    try:
        page_texts, page_raw = await fetch_urls_from_hits(deduped, max_urls=3)
        pages_fetched = len(page_raw)
        if page_raw:
            # Добавляем как доп. хиты для UI «сырые результаты»
            deduped = list(deduped) + page_raw
    except Exception as e:
        logger.warning("research_lead fetch страниц: %s", e)

    answer, llm_provider = await synthesize_dossier_llm(
        company=company,
        today=today,
        year=year,
        context=context,
        formatted_hits=formatted,
        page_texts=page_texts,
    )
    answer, passport_json = split_dossier_and_passport_json(answer or "")
    # Флаги LLM только если итоговый текст — реальное досье от модели
    if llm_provider and is_usable_dossier(answer) and not is_error_summary(answer):
        llm_used = True
    else:
        llm_used = False
        llm_provider = None
        passport_json = None
        answer = ensure_nonempty_summary(
            "", company=company, hits=deduped, today=today
        )

    brief = agent_brief_from_summary(answer)

    from core.agent_gaps import research_agent_checklist

    return {
        "answer": answer,
        "queries_used": queries,
        "raw_results": deduped,
        "providers_used": providers_used,
        "page_texts": page_texts,
        "passport_json": passport_json,
        "web_research": {
            "at": today,
            "summary": answer,
            "agent_brief": brief,
            "agent_requirements": research_agent_checklist(),
            "queries": queries,
            "raw_results": _compact_hits(deduped),
            "providers_used": providers_used,
            "llm": llm_used,
            "llm_provider": llm_provider,
            "fallback": not llm_used,
            "pages_fetched": pages_fetched,
            "status": done_status(llm_used),
            "status_label": research_status_label(done_status(llm_used)),
        },
    }


async def research_lead(*, lead: dict[str, Any], force: bool = False) -> dict[str, Any]:
    """
    Исследование: ИНН (если пусто) → Checko enrich → веб-досье → BuiltWith/DNS.
    Таймаут ~2.5 мин суммарно; этапы пишем в research_stages; gaps → card_suffler.
    """
    lead = dict(lead or {})
    company = (lead.get("company") or lead.get("name") or "").strip()
    if not company:
        raise ValueError("lead.company обязателен")

    stages: list[str] = []
    resolved_inn_meta: dict[str, Any] = {}

    # 1) ИНН, если пусто
    inn = re.sub(r"\D", "", str(lead.get("inn") or lead.get("INN") or ""))
    if len(inn) not in (10, 12):
        stages.append("resolve_inn")
        try:
            resolved_inn_meta = await resolve_inn(
                company=company,
                website=str(lead.get("website") or ""),
            )
        except Exception as e:
            logger.warning("research_lead resolve_inn: %s", e)
            resolved_inn_meta = {}
        found = re.sub(r"\D", "", str((resolved_inn_meta or {}).get("inn") or ""))
        if len(found) in (10, 12):
            lead["inn"] = found
            inn = found
            stages.append(f"inn:{found}")
        else:
            stages.append("inn:not_found")
    else:
        lead["inn"] = inn
        stages.append(f"inn:existing:{inn}")

    # 2) Checko/enrich + narrative (после ИНН Checko даёт ОКВЭД/фин/контакты)
    # Дефолты под ~2.5 мин суммарно (enrich + narrative + domain)
    enrich_timeout = _env_float("RESEARCH_ENRICH_TIMEOUT", 70.0)
    narr_timeout = _env_float("RESEARCH_NARRATIVE_TIMEOUT", 90.0)
    stages.append("enrich+narrative")
    enrich_res, narr_res = await asyncio.gather(
        _deadline(enrich_lead(lead=lead, force=force), enrich_timeout, "research_lead enrich"),
        _deadline(
            _narrative_web_research(company, lead), narr_timeout, "research_lead narrative"
        ),
        return_exceptions=True,
    )

    today = datetime.now(timezone.utc).date().isoformat()

    if isinstance(enrich_res, Exception):
        logger.warning(
            "research_lead enrich: %s", enrich_res or type(enrich_res).__name__
        )
        enrich_res = {
            "enriched": {},
            "missing_fields": [],
            "raw_results": [],
            "providers_used": [],
        }
    if isinstance(narr_res, Exception):
        logger.warning(
            "research_lead narrative: %s", narr_res or type(narr_res).__name__
        )
        fb = fallback_dossier_from_hits(company, [], today)
        narr_res = {
            "answer": fb,
            "queries_used": [],
            "raw_results": [],
            "providers_used": [],
            "page_texts": "",
            "web_research": {
                "at": today,
                "summary": fb,
                "agent_brief": agent_brief_from_summary(fb),
                "queries": [],
                "raw_results": [],
                "providers_used": [],
                "llm": False,
                "llm_provider": None,
                "fallback": True,
                "pages_fetched": 0,
                "status": "done_fallback",
                "status_label": research_status_label("done_fallback"),
            },
        }

    providers = list(
        dict.fromkeys(
            list(enrich_res.get("providers_used") or [])
            + list(narr_res.get("providers_used") or [])
        )
    )
    raw = list(enrich_res.get("raw_results") or []) + list(narr_res.get("raw_results") or [])

    # Паспорт: regex (+ LLM только если нужно и не удваиваем локальный синтез)
    page_texts = str(narr_res.get("page_texts") or "")
    # сниппеты сайта из enrich тоже полезны
    for h in enrich_res.get("raw_results") or []:
        if (h.get("source") or "") in ("website_scrape", "page_fetch") and h.get("snippet"):
            page_texts += f"\n\n--- {h.get('url') or ''} ---\n{h.get('snippet')}"

    passport_json = (
        narr_res.get("passport_json")
        if isinstance(narr_res.get("passport_json"), dict)
        else None
    )
    wr_meta = narr_res.get("web_research") if isinstance(narr_res.get("web_research"), dict) else {}
    dossier_provider = wr_meta.get("llm_provider")
    # auto: второй LLM только после Groq-досье без JSON; never/always — через env
    second_mode = (os.getenv("RESEARCH_PASSPORT_SECOND_LLM") or "auto").strip().lower()
    if passport_json:
        allow_passport_llm = False
    elif second_mode in ("1", "true", "yes", "always"):
        allow_passport_llm = True
    elif second_mode in ("0", "false", "no", "never"):
        allow_passport_llm = False
    else:
        allow_passport_llm = dossier_provider == "groq"

    try:
        extract = await extract_passport_from_research_sources(
            company=company,
            summary=str(narr_res.get("answer") or ""),
            hits=list(narr_res.get("raw_results") or [])[:18],
            page_texts=page_texts,
            llm_json=passport_json,
            allow_llm=allow_passport_llm,
        )
    except Exception as e:
        logger.warning("research_lead passport extract: %s", e)
        extract = {}

    enriched, passport = merge_research_passport(enrich_res, extract)
    web_research = narr_res.get("web_research") or {
        "at": today,
        "summary": narr_res.get("answer") or "",
        "agent_brief": "",
        "queries": [],
        "raw_results": [],
        "providers_used": [],
        "llm": False,
        "llm_provider": None,
        "fallback": True,
        "pages_fetched": 0,
    }
    if isinstance(web_research, dict):
        web_research = dict(web_research)
        web_research["summary"] = ensure_nonempty_summary(
            str(web_research.get("summary") or ""),
            company=company,
            hits=list(narr_res.get("raw_results") or []),
            today=today,
        )
        if not web_research.get("agent_brief"):
            web_research["agent_brief"] = agent_brief_from_summary(web_research["summary"])
        if not web_research.get("agent_requirements"):
            from core.agent_gaps import research_agent_checklist

            web_research["agent_requirements"] = research_agent_checklist()
        web_research.setdefault("status", done_status(bool(web_research.get("llm"))))
        web_research.setdefault(
            "status_label", research_status_label(str(web_research.get("status") or ""))
        )
        web_research["passport_extract"] = {
            "phones": extract.get("phones") or [],
            "emails": extract.get("emails") or [],
            "industry": extract.get("industry"),
            "contacts_count": len(extract.get("contacts") or []),
            "director": extract.get("director"),
        }

    # BuiltWith + WhoIs/DNS по сайту (даже без ИНН / Checko)
    website = (
        (enriched or {}).get("website")
        or (lead.get("website") or "")
        or ""
    ).strip()
    if (not website or website in ("—", "-")) and isinstance(passport, dict):
        co = (passport.get("checko") or {}).get("company") or {}
        if isinstance(co, dict):
            website = str(co.get("website") or "").strip()

    domain_pack: dict[str, Any] = {}
    if website and website not in ("—", "-"):
        try:
            from .domain_enrich import enrich_domain_signals

            domain_pack = await enrich_domain_signals(website)
        except Exception as e:
            logger.warning("research_lead domain enrich: %s", e)
            domain_pack = {}

    tech = domain_pack.get("tech") if isinstance(domain_pack.get("tech"), dict) else {}
    dns = (
        domain_pack.get("domain_signals")
        if isinstance(domain_pack.get("domain_signals"), dict)
        else {}
    )
    if tech or dns:
        passport = _merge_domain_into_passport(passport, tech, dns)
        if isinstance(web_research, dict):
            web_research = dict(web_research)
            if dns:
                web_research["domain_signals"] = dns
            if tech:
                from .domain_enrich import tech_brief

                brief_extra = tech_brief(tech)
                if brief_extra:
                    prev = str(web_research.get("agent_brief") or "")
                    addon = f"\n\n## Технологии (BuiltWith)\n{brief_extra}"
                    if dns.get("summary"):
                        addon += f"\nDNS/WhoIs: {dns['summary']}"
                    if "## Технологии (BuiltWith)" not in prev:
                        web_research["agent_brief"] = (prev + addon).strip()[:4500]
            for p in domain_pack.get("providers_used") or []:
                if p not in providers:
                    providers.append(p)
            raw = list(raw) + list(domain_pack.get("raw_results") or [])

    stages.append("domain_signals")

    # ИНН в passport/enriched, если нашли
    if inn and len(inn) in (10, 12):
        if not isinstance(passport, dict):
            passport = {}
        else:
            passport = dict(passport)
        passport["inn"] = passport.get("inn") or inn
        checko_p = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
        checko_p = dict(checko_p)
        co_p = checko_p.get("company") if isinstance(checko_p.get("company"), dict) else {}
        co_p = dict(co_p)
        co_p.setdefault("inn", inn)
        checko_p["company"] = co_p
        passport["checko"] = checko_p
        if isinstance(enriched, dict):
            enriched = dict(enriched)
            enriched.setdefault("inn", inn)

    from core.agent_gaps import card_suffler

    lead_like = _lead_like_after_research(lead, enriched, passport, web_research, tech)
    suffler = card_suffler(lead_like)
    remaining = list(suffler.get("missing_keys") or [])
    if remaining and _env_float("RESEARCH_SECOND_PASS", 1.0) >= 1:
        stages.append("field_fill")
        try:
            from .company_name_ru import company_search_variants
            from .field_fill import fill_gaps_from_web

            fill_company = company_search_variants(company)[0] if company else company
            # предпочесть RU-вариант для добора
            for v in company_search_variants(company):
                if re.search(r"[а-яА-ЯёЁ]", v):
                    fill_company = v
                    break
            enriched, passport, fill_hits, fill_meta = await fill_gaps_from_web(
                company=fill_company,
                missing_keys=remaining,
                enriched=enriched if isinstance(enriched, dict) else {},
                passport=passport if isinstance(passport, dict) else {},
                website=website or str(lead.get("website") or ""),
            )
            if fill_hits:
                raw = list(raw) + list(fill_hits)
            if fill_meta.get("inn"):
                lead["inn"] = fill_meta["inn"]
                inn = str(fill_meta["inn"])
                stages.append(f"inn:fill:{inn}")
                if "checko" not in providers and fill_meta.get("checko"):
                    providers.append("checko")
            if fill_meta.get("filled_keys"):
                stages.append("filled:" + ",".join(fill_meta["filled_keys"]))
            if isinstance(web_research, dict) and fill_hits:
                web_research = dict(web_research)
                extra = "\n".join(
                    f"- {h.get('title')}: {(h.get('snippet') or '')[:180]}"
                    for h in fill_hits[:6]
                )
                if extra:
                    brief0 = str(web_research.get("agent_brief") or "")
                    web_research["agent_brief"] = (
                        brief0 + "\n\n## Добор полей\n" + extra
                    ).strip()[:4500]
            lead_like = _lead_like_after_research(
                lead, enriched, passport, web_research, tech
            )
            suffler = card_suffler(lead_like)
            remaining = list(suffler.get("missing_keys") or [])
        except Exception as e:
            logger.warning("research_lead field_fill: %s", e)
            stages.append("field_fill:error")

    if isinstance(web_research, dict):
        web_research = dict(web_research)
        web_research["research_stages"] = list(stages)
        web_research["remaining_gaps"] = suffler.get("gaps") or []
        if resolved_inn_meta:
            web_research["inn_resolve"] = {
                "inn": resolved_inn_meta.get("inn"),
                "source": resolved_inn_meta.get("source"),
                "candidates": (resolved_inn_meta.get("candidates") or [])[:3],
            }

    # Sync: паспорт/🔍 → плоские поля enriched (телефон, email, бюджет…)
    try:
        from .card_sync import sync_enriched_from_research

        enriched, passport, sync_keys = sync_enriched_from_research(
            lead=lead,
            enriched=enriched if isinstance(enriched, dict) else {},
            passport=passport if isinstance(passport, dict) else {},
            web_research=web_research if isinstance(web_research, dict) else {},
        )
        if sync_keys:
            stages.append("card_sync:" + ",".join(sync_keys))
            lead_like = _lead_like_after_research(
                lead, enriched, passport, web_research, tech
            )
            from core.agent_gaps import card_suffler as _card_suffler

            suffler = _card_suffler(lead_like)
            remaining = list(suffler.get("missing_keys") or [])
            if isinstance(web_research, dict):
                web_research["remaining_gaps"] = suffler.get("gaps") or []
                web_research["card_sync_keys"] = sync_keys
    except Exception as e:
        logger.warning("research_lead card_sync: %s", e)
        stages.append("card_sync:error")

    stages.append("done")
    return {
        "enriched": enriched,
        "missing_fields": enrich_res.get("missing_fields") or [],
        "passport": passport,
        "cached": enrich_res.get("cached", False),
        "raw_results": raw[:40],
        "providers_used": providers,
        "answer": narr_res.get("answer") or "",
        "queries_used": narr_res.get("queries_used") or [],
        "web_research": web_research,
        "research_stages": stages,
        "card_suffler": suffler,
        "remaining_gaps": remaining,
        "resolved_inn": resolved_inn_meta or None,
    }


def _lead_like_after_research(
    lead: dict[str, Any],
    enriched: dict[str, Any] | None,
    passport: dict[str, Any] | None,
    web_research: dict[str, Any] | None,
    tech: dict[str, Any] | None,
) -> dict[str, Any]:
    enriched = enriched or {}
    passport = passport if isinstance(passport, dict) else {}
    checko = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
    checko = dict(checko)
    if isinstance(web_research, dict):
        analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
        analyses = dict(analyses)
        analyses["web_research"] = web_research
        checko["analyses"] = analyses
    if tech:
        checko["tech"] = {**(checko.get("tech") or {}), **tech}
    return {
        "company": lead.get("company") or enriched.get("company"),
        "contact": lead.get("contact") or enriched.get("decision_maker"),
        "email": lead.get("email") or enriched.get("email"),
        "phone": lead.get("phone") or enriched.get("phone"),
        "industry": lead.get("industry") or passport.get("industry"),
        "budget": lead.get("budget") or enriched.get("revenue"),
        "stage": lead.get("stage"),
        "employees": lead.get("employees") or enriched.get("employees"),
        "website": lead.get("website") or enriched.get("website"),
        "inn": lead.get("inn") or passport.get("inn"),
        "checko": checko,
        "tech": tech or passport.get("tech") or checko.get("tech"),
        "financials": checko.get("financials") or passport.get("financials"),
    }


async def _second_pass_for_gaps(
    company: str, missing_keys: list[str], *, max_queries: int = 3
) -> list[dict]:
    """Короткие целевые запросы только по оставшимся дырам."""
    qmap = {
        "email": f'"{company}" email OR почта контакт',
        "phone": f'"{company}" телефон OR +7 контакты',
        "contact": f'"{company}" генеральный директор OR руководитель',
        "industry": f'"{company}" отрасль ОКВЭД чем занимается',
        "okved": f'"{company}" ОКВЭД вид деятельности',
        "financials": f'"{company}" выручка финансы отчетность',
        "website": f'"{company}" официальный сайт',
        "employees": f'"{company}" численность сотрудников',
    }
    queries: list[str] = []
    for key in missing_keys:
        if key in qmap and qmap[key] not in queries:
            queries.append(qmap[key])
        if len(queries) >= max_queries:
            break
    if not queries:
        return []

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    tasks: list[asyncio.Task] = []
    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if provider not in _WEB_PROVIDERS or not pcfg.get("enabled", True):
                continue
            mr = min(int(pcfg.get("max_results", 4) or 4), 4)
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            elif provider == "duckduckgo":
                tasks.append(asyncio.create_task(_search_duckduckgo(q, mr)))
    if not tasks:
        return []
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out: list[dict] = []
    for res in results:
        if isinstance(res, Exception) or not res:
            continue
        out.extend(res)
    return _deduplicate(out)[:12]


def _merge_domain_into_passport(
    passport: dict[str, Any] | None,
    tech: dict[str, Any],
    dns: dict[str, Any],
) -> dict[str, Any]:
    """Кладёт BuiltWith/DNS в passport.tech и checko.tech."""
    base: dict[str, Any] = dict(passport) if isinstance(passport, dict) else {}
    merged_tech = dict(tech) if tech else dict(base.get("tech") or {})
    if dns:
        merged_tech["domain_signals"] = dns
    if merged_tech:
        base["tech"] = merged_tech
    checko = base.get("checko") if isinstance(base.get("checko"), dict) else {}
    checko = dict(checko)
    if merged_tech:
        # Не затираем bitrix/UF внутрии в checko.tech — только доменный стек
        prev = checko.get("tech") if isinstance(checko.get("tech"), dict) else {}
        checko["tech"] = {**prev, **merged_tech}
    if dns:
        analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
        analyses = dict(analyses)
        wr = analyses.get("web_research") if isinstance(analyses.get("web_research"), dict) else {}
        wr = dict(wr)
        wr["domain_signals"] = dns
        analyses["web_research"] = wr
        checko["analyses"] = analyses
    if checko:
        base["checko"] = checko
    return base
