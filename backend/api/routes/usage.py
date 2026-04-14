"""
API Usage — статистика использования всех внешних API и лимиты.

GET  /api/usage/stats          — все счётчики + лимиты
GET  /api/usage/live           — живые данные от Hunter, Apollo (текущие остатки)
POST /api/usage/reset/{service} — сброс счётчика
POST /api/usage/reset_all      — сброс всего
"""
from __future__ import annotations

import asyncio
import logging
import os
import time

import httpx
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/usage", tags=["usage"])


# ── Живые лимиты от провайдеров ───────────────────────────────────────────────

async def _hunter_account() -> dict:
    """GET /v2/account — узнаём остаток запросов Hunter.io."""
    key = os.getenv("HUNTER_API_KEY", "")
    if not key or key == "your_hunter_api_key":
        return {"available": False, "error": "HUNTER_API_KEY не задан"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get("https://api.hunter.io/v2/account", params={"api_key": key})
            if r.status_code != 200:
                return {"available": False, "error": f"HTTP {r.status_code}"}
            d = r.json().get("data", {})
            req = d.get("requests", {})
            searches = req.get("searches", {})
            verif = req.get("verifications", {})
            return {
                "available": True,
                "plan": d.get("plan_name", "?"),
                "searches_used": searches.get("used", 0),
                "searches_available": searches.get("available", 0),
                "verifications_used": verif.get("used", 0),
                "verifications_available": verif.get("available", 0),
                "first_name": d.get("first_name", ""),
                "email": d.get("email", ""),
            }
    except Exception as e:
        return {"available": False, "error": str(e)}


async def _apollo_account() -> dict:
    """Apollo.io — проверяем аккаунт через /api/v1/auth/health."""
    key = os.getenv("APOLLO_API_KEY", "")
    if not key or key == "your_apollo_api_key":
        return {"available": False, "error": "APOLLO_API_KEY не задан"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(
                "https://api.apollo.io/api/v1/auth/health",
                headers={"X-Api-Key": key, "Cache-Control": "no-cache"},
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    "available": True,
                    "status": d.get("status", "ok"),
                    "is_logged_in": d.get("is_logged_in", False),
                    "message": d.get("message", ""),
                }
            return {"available": False, "error": f"HTTP {r.status_code}: {r.text[:100]}"}
    except Exception as e:
        return {"available": False, "error": str(e)}


async def _groq_models() -> dict:
    """Groq — проверяем доступные модели."""
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return {"available": False, "error": "GROQ_API_KEY не задан"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            if r.status_code == 200:
                models = [m["id"] for m in r.json().get("data", [])]
                current = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
                return {
                    "available": True,
                    "current_model": current,
                    "models_count": len(models),
                    "models": models[:10],
                }
            return {"available": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"available": False, "error": str(e)}


async def _checko_status() -> dict:
    """Checko — проверяем доступность ключа."""
    key = os.getenv("CHECKO_API_KEY", "")
    if not key:
        return {"available": False, "error": "CHECKO_API_KEY не задан"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(
                "https://api.checko.ru/v2/company",
                params={"key": key, "inn": "7736207543"},  # Сбербанк — тест
            )
            if r.status_code == 200:
                return {"available": True, "status": "ok"}
            return {"available": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"available": False, "error": str(e)}


def _env_key_status(env_var: str, dummy: str = "") -> str:
    """Возвращает: 'set' | 'missing' | 'dummy'."""
    v = os.getenv(env_var, "")
    if not v:
        return "missing"
    if dummy and v == dummy:
        return "dummy"
    return "set"


# ── Эндпоинты ─────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    """Все счётчики использования + лимиты + статус ключей."""
    from core.stats import get_all, KNOWN_LIMITS

    counters = get_all()
    result = []

    # Объединяем известные сервисы + те что уже есть в счётчиках
    all_services = set(KNOWN_LIMITS.keys()) | set(counters.keys())

    alerts: list[dict] = []

    for svc in sorted(all_services):
        limits = KNOWN_LIMITS.get(svc, {})
        c = counters.get(svc, {})

        entry = {
            "service": svc,
            "name": limits.get("name", svc),
            "plan": limits.get("plan", "unknown"),
            "reset": limits.get("reset", "?"),
            "docs": limits.get("docs", ""),
            # Счётчики
            "calls_today": c.get("calls_today", 0),
            "calls_month": c.get("calls_month", 0),
            "calls_total": c.get("calls_total", 0),
            "tokens_prompt_today": c.get("tokens_prompt_today", 0),
            "tokens_completion_today": c.get("tokens_completion_today", 0),
            "tokens_prompt_month": c.get("tokens_prompt_month", 0),
            "tokens_completion_month": c.get("tokens_completion_month", 0),
            "tokens_total": c.get("tokens_total", 0),
            "errors_today": c.get("errors_today", 0),
            "last_used": c.get("last_used"),
            # Лимиты
            "limit_day_calls": limits.get("limit_day_calls"),
            "limit_month_calls": limits.get("limit_month_calls"),
            "limit_day_tokens": limits.get("limit_day_tokens"),
            "limit_month_tokens": limits.get("limit_month_tokens"),
            # Статус ключа (None для локальных сервисов без API-ключа)
            "key_status": _env_key_status(_key_env(svc)) if _key_env(svc) else None,
        }

        # Процент использования
        if limits.get("limit_day_calls") and c.get("calls_today", 0):
            entry["pct_day"] = round(c["calls_today"] / limits["limit_day_calls"] * 100, 1)
        elif limits.get("limit_month_calls") and c.get("calls_month", 0):
            entry["pct_month"] = round(c["calls_month"] / limits["limit_month_calls"] * 100, 1)
        elif limits.get("limit_day_tokens") and (c.get("tokens_prompt_today", 0) + c.get("tokens_completion_today", 0)):
            total_t = c["tokens_prompt_today"] + c["tokens_completion_today"]
            entry["pct_day"] = round(total_t / limits["limit_day_tokens"] * 100, 1)

        _append_alerts_for_service(alerts, entry)
        result.append(entry)

    summary = {
        "services_total": len(result),
        "alerts_total": len(alerts),
        "critical_total": len([a for a in alerts if a["level"] == "critical"]),
        "warning_total": len([a for a in alerts if a["level"] == "warning"]),
        "last_calculated_ts": int(time.time()),
    }
    return {"status": "ok", "services": result, "alerts": alerts, "summary": summary}


@router.get("/live")
async def get_live():
    """Живые данные от провайдеров (Hunter, Apollo, Groq, Checko)."""
    hunter, apollo, groq, checko = await asyncio.gather(
        _hunter_account(),
        _apollo_account(),
        _groq_models(),
        _checko_status(),
        return_exceptions=True,
    )

    def safe(x):
        return x if isinstance(x, dict) else {"available": False, "error": str(x)}

    checko_live = safe(checko)
    try:
        from leadgen.modules.checko import get_runtime_state
        checko_live["runtime"] = get_runtime_state()
    except Exception:
        checko_live["runtime"] = {}

    return {
        "status": "ok",
        "hunter": safe(hunter),
        "apollo": safe(apollo),
        "groq": safe(groq),
        "checko": checko_live,
    }


@router.post("/reset/{service}")
async def reset_service(service: str):
    from core.stats import reset_service as _reset
    _reset(service)
    return {"status": "ok", "reset": service}


@router.post("/reset_all")
async def reset_all():
    from core.stats import reset_all as _reset_all
    _reset_all()
    return {"status": "ok"}


# ── Утилиты ───────────────────────────────────────────────────────────────────

def _key_env(service: str) -> str:
    """Возвращает имя переменной окружения для API-ключа сервиса."""
    return {
        "groq": "GROQ_API_KEY",
        "newsapi": "NEWS_API_KEY",
        "tavily": "TAVILY_API_KEY",
        "brave": "BRAVE_API_KEY",
        "hunter": "HUNTER_API_KEY",
        "apollo": "APOLLO_API_KEY",
        "checko": "CHECKO_API_KEY",
        "builtwith": "BUILTWITH_API_KEY",
        "ollama": "",
    }.get(service, "")


def _append_alerts_for_service(alerts: list[dict], entry: dict) -> None:
    svc = entry.get("service")
    name = entry.get("name", svc)
    pct = entry.get("pct_day")
    if pct is None:
        pct = entry.get("pct_month")

    if pct is not None:
        if pct >= 100:
            alerts.append({
                "service": svc,
                "level": "critical",
                "code": "limit_exceeded",
                "message": f"{name}: лимит превышен ({pct}%).",
            })
        elif pct >= 90:
            alerts.append({
                "service": svc,
                "level": "critical",
                "code": "limit_critical",
                "message": f"{name}: критично близко к лимиту ({pct}%).",
            })
        elif pct >= 70:
            alerts.append({
                "service": svc,
                "level": "warning",
                "code": "limit_warning",
                "message": f"{name}: высокий расход ({pct}%).",
            })

    if (entry.get("errors_today") or 0) > 0:
        alerts.append({
            "service": svc,
            "level": "warning",
            "code": "errors_today",
            "message": f"{name}: ошибок сегодня {entry.get('errors_today')}.",
        })
