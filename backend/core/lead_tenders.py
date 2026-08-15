"""Тендеры на лиде: прошлое/текущее + usage поисковика без LLM-токенов."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

WebSearchFn = Callable[[str, int], Awaitable[tuple[list[dict], list[dict]]]]
ProviderFn = Callable[..., Awaitable[tuple[Any, list[dict]]]]

_MAX = 8


def usage_row(
    provider: str,
    *,
    requests: int = 1,
    tokens: int | None = None,
    billed: str = "requests",
    hits: int = 0,
    note: str = "",
    error: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "provider": provider,
        "requests": int(requests),
        "tokens": tokens,
        "billed": billed,
        "hits": int(hits),
        "note": note,
    }
    if error:
        row["error"] = error
    return row


def build_web_query(company: str, inn: str) -> str:
    bits = [str(company or "").strip()]
    inn_s = str(inn or "").strip()
    if inn_s:
        bits.append(f"ИНН {inn_s}")
    bits.append("тендер OR госзакупка OR zakupki.gov.ru")
    return " ".join(b for b in bits if b)


def contracts_from_checko(checko: dict[str, Any] | None) -> list[dict[str, Any]]:
    raw = checko if isinstance(checko, dict) else {}
    fin = raw.get("financials") if isinstance(raw.get("financials"), dict) else {}
    items = fin.get("contracts") if isinstance(fin.get("contracts"), list) else []
    out: list[dict[str, Any]] = []
    for c in items:
        if not isinstance(c, dict):
            continue
        title = str(c.get("subject") or c.get("name") or c.get("title") or "").strip()
        number = str(c.get("number") or c.get("regNum") or "").strip()
        out.append({
            "id": number or f"checko:{len(out)}",
            "title": title or number or "Контракт",
            "amount": c.get("amount"),
            "date": str(c.get("date") or ""),
            "customer": str(c.get("customer") or ""),
            "url": str(c.get("url") or ""),
            "source": "checko",
            "role": "supplier",
            "status": "past",
        })
    return out[:_MAX]


def summarize_lead_tenders(
    *,
    current: list[dict],
    past: list[dict],
    web: list[dict],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amounts = [float(x["amount"]) for x in past if isinstance(x.get("amount"), (int, float))]
    avg = round(sum(amounts) / len(amounts), 2) if amounts else None
    out = {
        "past_count": len(past),
        "current_count": len(current),
        "web_count": len(web),
        "avg_amount": avg,
    }
    if extra:
        out.update(extra)
    return out


def attach_tenders_to_checko(checko: dict[str, Any] | None, snapshot: dict[str, Any]) -> dict[str, Any]:
    out = dict(checko) if isinstance(checko, dict) else {}
    analyses = dict(out.get("analyses") or {}) if isinstance(out.get("analyses"), dict) else {}
    analyses["lead_tenders"] = snapshot
    out["analyses"] = analyses
    return out


def _norm_web(hit: dict[str, Any]) -> dict[str, Any]:
    title = str(hit.get("title") or "").strip()
    url = str(hit.get("url") or "")
    src = str(hit.get("source") or "web")
    return {
        "id": str(hit.get("id") or "") or f"web:{url or title}"[:80],
        "title": title[:200] or "Веб-результат",
        "amount": hit.get("amount"),
        "date": str(hit.get("date") or ""),
        "customer": str(hit.get("customer") or ""),
        "url": url,
        "source": src,
        "role": hit.get("role") or "unknown",
        "status": "web",
    }


async def search_lead_tenders(
    *,
    inn: str = "",
    company: str = "",
    checko: dict[str, Any] | None = None,
    web_search: WebSearchFn | None = None,
    tenderguru_search: ProviderFn | None = None,
    datanewton_stat: ProviderFn | None = None,
    checko_live: ProviderFn | None = None,
) -> dict[str, Any]:
    """Живой поиск: Checko + тендерные API + веб-поисковик. LLM не вызываем."""
    inn_s = str(inn or "").strip()
    company_s = str(company or "").strip()
    query = build_web_query(company_s, inn_s)
    past = contracts_from_checko(checko)
    providers: list[dict[str, Any]] = []
    if past:
        providers.append(usage_row("checko_cache", requests=0, billed="free", hits=len(past), note="уже на лиде"))

    from core import lead_tenders_providers as _p

    web_fn = web_search or _p.default_web_search
    tg_fn = tenderguru_search or _p.default_tenderguru_search
    dn_fn = datanewton_stat or _p.default_datanewton_stat
    ck_fn = checko_live or _p.default_checko_live

    async def _call(fn, *args):
        try:
            return await fn(*args)
        except Exception as exc:
            logger.warning("lead_tenders provider: %s", exc)
            return [], [usage_row(getattr(fn, "__name__", "provider"), requests=1, billed="error", error=str(exc)[:120])]

    web_res, tg_res, dn_res, ck_res = await asyncio.gather(
        _call(web_fn, query, _MAX),
        _call(tg_fn, inn_s, company_s),
        _call(dn_fn, inn_s),
        _call(ck_fn, inn_s, bool(past)),
    )

    web_hits, web_usage = web_res if isinstance(web_res, tuple) else ([], [])
    tg_items, tg_usage = tg_res if isinstance(tg_res, tuple) else ([], [])
    dn_payload, dn_usage = dn_res if isinstance(dn_res, tuple) else ({}, [])
    live_past, live_usage = ck_res if isinstance(ck_res, tuple) else ([], [])

    for block in (web_usage, tg_usage, dn_usage, live_usage):
        if isinstance(block, list):
            providers.extend(block)
    if not past and isinstance(live_past, list):
        past = live_past[:_MAX]

    current = [x for x in (tg_items or []) if isinstance(x, dict)][:_MAX]
    web = [_norm_web(x) for x in (web_hits or []) if isinstance(x, dict)][:_MAX]
    extra = dn_payload if isinstance(dn_payload, dict) else {}
    snap = {
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "inn": inn_s,
        "company": company_s,
        "query": query,
        "current": current,
        "past": past[:_MAX],
        "web": web,
        "summary": summarize_lead_tenders(current=current, past=past, web=web, extra=extra),
        "usage": {
            "llm_tokens": 0,
            "billed_as": "search_requests_not_llm",
            "providers": providers,
        },
    }
    return snap
