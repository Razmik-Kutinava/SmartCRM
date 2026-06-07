"""
Клиент Public API «Мои-Закупки» (КТРУ, ОКПД-2).
https://moy-zakupki.ru/api/public/v2 — заголовок Authorization: Api-Key <ключ>

Кэш на диске снижает расход месячной квоты. Реальные HTTP-вызовы учитываются в core.stats.track_api("moy_zakupki").
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://moy-zakupki.ru/api/public/v2"
_CACHE_DIR: Path | None = None


def _cache_root() -> Path:
    global _CACHE_DIR
    if _CACHE_DIR is None:
        base = Path(__file__).resolve().parent.parent / "data" / "moy_zakupki_cache"
        base.mkdir(parents=True, exist_ok=True)
        _CACHE_DIR = base
    return _CACHE_DIR


def _ttl_seconds() -> float:
    try:
        days = float(os.getenv("MOY_ZAKUPKI_CACHE_TTL_DAYS", "14"))
    except ValueError:
        days = 14.0
    return max(3600.0, days * 86400.0)


def _cache_key(kind: str, payload: str) -> str:
    h = hashlib.sha256(f"{kind}:{payload}".encode("utf-8")).hexdigest()[:32]
    return h


def _cache_get(key: str) -> dict | list | None:
    path = _cache_root() / f"{key}.json"
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        ts = raw.get("_ts", 0)
        if time.time() - ts > _ttl_seconds():
            path.unlink(missing_ok=True)
            return None
        return raw.get("data")
    except Exception as e:
        logger.debug("moy_zakupki cache read: %s", e)
        return None


def _cache_set(key: str, data: dict | list) -> None:
    path = _cache_root() / f"{key}.json"
    try:
        path.write_text(
            json.dumps({"_ts": time.time(), "data": data}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.debug("moy_zakupki cache write: %s", e)


def _api_key() -> str:
    return (os.getenv("MOY_ZAKUPKI_API_KEY") or "").strip()


def _headers() -> dict[str, str]:
    k = _api_key()
    if not k:
        return {}
    return {"Authorization": f"Api-Key {k}"}


def _track(ok: bool) -> None:
    try:
        from core.stats import track_api

        if ok:
            track_api("moy_zakupki")
        else:
            track_api("moy_zakupki", error=True)
    except Exception:
        pass


async def _http_get(path: str, params: dict[str, Any] | None = None, use_cache: bool = True) -> dict | list:
    """GET с кэшем. path без base, с ведущим /."""
    key = _api_key()
    if not key:
        raise RuntimeError("MOY_ZAKUPKI_API_KEY не задан")

    params = {k: v for k, v in (params or {}).items() if v is not None}
    sort_key = json.dumps({"p": path, "q": params}, sort_keys=True, ensure_ascii=True)
    ck = _cache_key("GET", sort_key)
    if use_cache:
        hit = _cache_get(ck)
        if hit is not None:
            return hit

    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.get(url, headers=_headers(), params=params)
    except Exception as e:
        logger.warning("moy_zakupki GET %s: %s", path, e)
        _track(False)
        raise

    if r.status_code == 429:
        _track(False)
        raise httpx.HTTPStatusError("rate limited", request=r.request, response=r)
    if r.status_code >= 400:
        _track(False)
        r.raise_for_status()

    data = r.json()
    _track(True)
    if use_cache:
        _cache_set(ck, data if isinstance(data, (dict, list)) else {"_raw": data})
    return data


async def _http_post(path: str, body: dict[str, Any], use_cache: bool = True) -> dict | list:
    key = _api_key()
    if not key:
        raise RuntimeError("MOY_ZAKUPKI_API_KEY не задан")

    sort_key = json.dumps({"p": path, "b": body}, sort_keys=True, ensure_ascii=True)
    ck = _cache_key("POST", sort_key)
    if use_cache:
        hit = _cache_get(ck)
        if hit is not None:
            return hit

    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                url,
                headers={**_headers(), "Content-Type": "application/json"},
                json=body,
            )
    except Exception as e:
        logger.warning("moy_zakupki POST %s: %s", path, e)
        _track(False)
        raise

    if r.status_code == 429:
        _track(False)
        raise httpx.HTTPStatusError("rate limited", request=r.request, response=r)
    if r.status_code >= 400:
        _track(False)
        r.raise_for_status()

    data = r.json()
    _track(True)
    if use_cache:
        _cache_set(ck, data if isinstance(data, (dict, list)) else {"_raw": data})
    return data


# ── Публичные методы API (соответствуют документации) ──────────────────────────


async def okpd2_list(
    page: int = 1,
    per_page: int = 15,
    level: int | None = None,
    is_actual: bool | None = True,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "per_page": min(per_page, 50)}
    if level is not None:
        params["level"] = level
    if is_actual is not None:
        params["is_actual"] = str(is_actual).lower()
    raw = await _http_get("/okpd2/", params)
    return raw if isinstance(raw, dict) else {"results": [], "count": 0}


async def okpd2_detail(code: str) -> dict[str, Any]:
    code_s = (code or "").strip().strip("/")
    if not code_s:
        raise ValueError("code пустой")
    raw = await _http_get(f"/okpd2/{code_s}/", {})
    return raw if isinstance(raw, dict) else {}


async def ktru_list(
    page: int = 1,
    per_page: int = 15,
    status: str | None = None,
    is_enlarged: bool | None = None,
    okpd2_code: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "per_page": min(per_page, 50)}
    if status:
        params["status"] = status
    if is_enlarged is not None:
        params["is_enlarged"] = str(is_enlarged).lower()
    if okpd2_code:
        params["okpd2_code"] = okpd2_code
    raw = await _http_get("/ktru/", params)
    return raw if isinstance(raw, dict) else {"results": [], "count": 0}


async def ktru_detail(code: str) -> dict[str, Any]:
    code_s = (code or "").strip().strip("/")
    if not code_s:
        raise ValueError("code пустой")
    raw = await _http_get(f"/ktru/{code_s}/", {})
    return raw if isinstance(raw, dict) else {}


async def ktru_search(body: dict[str, Any]) -> dict[str, Any] | list:
    raw = await _http_post("/ktru/search/", body)
    return raw if isinstance(raw, (dict, list)) else {}


# ── Обёртка для параллельного веб-поиска (rag/search) ────────────────────────

_OKPD_RE = re.compile(r"(?:^|\s|\b)(\d{2}\.\d{2}(?:\.\d{2})?(?:\.\d{2})?(?:\.\d{2})?)\b")


async def search_hints_for_query(query: str, max_results: int = 8) -> list[dict]:
    """
    Преобразует ответы КТРУ/ОКПД-2 в формат результатов поиска (title, snippet, url, source).
    """
    if not _api_key():
        return []

    q = (query or "").strip()
    if not q:
        return []

    out: list[dict] = []

    m = _OKPD_RE.search(q)
    if m:
        code = m.group(1)
        try:
            detail = await okpd2_detail(code)
            name = (detail.get("name") or "").strip()
            children = detail.get("children") or []
            ch_preview = ""
            if isinstance(children, list) and children:
                ch_preview = "; ".join(
                    f'{c.get("code","")} {c.get("name","")}' for c in children[:5] if isinstance(c, dict)
                )
            snippet = f"ОКПД-2: {name}"
            if detail.get("parent_code"):
                snippet += f" · родитель: {detail.get('parent_code')}"
            if ch_preview:
                snippet += f" · дочерние: {ch_preview[:500]}"
            out.append({
                "title": f"ОКПД-2 {code}" + (f" — {name}" if name else ""),
                "snippet": snippet[:700],
                "url": f"https://moy-zakupki.ru/?okpd={code}",
                "date": "",
                "source": "moy_zakupki",
            })
        except Exception as e:
            logger.debug("moy_zakupki okpd2_detail: %s", e)

    if len(out) >= max_results:
        return out[:max_results]

    # Если уже нашли карточку ОКПД по коду в запросе — второй вызов (КТРУ search) не делаем (квота).
    if m and out:
        return out[:max_results]

    try:
        raw = await ktru_search({
            "characteristics": [q[:500]],
            "status": "Включено в КТРУ",
            "is_enlarged": False,
        })
    except Exception as e:
        logger.warning("moy_zakupki ktru_search: %s", e)
        return out[:max_results]

    results = []
    if isinstance(raw, dict):
        results = raw.get("results") or raw.get("data") or []
    elif isinstance(raw, list):
        results = raw

    for item in results[: max_results - len(out)]:
        if not isinstance(item, dict):
            continue
        code = (item.get("code") or "").strip()
        name = (item.get("name") or item.get("shortname") or "").strip()
        okpd_c = (item.get("okpd2_code") or "").strip()
        okpd_n = (item.get("okpd2_name") or "").strip()
        snippet = f"КТРУ {code}"
        if okpd_c:
            snippet += f" · ОКПД-2: {okpd_c}"
        if okpd_n:
            snippet += f" ({okpd_n})"
        if item.get("unit_name"):
            snippet += f" · ед.: {item.get('unit_name')}"
        out.append({
            "title": name or f"КТРУ {code}",
            "snippet": snippet[:700],
            "url": f"https://moy-zakupki.ru/?ktru={code}" if code else "https://moy-zakupki.ru/",
            "date": "",
            "source": "moy_zakupki",
        })

    return out[:max_results]


async def fetch_classifier_hints(q: str, okpd: str | None) -> dict[str, Any]:
    """Для ответа /api/tenders/search: подсказки по классификаторам (с кэшем)."""
    if not _api_key():
        return {"enabled": False, "error": "MOY_ZAKUPKI_API_KEY не задан"}

    hints: dict[str, Any] = {"enabled": True}
    okpd_code = (okpd or "").strip()
    if not okpd_code:
        m = _OKPD_RE.search(q or "")
        if m:
            okpd_code = m.group(1)

    if okpd_code:
        try:
            hints["okpd2"] = await okpd2_detail(okpd_code)
        except Exception as e:
            hints["okpd2_error"] = str(e)

    try:
        raw = await ktru_search({
            "characteristics": [(q or "закупка")[:400]],
            "status": "Включено в КТРУ",
            "is_enlarged": False,
        })
        if isinstance(raw, list):
            hints["ktru_search"] = {"results": raw}
        elif isinstance(raw, dict):
            hints["ktru_search"] = raw if raw.get("results") is not None else {"results": []}
    except Exception as e:
        hints["ktru_search_error"] = str(e)

    return hints
