"""Целевой добор полей по gaps: веб-запросы → extract → passport/enriched (+ Checko по ИНН)."""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
)
_DIR_RE = re.compile(
    r"(?:генеральный\s+директор|директор|руководител\w*|ceo|генеральный)\s*[:\-]?\s*"
    r"([А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z]\.?){0,2}(?:\s+[А-ЯЁA-Z][а-яёa-z]+)?)",
    re.I,
)
_REV_RE = re.compile(
    r"(?:выручка|оборот|revenue)[^\d]{0,20}([\d\s]+(?:[.,]\d+)?)\s*(млрд|млн|тыс|₽|руб|rub)?",
    re.I,
)

# Gaps, которые имеет смысл закрывать вебом (CRM-only не трогаем)
_WEB_FILLABLE = frozenset({
    "inn", "okved", "industry", "contact", "email", "phone",
    "financials", "website", "employees", "tech_stack",
})


def _blob(hits: list[dict]) -> str:
    parts = []
    for h in hits or []:
        parts.append(f"{h.get('title') or ''}\n{h.get('snippet') or ''}")
    return "\n".join(parts)


def extract_fields_from_hits(hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Regex-extract из сниппетов целевого поиска."""
    from .resolve_inn import extract_inn_from_texts
    from .checko_passport import filter_emails, filter_phones

    text = _blob(hits)
    out: dict[str, Any] = {}
    inn = extract_inn_from_texts(
        [f"{h.get('title') or ''} {h.get('snippet') or ''}" for h in (hits or [])]
    )
    if inn:
        out["inn"] = inn
    emails = filter_emails(_EMAIL_RE.findall(text))
    phones = filter_phones(_PHONE_RE.findall(text))
    if emails:
        out["email"] = emails[0]
        out["emails"] = emails[:5]
    if phones:
        out["phone"] = phones[0]
        out["phones"] = phones[:5]
    m = _DIR_RE.search(text)
    if m:
        out["decision_maker"] = m.group(1).strip()
        out["director"] = out["decision_maker"]
    rm = _REV_RE.search(text)
    if rm:
        out["revenue_hint"] = " ".join(p for p in rm.groups() if p).strip()
    # сайт из url хитов (не агрегаторы)
    for h in hits or []:
        url = str(h.get("url") or "")
        if url.startswith("http") and not any(
            x in url for x in ("google.", "yandex.", "duckduckgo", "wikipedia")
        ):
            out.setdefault("website", url.split("?")[0][:200])
            break
    return out


async def search_hits_for_gaps(
    company: str, missing_keys: list[str], *, max_queries: int = 5
) -> list[dict]:
    """Веб-хиты только по fillable gaps."""
    import asyncio

    from .config import load_config
    from .merge import _deduplicate
    from .providers import _search_brave, _search_duckduckgo, _search_serper, _search_tavily

    keys = [k for k in missing_keys if k in _WEB_FILLABLE]
    qmap = {
        "inn": f'"{company}" ИНН',
        "email": f'"{company}" email OR почта',
        "phone": f'"{company}" телефон контакты',
        "contact": f'"{company}" генеральный директор',
        "industry": f'"{company}" отрасль ОКВЭД',
        "okved": f'"{company}" ОКВЭД',
        "financials": f'"{company}" выручка финансы',
        "website": f'"{company}" официальный сайт',
        "employees": f'"{company}" численность сотрудников',
        "tech_stack": f'"{company}" технологии IT стек',
    }
    queries: list[str] = []
    for key in keys:
        q = qmap.get(key)
        if q and q not in queries:
            queries.append(q)
        if len(queries) >= max_queries:
            break
    if not queries:
        return []

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    web = frozenset({"serper", "brave", "tavily", "duckduckgo"})
    tasks: list[asyncio.Task] = []
    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if provider not in web or not pcfg.get("enabled", True):
                continue
            mr = min(int(pcfg.get("max_results", 5) or 5), 5)
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
    return _deduplicate(out)[:20]


async def checko_after_inn(
    inn: str, *, website: str = "", existing_checko: dict | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """После найденного ИНН — полный Checko passport."""
    from .enrich_sources import checko_enrich_by_inn

    fields, _raw, passport = await checko_enrich_by_inn(
        inn, existing_checko=existing_checko, website=website
    )
    return fields or {}, passport or {}


def _merge_extract_into(
    enriched: dict[str, Any],
    passport: dict[str, Any],
    extracted: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    enriched = dict(enriched or {})
    passport = dict(passport or {}) if isinstance(passport, dict) else {}

    if extracted.get("inn") and not enriched.get("inn"):
        enriched["inn"] = extracted["inn"]
        passport["inn"] = passport.get("inn") or extracted["inn"]
    if extracted.get("email") and not enriched.get("email"):
        enriched["email"] = extracted["email"]
    if extracted.get("phone") and not enriched.get("phone"):
        enriched["phone"] = extracted["phone"]
    if extracted.get("decision_maker") and not enriched.get("decision_maker"):
        enriched["decision_maker"] = extracted["decision_maker"]
    if extracted.get("website") and not enriched.get("website"):
        enriched["website"] = extracted["website"]
    if extracted.get("revenue_hint") and not enriched.get("revenue"):
        enriched["revenue"] = extracted["revenue_hint"]

    checko = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
    checko = dict(checko)
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    company = dict(company)
    if extracted.get("inn"):
        company.setdefault("inn", extracted["inn"])
    if extracted.get("emails"):
        prev = list(company.get("emails") or [])
        for e in extracted["emails"]:
            if e not in prev:
                prev.append(e)
        company["emails"] = prev
    if extracted.get("phones"):
        from .checko_passport import filter_phones

        cleaned = filter_phones(extracted["phones"])
        if cleaned:
            prev = list(company.get("phones") or [])
            for p in cleaned:
                if p not in prev:
                    prev.append(p)
            company["phones"] = prev
            if not enriched.get("phone"):
                enriched["phone"] = cleaned[0]
    if extracted.get("director"):
        company.setdefault("director", extracted["director"])
    checko["company"] = company
    passport["checko"] = checko
    return enriched, passport


async def fill_gaps_from_web(
    *,
    company: str,
    missing_keys: list[str],
    enriched: dict[str, Any] | None = None,
    passport: dict[str, Any] | None = None,
    website: str = "",
) -> tuple[dict[str, Any], dict[str, Any], list[dict], dict[str, Any]]:
    """Добор полей по gaps → enriched/passport; при ИНН — Checko."""
    enriched = dict(enriched or {})
    passport = dict(passport or {}) if isinstance(passport, dict) else {}
    keys = [k for k in (missing_keys or []) if k in _WEB_FILLABLE]
    meta: dict[str, Any] = {"filled_keys": [], "inn": None, "checko": False}

    if not keys:
        return enriched, passport, [], meta

    hits = await search_hits_for_gaps(company, keys)
    extracted = extract_fields_from_hits(hits)
    enriched, passport = _merge_extract_into(enriched, passport, extracted)

    inn_before = re.sub(
        r"\D",
        "",
        str(
            (passport.get("inn") if isinstance(passport, dict) else "")
            or ((passport.get("checko") or {}).get("company") or {}).get("inn")
            or ""
        ),
    )
    inn = str(extracted.get("inn") or enriched.get("inn") or passport.get("inn") or "")
    inn = re.sub(r"\D", "", inn)
    inn_changed = bool(
        len(inn) in (10, 12)
        and inn_before
        and len(inn_before) in (10, 12)
        and inn != inn_before
    )
    need_checko = len(inn) in (10, 12) and (
        inn_changed
        or "financials" in keys
        or "okved" in keys
        or not (passport.get("checko") or {}).get("financials")
        or (passport.get("checko") or {}).get("meta", {}).get("source") == "web_research"
    )
    if need_checko:
        try:
            # при смене ИНН не тащим старый паспорт чужой фирмы
            existing = None
            if not inn_changed:
                existing = (
                    passport.get("checko") if isinstance(passport.get("checko"), dict) else None
                )
            fields, pp = await checko_after_inn(
                inn,
                website=website or enriched.get("website") or "",
                existing_checko=existing,
            )
            if fields:
                for k, v in fields.items():
                    if v and (inn_changed or not enriched.get(k)):
                        enriched[k] = v
            if pp:
                from .checko_passport import merge_checko_passport

                new_c = pp.get("checko") if isinstance(pp.get("checko"), dict) else {}
                if inn_changed and new_c:
                    # заменяем company/financials целевого ИНН, analyses оставляем
                    base = (
                        passport.get("checko")
                        if isinstance(passport.get("checko"), dict)
                        else {}
                    )
                    analyses = base.get("analyses") if isinstance(base.get("analyses"), dict) else {}
                    passport["checko"] = dict(new_c)
                    if analyses:
                        passport["checko"]["analyses"] = analyses
                    if new_c.get("meta") is None:
                        passport["checko"]["meta"] = {"source": "checko", "inn": inn}
                elif new_c:
                    base = (
                        passport.get("checko")
                        if isinstance(passport.get("checko"), dict)
                        else {}
                    )
                    passport["checko"] = merge_checko_passport(base, new_c)
                for pk in ("inn", "ogrn", "industry", "city"):
                    if pp.get(pk) and (inn_changed or not passport.get(pk)):
                        passport[pk] = pp[pk]
                if pp.get("financials") and (inn_changed or not passport.get("financials")):
                    passport["financials"] = pp["financials"]
                passport["inn"] = inn
                meta["checko"] = True
            meta["inn"] = inn
            if inn_changed:
                meta["inn_changed"] = True
                meta["inn_before"] = inn_before
            enriched["inn"] = inn
        except Exception as e:
            logger.warning("fill_gaps checko_after_inn: %s", e)
            meta["inn"] = inn

    for k in ("inn", "email", "phone", "contact", "website", "financials"):
        if k == "contact" and enriched.get("decision_maker"):
            meta["filled_keys"].append(k)
        elif k == "financials" and (
            enriched.get("revenue")
            or (passport.get("checko") or {}).get("financials")
        ):
            meta["filled_keys"].append(k)
        elif k != "contact" and k != "financials" and (enriched.get(k) or passport.get(k)):
            meta["filled_keys"].append(k)

    return enriched, passport, hits, meta
