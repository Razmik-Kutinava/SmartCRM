"""
Checko API v2.4 — полная интеграция.
https://api.checko.ru/v2/

Реальная структура ответа /company (поля ЕГРЮЛ):
  ИНН, КПП, ОГРН, НаимСокр, НаимПолн, ДатаРег
  Статус: {Код, Наим}          ("Действует" / "Ликвидировано" / ...)
  Регион: {Код, Наим}
  ЮрАдрес: {НасПункт, АдресРФ, Недост, ...}
  ОКВЭД: {Код, Наим, Версия}
  Руковод: [{ФИО, НаимДолжн, ОгрДоступ, ДисквЛицо, ...}]
  Учред: {ФЛ: [{ФИО, ИНН, Доля, ...}], РосОрг: [{НаимСокр, ИНН, Доля, ...}]}
  Контакты: {Тел: [...], Эмейл: [...]}
  Лиценз: [{Номер, Дата, ВидДеят: [...]}]
  Булевы флаги риска: НедобросПоставщик, МассРуковод, МассАдрес и др.

Финансы /finances:
  data: {"2023": {"2110": revenue, "2400": profit, "1600": assets, "1520": debt, ...}}

ENV: CHECKO_API_KEY (лайт = 100 запросов/сутки)
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE = "https://api.checko.ru/v2"
TIMEOUT = 12.0
_CACHE_FILE = Path("data/checko_cache.json")
_CACHE_TTL_SECONDS = int(os.getenv("CHECKO_CACHE_TTL_SECONDS", "86400"))  # 24h
_BREAKER_THRESHOLD = int(os.getenv("CHECKO_BREAKER_THRESHOLD", "5"))
_BREAKER_COOLDOWN_SECONDS = int(os.getenv("CHECKO_BREAKER_COOLDOWN_SECONDS", "900"))  # 15m

_cache_lock = threading.Lock()
_cache: dict[str, dict[str, Any]] = {}
_forbidden_streak = 0
_blocked_until = 0.0


def _cache_load() -> None:
    global _cache
    try:
        if _CACHE_FILE.exists():
            _cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("Checko cache load failed: %s", e)
        _cache = {}


def _cache_save() -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.debug("Checko cache save failed: %s", e)


def _cache_key(path: str, params: dict | None) -> str:
    base_params = dict(params or {})
    base_params.pop("key", None)
    payload = json.dumps({"path": path, "params": base_params}, sort_keys=True, ensure_ascii=False)
    return payload


def _cache_get(key: str) -> dict | list | None:
    now = time.time()
    with _cache_lock:
        row = _cache.get(key)
        if not row:
            return None
        exp = float(row.get("expires_at", 0))
        if exp <= now:
            _cache.pop(key, None)
            return None
        return row.get("body")


def _cache_put(key: str, body: dict | list) -> None:
    with _cache_lock:
        _cache[key] = {
            "expires_at": time.time() + _CACHE_TTL_SECONDS,
            "body": body,
        }
        _cache_save()


def _breaker_is_open() -> bool:
    return time.time() < _blocked_until


def _breaker_record_forbidden() -> None:
    global _forbidden_streak, _blocked_until
    _forbidden_streak += 1
    if _forbidden_streak >= _BREAKER_THRESHOLD:
        _blocked_until = time.time() + _BREAKER_COOLDOWN_SECONDS
        logger.warning(
            "Checko breaker OPEN for %ss after %s consecutive 403",
            _BREAKER_COOLDOWN_SECONDS,
            _forbidden_streak,
        )


def _breaker_record_success() -> None:
    global _forbidden_streak, _blocked_until
    _forbidden_streak = 0
    _blocked_until = 0.0


def get_runtime_state() -> dict[str, Any]:
    """Текущее состояние кэша/брейкера для мониторинга в Ops."""
    now = time.time()
    with _cache_lock:
        cache_items = len(_cache)
    blocked_for = max(0.0, _blocked_until - now)
    return {
        "cache_enabled": True,
        "cache_ttl_seconds": _CACHE_TTL_SECONDS,
        "cache_items": cache_items,
        "breaker_open": blocked_for > 0,
        "breaker_forbidden_streak": _forbidden_streak,
        "breaker_blocked_for_seconds": int(blocked_for),
        "breaker_threshold": _BREAKER_THRESHOLD,
    }


def _key() -> str:
    return os.getenv("CHECKO_API_KEY", "")


def _available() -> bool:
    return bool(_key())


async def _get(path: str, params: dict | None = None) -> dict | list | None:
    """Базовый GET с авторизацией и обработкой лимита."""
    if not _available():
        return None
    p = {"key": _key(), **(params or {})}
    ck = _cache_key(path, p)
    cached = _cache_get(ck)
    if cached is not None:
        return cached
    if _breaker_is_open():
        logger.warning("Checko breaker active, skip %s", path)
        return None
    try:
        from core.stats import track_api
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(f"{BASE}{path}", params=p)
            if r.status_code == 403:
                _breaker_record_forbidden()
                track_api("checko", error=True)
                logger.warning("Checko forbidden on %s", path)
                return None
            if r.status_code == 429:
                logger.warning("Checko: rate limit (100/day exhausted)")
                track_api("checko", error=True)
                return None
            if r.status_code == 404:
                track_api("checko")
                return None
            r.raise_for_status()
            body = r.json()
            # Checko всегда возвращает meta с message — проверим на ошибку
            meta = body.get("meta") or {}
            if meta.get("status") == "error":
                logger.warning("Checko API error: %s", meta.get("message"))
                track_api("checko", error=True)
                return None
            _breaker_record_success()
            track_api("checko")
            _cache_put(ck, body)
            return body
    except Exception as e:
        logger.warning("Checko %s failed: %s", path, e)
        return None


_cache_load()


# ══════════════════════════════════════════════════════════════════════════════
# /company — основные данные ЕГРЮЛ
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_company(inn: str) -> dict | None:
    """
    Полные данные организации по ИНН.
    Возвращает нормализованный словарь совместимый с dadata._parse_suggestion.
    """
    body = await _get("/company", {"inn": inn})
    if not body:
        return None
    raw = body.get("data") or {}
    if not raw:
        return None
    return _parse_company(raw)


async def search_companies(query: str, count: int = 5) -> list[dict]:
    """
    Поиск организаций по названию через egrul.nalog.ru (бесплатно, без ключа).
    Checko /search не работает на свободном тарифе.
    После получения ИНН — обогащаем через Checko /company.
    """
    rows = await _search_egrul_rows(query, count)
    if not rows:
        return []

    inns = []
    for row in rows[:count]:
        inn = row.get("i") or row.get("inn") or row.get("ИНН") or ""
        if inn:
            inns.append(str(inn))

    # Если ключа Checko нет — возвращаем минимальные данные из ЕГРЮЛ rows.
    if not _available():
        parsed = [_parse_search_item(r) for r in rows[:count]]
        return [p for p in parsed if p]

    import asyncio
    results = await asyncio.gather(
        *[fetch_company(inn) for inn in inns[:count]],
        return_exceptions=True,
    )
    out: list[dict] = []
    for idx, r in enumerate(results):
        if isinstance(r, dict) and r:
            out.append(r)
        else:
            # fallback на минимальные данные из ЕГРЮЛ, если Checko не отдал карточку
            if idx < len(rows):
                p = _parse_search_item(rows[idx])
                if p:
                    out.append(p)
    return out


async def _search_egrul(query: str, count: int = 5) -> list[str]:
    rows = await _search_egrul_rows(query, count)
    inns = []
    for row in rows[:count]:
        inn = row.get("i") or row.get("inn") or row.get("ИНН") or ""
        if inn:
            inns.append(str(inn))
    return inns


async def _search_egrul_rows(query: str, count: int = 5) -> list[dict]:
    """
    Поиск в ЕГРЮЛ по названию → сырые rows.
    Нужен для fallback, когда Checko API ключ не задан.
    """
    try:
        import asyncio
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://egrul.nalog.ru/",
                data={"query": query, "region": "", "page": ""},
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code != 200:
                # Fallback: GET с query
                r = await client.get(
                    "https://egrul.nalog.ru/search-result",
                    params={"query": query, "region": "", "page": ""},
                    headers={"Accept": "application/json"},
                )
            if r.status_code != 200:
                return []
            try:
                data = r.json()
            except Exception:
                return []

            # ЕГРЮЛ может вернуть token t, а строки будут доступны по /search-result/{t}
            rows = []
            if isinstance(data, dict):
                rows = data.get("rows") or []
                token = data.get("t")
                if not rows and token:
                    for _ in range(4):
                        await asyncio.sleep(0.8)
                        rr = await client.get(
                            f"https://egrul.nalog.ru/search-result/{token}",
                            headers={"Accept": "application/json"},
                        )
                        if rr.status_code != 200:
                            continue
                        try:
                            token_data = rr.json()
                        except Exception:
                            continue
                        if token_data.get("status") == "wait":
                            continue
                        rows = token_data.get("rows") or []
                        if rows:
                            break
            elif isinstance(data, list):
                rows = data

            return rows[:count]
    except Exception as e:
        logger.warning("EGRUL search failed for '%s': %s", query, e)
        return []


def _parse_search_item(item: dict) -> dict | None:
    """Парсит элемент из списка /search — формат проще чем /company."""
    if not isinstance(item, dict):
        return None
    inn = item.get("ИНН") or item.get("inn") or item.get("i") or ""
    if not inn:
        return None
    address_raw = item.get("ЮрАдрес") or item.get("address") or item.get("g") or ""
    name_full = item.get("НаимПолн") or item.get("name") or item.get("n") or ""
    name_short = item.get("НаимСокр") or item.get("c") or name_full

    return {
        "inn": inn,
        "kpp": item.get("КПП") or item.get("kpp") or item.get("p") or "",
        "ogrn": item.get("ОГРН") or item.get("ogrn") or item.get("o") or "",
        "name": name_full or name_short,
        "name_short": name_short or "",
        "okved": _str_from_field(item.get("ОКВЭД")),
        "okved_name": "",
        "status": _parse_status(item.get("Статус")),
        "registration_date": item.get("ДатаРег") or item.get("r"),
        "liquidation_date": item.get("ДатаЛикв"),
        "address": address_raw,
        "city": _extract_city(address_raw),
        "director": "",
        "director_post": "",
        "founders": [],
        "employees_count": None,
        "website": "",
        "branch_count": 0,
        "management_type": "hired_director",
        "revenue": None, "income": None, "expense": None,
        "debt": None, "finance_year": None,
        "dadata_emails": [], "dadata_phones": [],
        "smb_category": None, "licenses": [],
        "_source": "checko",
    }


def _parse_company(d: dict) -> dict | None:
    """
    Нормализует ответ Checko /company (поля ЕГРЮЛ).
    Ключи API — кириллица, структура задокументирована выше.
    """
    if not d:
        return None

    # ─── Идентификаторы ──────────────────────────────────────────────────────
    inn = d.get("ИНН") or ""
    kpp = d.get("КПП") or ""
    ogrn = d.get("ОГРН") or ""

    # ─── Название ────────────────────────────────────────────────────────────
    name = d.get("НаимПолн") or d.get("НаимСокр") or ""
    name_short = d.get("НаимСокр") or ""

    # ─── Статус ──────────────────────────────────────────────────────────────
    status = _parse_status(d.get("Статус"))
    reg_date = d.get("ДатаРег") or d.get("ДатаОГРН") or None

    # ─── Адрес ───────────────────────────────────────────────────────────────
    yur = d.get("ЮрАдрес") or {}
    if isinstance(yur, dict):
        address = yur.get("АдресРФ") or yur.get("НасПункт") or ""
        city_raw = yur.get("НасПункт") or ""
    else:
        address = str(yur)
        city_raw = ""

    # Регион как fallback для города
    region = d.get("Регион") or {}
    city = _clean_city(city_raw) or (region.get("Наим") if isinstance(region, dict) else "") or ""

    # ─── ОКВЭД ───────────────────────────────────────────────────────────────
    okved_raw = d.get("ОКВЭД") or {}
    if isinstance(okved_raw, dict):
        okved = okved_raw.get("Код") or ""
        okved_name = okved_raw.get("Наим") or ""
    else:
        okved = str(okved_raw) if okved_raw else ""
        okved_name = ""

    # ─── Руководитель ────────────────────────────────────────────────────────
    director_full = ""
    director_post = ""
    has_disqualified = False

    rukovod = d.get("Руковод") or []
    if rukovod and isinstance(rukovod, list):
        for r in rukovod:
            if not isinstance(r, dict):
                continue
            if r.get("ДисквЛицо"):
                has_disqualified = True
            fio = r.get("ФИО")
            if fio and isinstance(fio, str):
                director_full = fio.strip()
                director_post = (r.get("НаимДолжн") or "Генеральный директор").strip()
                break
            elif fio and isinstance(fio, dict):
                parts = [fio.get("Фамилия", ""), fio.get("Имя", ""), fio.get("Отчество", "")]
                director_full = " ".join(p for p in parts if p).strip()
                director_post = (r.get("НаимДолжн") or "Генеральный директор").strip()
                break

    # ─── Учредители ──────────────────────────────────────────────────────────
    uchred = d.get("Учред") or {}
    founders: list[dict] = []

    # Физлица
    for fl in (uchred.get("ФЛ") or []):
        if not isinstance(fl, dict):
            continue
        fio = fl.get("ФИО") or ""
        inn_fl = fl.get("ИНН") or ""
        doля = fl.get("Доля") or {}
        pct = _num(doля.get("Процент") if isinstance(doля, dict) else None)
        founders.append({
            "name": str(fio).strip() if fio else "",
            "type": "INDIVIDUAL",
            "inn": inn_fl,
            "share_percent": pct,
        })

    # Российские юрлица
    for ro in (uchred.get("РосОрг") or []):
        if not isinstance(ro, dict):
            continue
        fname = ro.get("НаимСокр") or ro.get("НаимПолн") or ""
        inn_ro = ro.get("ИНН") or ""
        doля = ro.get("Доля") or {}
        pct = _num(doля.get("Процент") if isinstance(doля, dict) else None)
        if fname or inn_ro:
            founders.append({
                "name": str(fname).strip(),
                "type": "LEGAL",
                "inn": inn_ro,
                "share_percent": pct,
            })

    # Иностранные
    for ino in (uchred.get("ИнОрг") or []):
        if not isinstance(ino, dict):
            continue
        fname = ino.get("НаимПолн") or ino.get("НаимСокр") or ""
        if fname:
            founders.append({"name": str(fname).strip(), "type": "FOREIGN", "inn": "", "share_percent": None})

    # ─── Контакты ────────────────────────────────────────────────────────────
    contacts = d.get("Контакты") or {}
    if isinstance(contacts, dict):
        phones: list[str] = []
        emails: list[str] = []
        website = ""
        for _k, _v in contacts.items():
            _kl = _k.lower()
            if "тел" in _kl or "phone" in _kl:
                _lst = _v if isinstance(_v, list) else ([_v] if _v else [])
                phones = [str(t) for t in _lst if t]
            elif "мейл" in _kl or "mail" in _kl:
                # Ловим и "Эмейл" и "Емэйл" (разные кодпоинты Э/Е и е/э)
                _lst = _v if isinstance(_v, list) else ([_v] if _v else [])
                emails = [str(e) for e in _lst if e]
            elif "сайт" in _kl or "site" in _kl:
                if isinstance(_v, list):
                    website = _v[0] if _v else ""
                else:
                    website = str(_v) if _v else ""
        # VK/соцсети не используем как website
    else:
        phones, emails, website = [], [], ""

    # Если нет сайта — пробуем угадать из email (домен первого email)
    if not website and emails:
        domain_from_email = emails[0].split("@")[-1] if "@" in emails[0] else ""
        if domain_from_email and domain_from_email not in ("gmail.com", "mail.ru", "yandex.ru", "bk.ru"):
            website = domain_from_email

    # ─── Лицензии ────────────────────────────────────────────────────────────
    licenses = []
    for lic in (d.get("Лиценз") or []):
        if not isinstance(lic, dict):
            continue
        for act in (lic.get("ВидДеят") or []):
            if act:
                licenses.append(str(act))

    # ─── Филиалы ─────────────────────────────────────────────────────────────
    filials = d.get("Филиалы") or {}
    if isinstance(filials, dict):
        branch_count = len(filials.get("Филиал") or [])
    else:
        branch_count = 0

    # ─── Аффилированные компании (СвязУчред) — компании где ЭТА компания учредитель ───
    related: list[dict] = []
    for rel in (d.get("СвязУчред") or []):
        if not isinstance(rel, dict):
            continue
        r_inn = rel.get("ИНН") or ""
        r_name = rel.get("НаимСокр") or rel.get("НаимПолн") or ""
        r_status = _parse_status(rel.get("Статус") or "")
        if r_inn or r_name:
            related.append({
                "inn": r_inn,
                "ogrn": rel.get("ОГРН") or "",
                "name": r_name,
                "name_full": rel.get("НаимПолн") or r_name,
                "status": r_status,
                "reg_date": rel.get("ДатаРег") or "",
                "okved": rel.get("ОКВЭД") or "",
                "address": rel.get("ЮрАдрес") or "",
                "_relation": "дочерняя/аффилированная компания",
            })

    # ─── Риск-флаги ──────────────────────────────────────────────────────────
    is_bad_supplier = bool(d.get("НедобросПоставщик"))
    is_mass_addr = bool((yur.get("МассАдрес") if isinstance(yur, dict) else None))

    management_type = _detect_mgt(founders, director_full)

    return {
        "inn": inn,
        "kpp": kpp,
        "ogrn": ogrn,
        "name": name,
        "name_short": name_short,
        "okved": okved,
        "okved_name": okved_name,
        "status": status,
        "registration_date": reg_date,
        "liquidation_date": None,
        "address": address,
        "city": city,
        "director": director_full,
        "director_post": director_post,
        "founders": founders,
        "employees_count": None,
        "website": website or "",
        "branch_count": branch_count,
        "management_type": management_type,
        # Финансы (пустые — берём из /finances отдельно)
        "revenue": None,
        "income": None,
        "expense": None,
        "debt": None,
        "finance_year": None,
        # Контакты
        "dadata_emails": emails,
        "dadata_phones": phones,
        # Доп. поля
        "smb_category": None,
        "licenses": licenses,
        "has_disqualified_leader": has_disqualified,
        "is_bad_supplier": is_bad_supplier,
        "is_mass_address": is_mass_addr,
        "related_companies": related,   # компании где ЭТА компания — учредитель
        "_source": "checko",
    }


# ══════════════════════════════════════════════════════════════════════════════
# /finances — финансовая отчётность (Росстат + ГИР БО)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_finances(inn: str) -> dict:
    """
    Финансовая отчётность по ИНН.
    Формат: data.{year}.{code} где 2110=выручка, 2400=прибыль, 1600=активы, 1520=долг
    """
    body = await _get("/finances", {"inn": inn})
    if not body:
        return {}
    data = body.get("data") or {}
    if not data:
        return {}
    return _parse_finances(data)


def _parse_finances(data: dict | list) -> dict:
    """Парсим финансовые данные — коды строк бухотчётности по МСФО."""
    revenue_series: list[tuple[int, float]] = []
    profit_series: list[tuple[int, float]] = []
    assets_val = None
    expense_val = None
    debt_val = None

    if isinstance(data, dict):
        for year_key, yr_data in data.items():
            if not isinstance(yr_data, dict):
                continue
            try:
                yr = int(year_key)
            except (ValueError, TypeError):
                continue
            # Строки бухотчётности (РСБУ)
            rev = _num(yr_data.get("2110"))   # Выручка
            prof = _num(yr_data.get("2400"))  # Чистая прибыль
            assets = _num(yr_data.get("1600"))  # Баланс активов
            # Расходы: себестоимость + коммерч. + управленч.
            exp = _sum_num(yr_data.get("2120"), yr_data.get("2210"), yr_data.get("2220"))
            debt = _num(yr_data.get("1520"))  # Кредиторская задолженность

            if rev is not None:
                revenue_series.append((yr, rev))
            if prof is not None:
                profit_series.append((yr, prof))
            # Берём данные самого свежего года
            if assets is not None:
                assets_val = assets
            if exp is not None:
                expense_val = exp
            if debt is not None:
                debt_val = debt

    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            yr = _num(item.get("year") or item.get("Год"))
            if yr is None:
                continue
            yr = int(yr)
            rev = _num(item.get("2110") or item.get("revenue"))
            prof = _num(item.get("2400") or item.get("profit"))
            if rev is not None:
                revenue_series.append((yr, rev))
            if prof is not None:
                profit_series.append((yr, prof))

    # Сортируем по году (старые → новые)
    revenue_series.sort(key=lambda x: x[0])
    profit_series.sort(key=lambda x: x[0])

    revenue = revenue_series[-1][1] if revenue_series else None
    profit = profit_series[-1][1] if profit_series else None
    finance_year = revenue_series[-1][0] if revenue_series else None

    trend = "unknown"
    if len(revenue_series) >= 2:
        prev = revenue_series[-2][1] or 0
        curr = revenue_series[-1][1] or 0
        if curr > prev * 1.1:
            trend = "growing"
        elif curr < prev * 0.9:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "revenue": revenue,
        "profit": profit,
        "assets": assets_val,
        "expense": expense_val,
        "debt": debt_val,
        "finance_year": finance_year,
        "revenue_trend": trend,
        "revenue_series": revenue_series[-3:],
        "profit_series": profit_series[-3:],
    }


# ══════════════════════════════════════════════════════════════════════════════
# /legal-cases — арбитражные дела (КАД)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_legal_cases(inn: str) -> dict:
    body = await _get("/legal-cases", {"inn": inn})
    if not body:
        return {"arbitration_count": 0, "cases": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or data.get("cases") or [])

    parsed = []
    for c in items[:5]:
        if isinstance(c, dict):
            parsed.append({
                "number": c.get("number") or c.get("НомерДела") or "",
                "date": c.get("date") or c.get("ДатаПод") or "",
                "amount": _num(c.get("amount") or c.get("Сумма")),
                "role": c.get("role") or c.get("Роль") or "",
                "result": c.get("result") or c.get("Результат") or "",
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total") or data.get("count")) or total

    return {"arbitration_count": int(total), "cases": parsed}


# ══════════════════════════════════════════════════════════════════════════════
# /enforcements — исполнительные производства ФССП
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_enforcements(inn: str) -> dict:
    body = await _get("/enforcements", {"inn": inn})
    if not body:
        return {"enforcement_count": 0, "enforcement_debt": 0, "enforcements": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    total_debt = 0.0
    parsed = []
    for item in items[:5]:
        if isinstance(item, dict):
            amount = _num(item.get("amount") or item.get("Сумма") or 0) or 0
            total_debt += amount
            parsed.append({
                "number": item.get("number") or item.get("НомерИП") or "",
                "date": item.get("date") or item.get("Дата") or "",
                "amount": amount,
                "reason": item.get("reason") or item.get("Предмет") or "",
                "status": item.get("status") or item.get("Статус") or "",
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {
        "enforcement_count": int(total),
        "enforcement_debt": total_debt,
        "enforcements": parsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /contracts — госзакупки (44-ФЗ)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_contracts(inn: str, limit: int = 5) -> dict:
    body = await _get("/contracts", {
        "inn": inn, "law": "44", "role": "supplier", "sort": "-date"
    })
    if not body:
        return {"contracts_count": 0, "contracts_total_amount": 0, "contracts": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or data.get("contracts") or [])

    total_amount = 0.0
    parsed = []
    for c in items[:limit]:
        if isinstance(c, dict):
            amount = _num(c.get("price") or c.get("amount") or c.get("Цена") or 0) or 0
            total_amount += amount
            parsed.append({
                "number": c.get("number") or c.get("regNum") or c.get("РегНом") or "",
                "date": c.get("date") or c.get("signDate") or c.get("Дата") or "",
                "amount": amount,
                "customer": c.get("customer") or c.get("Заказчик") or "",
                "subject": (c.get("subject") or c.get("name") or c.get("Предмет") or "")[:120],
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {
        "contracts_count": int(total),
        "contracts_total_amount": total_amount,
        "contracts": parsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /bankruptcy-messages — банкротство (ЕФРСБ)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_bankruptcy(inn: str) -> dict:
    body = await _get("/bankruptcy-messages", {"inn": inn})
    if not body:
        return {"has_bankruptcy": False, "bankruptcy_messages": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    has_bankrupt = False
    messages = []
    for m in items[:3]:
        if isinstance(m, dict):
            msg_type = m.get("type") or m.get("Тип") or ""
            if any(kw in str(msg_type).lower() for kw in ("банкрот", "конкурс", "несостоят")):
                has_bankrupt = True
            messages.append({
                "type": msg_type,
                "date": m.get("date") or m.get("Дата") or "",
                "text": (m.get("text") or m.get("Содержание") or "")[:200],
            })

    return {
        "has_bankruptcy": has_bankrupt or bool(items),
        "bankruptcy_messages": messages,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /inspections — проверки Генпрокуратуры
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_inspections(inn: str) -> dict:
    body = await _get("/inspections", {"inn": inn})
    if not body:
        return {"inspection_count": 0, "inspections": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    parsed = []
    for item in items[:5]:
        if isinstance(item, dict):
            parsed.append({
                "authority": item.get("authority") or item.get("Орган") or "",
                "date": item.get("date") or item.get("Дата") or "",
                "result": item.get("result") or item.get("Результат") or "",
                "violations": bool(item.get("violations") or item.get("Нарушения")),
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {"inspection_count": int(total), "inspections": parsed}


# ══════════════════════════════════════════════════════════════════════════════
# /fedresurs — сообщения Федресурса
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_fedresurs(inn: str) -> dict:
    body = await _get("/fedresurs", {"inn": inn})
    if not body:
        return {"fedresurs_count": 0, "fedresurs_messages": []}
    data = body.get("data") or body
    items = data if isinstance(data, list) else (data.get("items") or [])

    parsed = []
    for m in items[:5]:
        if isinstance(m, dict):
            parsed.append({
                "type": m.get("type") or m.get("Тип") or "",
                "date": m.get("date") or m.get("Дата") or "",
                "text": (m.get("text") or m.get("Содержание") or m.get("Сообщение") or "")[:250],
            })

    total = len(items)
    if isinstance(data, dict):
        total = _num(data.get("total")) or total

    return {"fedresurs_count": int(total), "fedresurs_messages": parsed}


# ══════════════════════════════════════════════════════════════════════════════
# fetch_full_profile — всё в одном запросе (параллельно)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_full_profile(inn: str) -> dict:
    """
    Параллельно запрашивает: финансы, арбитраж, ФССП, госзакупки,
    банкротство, проверки, Федресурс. Используется в pipeline вместо fns.py.
    """
    import asyncio

    if not _available():
        return {}

    results = await asyncio.gather(
        fetch_finances(inn),
        fetch_legal_cases(inn),
        fetch_enforcements(inn),
        fetch_contracts(inn),
        fetch_bankruptcy(inn),
        fetch_inspections(inn),
        fetch_fedresurs(inn),
        return_exceptions=True,
    )

    def _safe(r) -> dict:
        return r if isinstance(r, dict) else {}

    fin, legal, enf, contracts, bankrupt, insp, fedresurs = [_safe(r) for r in results]

    return {
        # Финансы
        "revenue": fin.get("revenue"),
        "profit": fin.get("profit"),
        "assets": fin.get("assets"),
        "expense": fin.get("expense"),
        "debt": fin.get("debt"),
        "finance_year": fin.get("finance_year"),
        "revenue_trend": fin.get("revenue_trend", "unknown"),
        "revenue_series": fin.get("revenue_series", []),
        "profit_series": fin.get("profit_series", []),
        # Арбитраж
        "arbitration_count": legal.get("arbitration_count", 0),
        "arbitration_cases": legal.get("cases", []),
        # ФССП
        "enforcement_count": enf.get("enforcement_count", 0),
        "enforcement_debt": enf.get("enforcement_debt", 0),
        "enforcements": enf.get("enforcements", []),
        # Госзакупки
        "contracts_count": contracts.get("contracts_count", 0),
        "contracts_total_amount": contracts.get("contracts_total_amount", 0),
        "contracts": contracts.get("contracts", []),
        # Банкротство
        "has_bankruptcy": bankrupt.get("has_bankruptcy", False),
        "bankruptcy_messages": bankrupt.get("bankruptcy_messages", []),
        # Проверки
        "inspection_count": insp.get("inspection_count", 0),
        "inspections": insp.get("inspections", []),
        # Федресурс
        "fedresurs_count": fedresurs.get("fedresurs_count", 0),
        "fedresurs_messages": fedresurs.get("fedresurs_messages", []),
        "_checko": True,
    }


# ══════════════════════════════════════════════════════════════════════════════
# /person — все компании физического лица (учредитель / директор / ИП)
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_person(person_inn: str) -> dict:
    """
    GET /person?inn={person_inn}
    Возвращает все связи физлица:
    - Учред: компании где он учредитель (с долями)
    - Руковод: компании где он директор/руководитель
    - ИП: его индивидуальные предпринимательства
    - Дисквал: флаг дисквалификации
    """
    if not _available() or not person_inn:
        return {}
    body = await _get("/person", {"inn": person_inn})
    if not body:
        return {}
    data = body.get("data") or body
    if not data or isinstance(data, list):
        return {}
    return _parse_person_data(data, person_inn)


def _parse_person_data(d: dict, person_inn: str) -> dict:
    """Нормализует ответ /person."""
    name = d.get("ФИО") or d.get("fio") or ""

    # Компании где учредитель
    founder_companies: list[dict] = []
    for c in (d.get("Учред") or []):
        if not isinstance(c, dict):
            continue
        c_inn = c.get("ИНН") or ""
        c_name = c.get("НаимСокр") or c.get("НаимПолн") or ""
        if c_inn or c_name:
            founder_companies.append({
                "inn": c_inn,
                "ogrn": c.get("ОГРН") or "",
                "name": c_name,
                "name_full": c.get("НаимПолн") or c_name,
                "status": _parse_status(c.get("Статус") or ""),
                "okved": c.get("ОКВЭД") or "",
                "city": _extract_city(c.get("ЮрАдрес") or ""),
                "address": c.get("ЮрАдрес") or "",
                "_relation": f"учредитель: {name}",
            })

    # Компании где директор/руководитель
    director_companies: list[dict] = []
    for c in (d.get("Руковод") or []):
        if not isinstance(c, dict):
            continue
        c_inn = c.get("ИНН") or ""
        c_name = c.get("НаимСокр") or c.get("НаимПолн") or ""
        if c_inn or c_name:
            director_companies.append({
                "inn": c_inn,
                "ogrn": c.get("ОГРН") or "",
                "name": c_name,
                "name_full": c.get("НаимПолн") or c_name,
                "status": _parse_status(c.get("Статус") or ""),
                "okved": c.get("ОКВЭД") or "",
                "city": _extract_city(c.get("ЮрАдрес") or ""),
                "address": c.get("ЮрАдрес") or "",
                "_relation": f"директор: {name}",
            })

    # ИП
    ip_list: list[dict] = []
    for ip in (d.get("ИП") or []):
        if not isinstance(ip, dict):
            continue
        ogrnip = ip.get("ОГРНИП") or ip.get("ОGRНИП") or ip.get("Рег") or ""
        status = _parse_status(ip.get("Статус") or "")
        ip_list.append({
            "ogrnip": ogrnip,
            "name": name,
            "status": status,
            "reg_date": ip.get("ДатаРег") or "",
            "okved": ip.get("ОКВЭД") or "",
            "city": _extract_city(ip.get("Адрес") or ""),
            "_relation": f"ИП: {name}",
        })

    return {
        "person_inn": person_inn,
        "person_name": name,
        "is_disqualified": bool(d.get("Дисквал") or d.get("Дисквалиф")),
        "is_mass_founder": bool(d.get("МассФЛ")),
        "founder_companies": founder_companies,
        "director_companies": director_companies,
        "ip_list": ip_list,
        "total_companies": len(founder_companies) + len(director_companies) + len(ip_list),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Вспомогательные функции
# ══════════════════════════════════════════════════════════════════════════════

def _parse_status(raw) -> str:
    """ЕГРЮЛ статус → стандартный код."""
    if isinstance(raw, dict):
        text = (raw.get("Наим") or raw.get("Код") or "").strip()
    else:
        text = str(raw or "").strip()

    t = text.upper()
    if not t or "ДЕЙСТВ" in t or t == "001" or t == "ACTIVE":
        return "ACTIVE"
    if "ЛИКВИД" in t or "LIQUIDAT" in t:
        return "LIQUIDATED" if ("ЗАВЕР" in t or "ПРЕКР" in t or "LIQUIDATED" == t) else "LIQUIDATING"
    if "БАНКР" in t or "BANKRUPT" in t:
        return "BANKRUPT"
    if "РЕОРГ" in t or "REORGANIZ" in t:
        return "REORGANIZING"
    return "ACTIVE"


def _clean_city(raw: str) -> str:
    """'г. Москва' → 'Москва', 'г Москва' → 'Москва'"""
    if not raw:
        return ""
    s = raw.strip()
    for prefix in ("г. ", "г.", "г "):
        if s.startswith(prefix):
            return s[len(prefix):].strip()
    return s


def _extract_city(address: str) -> str:
    """Извлекает город из строки адреса."""
    if not address:
        return ""
    for token in address.split(","):
        t = token.strip()
        if t.startswith("г. ") or t.startswith("г.") or t.startswith("г "):
            return _clean_city(t)
    return ""


def _str_from_field(val: Any) -> str:
    """Безопасное извлечение строки из поля (может быть dict или str)."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("Код") or val.get("code") or "")
    return str(val)


def _detect_mgt(founders: list, director: str) -> str:
    if not founders:
        return "hired_director"
    if len(founders) == 1:
        f_name = founders[0].get("name", "")
        if f_name and director and (f_name in director or director in f_name):
            return "owner_managed"
        return "owner_managed"
    if len(founders) > 3:
        return "board"
    return "hired_director"


def _num(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(" ", "").replace(",", ".").replace("\xa0", ""))
    except (ValueError, TypeError):
        return None


def _sum_num(*vals) -> float | None:
    """Суммирует несколько числовых полей, игнорируя None."""
    total = 0.0
    has_any = False
    for v in vals:
        n = _num(v)
        if n is not None:
            total += n
            has_any = True
    return total if has_any else None
