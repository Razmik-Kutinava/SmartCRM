"""Доп. источники для enrich_lead: Checko, таргет-запросы, парсинг сайта."""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def targeted_enrich_queries(company: str, industry: str, missing: list[str]) -> list[tuple[str, str]]:
    """Отдельные запросы под LinkedIn / ЛПР."""
    ind = f" {industry}" if industry else ""
    out: list[tuple[str, str]] = []
    if "linkedin" in missing:
        out.append((f"{company} site:linkedin.com/company{ind}", "linkedin"))
    if "decision_maker" in missing:
        out.append((f"{company} генеральный директор CEO руководитель{ind}", "decision_maker"))
    if "revenue" in missing:
        out.append((f"{company} выручка оборот год{ind}", "revenue"))
    return out


def _fmt_revenue(val: Any) -> str | None:
    if val is None:
        return None
    try:
        n = float(val)
    except (TypeError, ValueError):
        return str(val).strip() or None
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} млрд ₽"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f} млн ₽"
    return f"{int(n):,} ₽".replace(",", " ")


async def checko_enrich_by_inn(inn: str) -> tuple[dict[str, str], list[dict]]:
    """Checko по ИНН → поля enrich + сырые блоки для LLM."""
    inn = re.sub(r"\D", "", str(inn or ""))
    if len(inn) not in (10, 12):
        return {}, []

    try:
        from leadgen.modules.checko import _available, fetch_company, fetch_full_profile
    except ImportError:
        return {}, []

    if not _available():
        return {}, []

    enriched: dict[str, str] = {}
    raw: list[dict] = []

    try:
        card = await fetch_company(inn)
        if card:
            phones = card.get("dadata_phones") or []
            emails = card.get("dadata_emails") or []
            if phones:
                enriched["phone"] = str(phones[0])
            if emails:
                enriched["email"] = str(emails[0])
            if card.get("website"):
                w = str(card["website"]).strip()
                if w and not w.startswith("http"):
                    w = f"https://{w}"
                enriched["website"] = w
            if card.get("address"):
                enriched["address"] = str(card["address"])
            if card.get("director"):
                enriched["decision_maker"] = str(card["director"])
            if card.get("okved_name"):
                enriched["description"] = str(card["okved_name"])[:500]
            raw.append({
                "title": f"Checko: {card.get('name') or inn}",
                "snippet": " · ".join(
                    p for p in [
                        f"ИНН {inn}",
                        card.get("address"),
                        card.get("director"),
                        card.get("website"),
                    ] if p
                )[:700],
                "url": "",
                "date": "",
                "source": "checko",
            })

        fin = await fetch_full_profile(inn)
        rev = _fmt_revenue(fin.get("revenue"))
        if rev:
            enriched["revenue"] = rev
            raw.append({
                "title": f"Checko финансы {inn}",
                "snippet": f"Выручка: {rev}",
                "url": "",
                "date": "",
                "source": "checko_finance",
            })
    except Exception as e:
        logger.warning("checko_enrich_by_inn(%s): %s", inn, e)

    return enriched, raw


def _normalize_site_url(website: str) -> str | None:
    w = (website or "").strip()
    if not w or w in ("—", "-"):
        return None
    if not w.startswith("http"):
        w = f"https://{w}"
    try:
        p = urlparse(w)
        if not p.netloc:
            return None
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return None


def _html_to_text(html: str, limit: int = 3500) -> str:
    text = _HTML_TAG_RE.sub(" ", html)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


async def scrape_website_contacts(website: str) -> tuple[str, list[dict]]:
    """Главная + /contacts — текст для LLM."""
    base = _normalize_site_url(website)
    if not base:
        return "", []

    paths = ("", "/contacts", "/contact", "/about", "/company")
    chunks: list[str] = []
    raw: list[dict] = []

    async with httpx.AsyncClient(
        timeout=8.0,
        follow_redirects=True,
        headers={"User-Agent": "SmartCRM-enrich/1.0"},
    ) as client:
        for path in paths:
            url = urljoin(base + "/", path.lstrip("/")) if path else base
            try:
                r = await client.get(url)
                if r.status_code >= 400:
                    continue
                ctype = (r.headers.get("content-type") or "").lower()
                if "html" not in ctype and "text" not in ctype:
                    continue
                text = _html_to_text(r.text)
                if len(text) < 80:
                    continue
                chunks.append(f"--- {url} ---\n{text}")
                raw.append({
                    "title": f"Сайт: {url}",
                    "snippet": text[:400],
                    "url": url,
                    "date": "",
                    "source": "website_scrape",
                })
                if len(chunks) >= 2:
                    break
            except Exception as e:
                logger.debug("scrape %s: %s", url, e)

    return "\n\n".join(chunks), raw


def merge_enriched(base: dict[str, str], extra: dict[str, str]) -> dict[str, str]:
    """extra заполняет только пустые ключи в base."""
    out = dict(base)
    for k, v in extra.items():
        if k not in out and v:
            out[k] = v
    return out
