"""Живые провайдеры тендеров лида (без LLM)."""
from __future__ import annotations

import os
from typing import Any

from core.lead_tenders import _MAX, contracts_from_checko, usage_row
from core.stats import track_api


def _env(*names: str) -> bool:
    return any(str(os.getenv(n) or "").strip() for n in names)


async def default_web_search(query: str, max_results: int = 8) -> tuple[list[dict], list[dict]]:
    from rag.search.providers import _search_brave, _search_serper, _search_tavily

    hits: list[dict] = []
    usage: list[dict] = []
    plan = (
        ("brave", _search_brave, ("BRAVE_API_KEY",), "requests", "квота Brave, не токены"),
        ("serper", _search_serper, ("SERPER_API_KEY",), "searches", "кредиты Serper, не токены"),
        ("tavily", _search_tavily, ("TAVILY_API_KEY",), "credits", "кредиты Tavily (не LLM-токены SmartCRM)"),
    )
    for name, fn, envs, billed, note in plan:
        if not _env(*envs):
            usage.append(usage_row(name, requests=0, billed="skipped", note="нет ключа"))
            continue
        try:
            rows = await fn(query, max_results)
            n = len(rows or [])
            hits.extend(rows or [])
            usage.append(usage_row(name, requests=1, billed=billed, hits=n, note=note, tokens=None))
            try:
                track_api(name)
            except Exception:
                pass
        except Exception as exc:
            usage.append(usage_row(name, requests=1, billed=billed, note=note, error=str(exc)[:120]))
    return hits[: max_results * 3], usage


async def default_tenderguru_search(inn: str, company: str) -> tuple[list[dict], list[dict]]:
    key = str(os.getenv("TENDERGURU_API_KEY") or "").strip()
    if not key:
        return [], [usage_row("tenderguru", requests=0, billed="skipped", note="нет ключа")]
    from services.tenderguru import TenderGuruClient

    client = TenderGuruClient(key)
    items: list[dict] = []
    n = 0
    err: str | None = None
    try:
        if company:
            n += 1
            raw = await client.search_tenders(kwords=company[:80], actual=1)
            fmt = TenderGuruClient.format_search_response(raw)
            for t in fmt.get("tenders") or []:
                items.append({
                    "id": str(t.get("id") or t.get("tender_num") or len(items)),
                    "title": str(t.get("name") or "")[:200],
                    "amount": t.get("budget"),
                    "date": str(t.get("deadline") or t.get("published_date") or ""),
                    "customer": str(t.get("customer") or ""),
                    "url": str(t.get("external_url") or t.get("inner_url") or ""),
                    "source": "tenderguru",
                    "role": "unknown",
                    "status": "current" if t.get("status") == "active" else "past",
                })
    except Exception as exc:
        err = str(exc)[:120]
    try:
        if inn:
            n += 1
            raw_plans = await client.search_plans(org_inn=inn)
            pfmt = TenderGuruClient.format_plans_response(raw_plans)
            for t in pfmt.get("plans") or []:
                items.append({
                    "id": str(t.get("id") or t.get("reestr_number") or len(items)),
                    "title": str(t.get("name") or "")[:200],
                    "amount": t.get("budget"),
                    "date": str(t.get("deadline") or ""),
                    "customer": str(t.get("customer") or ""),
                    "url": str(t.get("external_url") or ""),
                    "source": "tenderguru_plan",
                    "role": "customer",
                    "status": "current",
                })
    except Exception as exc:
        err = ((err + "; ") if err else "") + str(exc)[:120]
    try:
        track_api("tenderguru", count=max(n, 1))
    except Exception:
        pass
    current = [x for x in items if x.get("status") == "current"][:_MAX]
    return current or items[:_MAX], [usage_row(
        "tenderguru", requests=n, billed="requests", hits=len(items),
        note="API TenderGuru, не токены", error=err,
    )]


async def default_datanewton_stat(inn: str) -> tuple[dict, list[dict]]:
    if not str(inn or "").strip():
        return {}, [usage_row("datanewton", requests=0, billed="skipped", note="нет ИНН")]
    key = str(os.getenv("DATANEWTON_API_KEY") or "").strip()
    if not key:
        return {}, [usage_row("datanewton", requests=0, billed="skipped", note="нет ключа")]
    import httpx
    from services.datanewton import DataNewtonClient

    client = DataNewtonClient(key)
    try:
        extra: dict[str, Any] = {}
        async with httpx.AsyncClient(timeout=client.timeout) as http:
            gcs = await client.gov_contracts_stat(http, inn=inn)
        try:
            track_api("datanewton")
        except Exception:
            pass
        if isinstance(gcs, dict) and gcs:
            extra = {
                "as_customer_total": gcs.get("totalContracts") or gcs.get("total_contracts") or gcs.get("total"),
                "as_customer_sum": gcs.get("totalSum") or gcs.get("total_sum") or gcs.get("sum"),
                "as_customer_last_year": gcs.get("last_year_contracts") or gcs.get("lastYearContracts"),
            }
        hits = 1 if extra else 0
        return extra, [usage_row("datanewton", requests=1, billed="free_requests", hits=hits, note="бесплатный API, не токены")]
    except Exception as exc:
        return {}, [usage_row("datanewton", requests=1, billed="free_requests", error=str(exc)[:120])]


async def default_checko_live(inn: str, already_has_past: bool) -> tuple[list[dict], list[dict]]:
    if already_has_past:
        return [], []
    if not str(inn or "").strip():
        return [], [usage_row("checko", requests=0, billed="skipped", note="нет ИНН")]
    from leadgen.modules.checko import fetch_contracts

    try:
        data = await fetch_contracts(inn, limit=_MAX)
        items = contracts_from_checko({"financials": data if isinstance(data, dict) else {}})
        try:
            track_api("checko")
        except Exception:
            pass
        return items, [usage_row("checko", requests=1, billed="requests", hits=len(items), note="квота Checko /contracts")]
    except Exception as exc:
        return [], [usage_row("checko", requests=1, billed="requests", error=str(exc)[:120])]
