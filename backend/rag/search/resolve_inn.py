"""Поиск ИНН по названию компании и домену (ЕГРЮЛ / Checko search)."""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


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
    for junk in ("ооо", "ао", "зао", "пао", "оао", "ип", "llc", "ltd", "inc"):
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
            # пересечение токенов
            ta, tb = set(cn.split()), set(nm.split())
            if ta and tb:
                score += 10 * len(ta & tb)
    site = _clean_domain(str(cand.get("website") or ""))
    if domain and site and (domain == site or domain.endswith("." + site) or site.endswith("." + domain)):
        score += 40
    if cand.get("inn"):
        score += 5
    return score


async def resolve_inn(*, company: str, website: str = "") -> dict[str, Any]:
    """Найти ИНН: ЕГРЮЛ/Checko по названию, предпочесть совпадение с доменом."""
    company = (company or "").strip()
    if not company:
        return {"inn": None, "source": None, "candidates": []}

    domain = _clean_domain(website)
    try:
        from leadgen.modules.checko import search_companies
    except ImportError:
        return {"inn": None, "source": None, "candidates": []}

    try:
        found = await search_companies(company, count=5)
    except Exception as e:
        logger.warning("resolve_inn search_companies: %s", e)
        return {"inn": None, "source": None, "candidates": []}

    ranked: list[tuple[int, dict]] = []
    for c in found or []:
        if not isinstance(c, dict) or not c.get("inn"):
            continue
        ranked.append((_score_candidate(company, domain, c), c))
    ranked.sort(key=lambda x: x[0], reverse=True)

    candidates = [
        {
            "inn": str(c.get("inn")),
            "name": c.get("name") or c.get("name_short"),
            "score": sc,
        }
        for sc, c in ranked[:5]
    ]
    if not ranked:
        return {"inn": None, "source": "egrul", "candidates": []}

    best_score, best = ranked[0]
    # Без уверенности не подставляем чужой ИНН
    if best_score < 15:
        return {"inn": None, "source": "egrul", "candidates": candidates}

    return {
        "inn": str(best["inn"]),
        "source": "egrul_checko",
        "candidates": candidates,
        "name": best.get("name") or best.get("name_short"),
    }
