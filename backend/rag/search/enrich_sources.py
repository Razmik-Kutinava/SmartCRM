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


async def checko_enrich_by_inn(
    inn: str,
    *,
    existing_checko: dict | None = None,
    website: str | None = None,
) -> tuple[dict[str, str], list[dict], dict]:
    """Checko по ИНН → поля enrich + сниппеты + патч паспорта."""
    from .checko_passport import load_checko_for_enrich

    return await load_checko_for_enrich(
        inn,
        existing_checko=existing_checko,
        website=website,
    )


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


_SKIP_FETCH_HOSTS = frozenset({"youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com"})


def _is_fetchable_url(url: str) -> bool:
    u = (url or "").strip()
    if not u.startswith("http"):
        return False
    low = u.lower()
    if any(h in low for h in _SKIP_FETCH_HOSTS):
        return False
    if low.endswith(".pdf") or ".pdf?" in low:
        return False
    return True


async def fetch_page_text(url: str, *, limit: int = 5000) -> tuple[str, dict | None]:
    """Полный fetch HTML-страницы по URL."""
    if not _is_fetchable_url(url):
        return "", None
    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        headers={"User-Agent": "SmartCRM-enrich/1.0"},
    ) as client:
        try:
            r = await client.get(url)
            if r.status_code >= 400:
                return "", None
            ctype = (r.headers.get("content-type") or "").lower()
            if "html" not in ctype and "text" not in ctype:
                return "", None
            text = _html_to_text(r.text, limit=limit)
            if len(text) < 120:
                return "", None
            block = {
                "title": f"Страница: {url}",
                "snippet": text[:500],
                "url": url,
                "date": "",
                "source": "page_fetch",
            }
            return text, block
        except Exception as e:
            logger.debug("fetch_page_text %s: %s", url, e)
            return "", None


async def fetch_urls_from_hits(
    hits: list[dict],
    *,
    max_urls: int = 3,
    skip_sources: frozenset[str] | None = None,
) -> tuple[str, list[dict]]:
    """Fetch полного текста топ URL из результатов поиска."""
    skip = skip_sources or frozenset({"website_scrape", "checko", "checko_finance"})
    seen: set[str] = set()
    chunks: list[str] = []
    raw: list[dict] = []
    for hit in hits:
        url = str(hit.get("url") or "").strip()
        src = str(hit.get("source") or "")
        if not url or src in skip:
            continue
        key = url.lower().rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        text, block = await fetch_page_text(url)
        if not text or not block:
            continue
        chunks.append(f"--- {url} ---\n{text}")
        raw.append(block)
        if len(raw) >= max_urls:
            break
    return "\n\n".join(chunks), raw


def merge_enriched(base: dict[str, str], extra: dict[str, str]) -> dict[str, str]:
    """extra заполняет только пустые ключи в base."""
    out = dict(base)
    for k, v in extra.items():
        if k not in out and v:
            out[k] = v
    return out
