"""Поиск ИНН по названию компании и домену (ЕГРЮЛ / Checko / веб)."""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_INN_RE = re.compile(r"\b(\d{10}|\d{12})\b")
_INN_NEAR_RE = re.compile(
    r"(?:инн|inn|tax\s*id|огрн)[^\d]{0,12}(\d{10}|\d{12})",
    re.I,
)


def _clean_domain(website: str) -> str:
    raw = (website or "").strip().lower()
    if not raw or raw in ("—", "-"):
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = (urlparse(raw).hostname or "").removeprefix("www.")
    except Exception:
        host = ""
    return host if host and "." in host else ""


def _norm_name(name: str) -> str:
    s = (name or "").lower().replace("ё", "е")
    s = re.sub(r"[\"«»']", "", s)
    for junk in ("ооо", "ао", "зао", "пао", "оао", "ип", "llc", "ltd", "inc", "банк", "bank"):
        s = re.sub(rf"\b{junk}\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _score_candidate(company: str, domain: str, cand: dict[str, Any]) -> int:
    score = 0
    cn = _norm_name(company)
    nm = _norm_name(str(cand.get("name") or cand.get("name_short") or ""))
    if cn and nm:
        if cn == nm:
            score += 50
        elif cn in nm or nm in cn:
            score += 30
        else:
            ta, tb = set(cn.split()), set(nm.split())
            if ta and tb:
                score += 10 * len(ta & tb)
    site = _clean_domain(str(cand.get("website") or ""))
    if domain and site and (domain == site or domain.endswith("." + site) or site.endswith("." + domain)):
        score += 40
    if cand.get("inn"):
        score += 5
    return score


def extract_inn_from_texts(texts: list[str]) -> str | None:
    """Достаёт ИНН: сначала рядом с «ИНН», иначе первое 10/12-значное (не телефон)."""
    near: list[str] = []
    loose: list[str] = []
    for t in texts or []:
        raw = str(t or "")
        for m in _INN_NEAR_RE.finditer(raw):
            near.append(m.group(1))
        for m in _INN_RE.finditer(raw):
            digits = m.group(1)
            # отсечь куски телефонов 79xxxxxxxxx
            if digits.startswith("79") and len(digits) == 11:
                continue
            if digits.startswith("89") and len(digits) == 11:
                continue
            loose.append(digits)
    for inn in near + loose:
        if len(inn) in (10, 12):
            return inn
    return None


async def _web_find_inn(company: str, website: str = "") -> str | None:
    """Веб: «компания ИНН» через Serper/Brave/Tavily/DDG."""
    from .providers import _search_brave, _search_duckduckgo, _search_serper, _search_tavily

    domain = _clean_domain(website)
    queries = [
        f'"{company}" ИНН',
        f"{company} ИНН организации",
    ]
    if domain:
        queries.append(f"site:{domain} ИНН")

    import asyncio

    tasks = []
    for q in queries[:2]:
        tasks.append(asyncio.create_task(_search_serper(q, 5)))
        tasks.append(asyncio.create_task(_search_brave(q, 5)))
        tasks.append(asyncio.create_task(_search_tavily(q, 4)))
        tasks.append(asyncio.create_task(_search_duckduckgo(q, 4)))
    if not tasks:
        return None
    results = await asyncio.gather(*tasks, return_exceptions=True)
    texts: list[str] = []
    for res in results:
        if isinstance(res, Exception) or not res:
            continue
        for h in res:
            texts.append(f"{h.get('title') or ''} {h.get('snippet') or ''}")
    return extract_inn_from_texts(texts)


async def _egrul_best(company: str, domain: str) -> tuple[dict | None, list[dict], int]:
    try:
        from leadgen.modules.checko import search_companies
    except ImportError:
        return None, [], 0

    try:
        found = await search_companies(company, count=5)
    except Exception as e:
        logger.warning("resolve_inn search_companies(%s): %s", company, e)
        return None, [], 0

    ranked: list[tuple[int, dict]] = []
    for c in found or []:
        if not isinstance(c, dict) or not c.get("inn"):
            continue
        ranked.append((_score_candidate(company, domain, c), c))
    ranked.sort(key=lambda x: x[0], reverse=True)
    candidates = [
        {"inn": str(c.get("inn")), "name": c.get("name") or c.get("name_short"), "score": sc}
        for sc, c in ranked[:5]
    ]
    if not ranked:
        return None, candidates, 0
    return ranked[0][1], candidates, ranked[0][0]


async def resolve_inn(*, company: str, website: str = "") -> dict[str, Any]:
    """ИНН: варианты имени (EN→RU) → ЕГРЮЛ → веб-regex."""
    company = (company or "").strip()
    if not company:
        return {"inn": None, "source": None, "candidates": []}

    from .company_name_ru import company_search_variants

    domain = _clean_domain(website)
    variants = company_search_variants(company)
    all_candidates: list[dict] = []
    best: dict | None = None
    best_score = 0
    used_query = ""

    for q in variants:
        cand, cands, score = await _egrul_best(q, domain)
        all_candidates.extend(cands)
        if cand and score > best_score:
            best, best_score, used_query = cand, score, q
        if best_score >= 30:
            break

    if best and best_score >= 15:
        return {
            "inn": str(best["inn"]),
            "source": "egrul_checko",
            "candidates": all_candidates[:5],
            "name": best.get("name") or best.get("name_short"),
            "query": used_query,
        }

    # Веб-fallback по всем вариантам имени
    for q in variants[:3]:
        try:
            inn = await _web_find_inn(q, website)
        except Exception as e:
            logger.warning("resolve_inn web(%s): %s", q, e)
            inn = None
        if inn:
            return {
                "inn": inn,
                "source": "web",
                "candidates": all_candidates[:5],
                "query": q,
            }

    return {
        "inn": None,
        "source": "egrul+web",
        "candidates": all_candidates[:5],
    }
