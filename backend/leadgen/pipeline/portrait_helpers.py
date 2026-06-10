"""Portrait search helpers."""
from __future__ import annotations

import logging
import re
from typing import Any

from .utils import (
    _extract_employees_from_text,
    _extract_revenue_from_text,
    _parse_json_safe,
    _safe,
)

logger = logging.getLogger(__name__)

async def _extract_company_from_portrait(portrait: str) -> str:
    """Извлекает название/ключевые слова компании из текстового портрета."""
    try:
        from core.llm import chat
        raw = await chat(
            [
                {"role": "system", "content": "Извлеки из описания ключевые слова для поиска компании в ЕГРЮЛ. Верни только строку запроса, без объяснений."},
                {"role": "user", "content": portrait},
            ],
            temperature=0.1,
            max_tokens=50,
        )
        return raw.strip()
    except Exception:
        return portrait[:50]


async def _parse_portrait_criteria(portrait: str) -> dict:
    """Парсит портрет → структурированные критерии поиска."""
    try:
        from core.llm import chat
        raw = await asyncio.wait_for(
            chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "Ты — парсер критериев поиска клиентов. "
                            "Из текстового описания портрета клиента извлеки структурированные параметры. "
                            'Ответь строго JSON: {"query": "строка для поиска ЕГРЮЛ", '
                            '"okved": "код ОКВЭД или пусто", "city": "", "region_code": "", '
                            '"employees_min": null, "employees_max": null, "revenue_min": null, '
                            '"keywords": [], "must_have_gov_contracts": false, "prefer_growing": false}'
                        ),
                    },
                    {"role": "user", "content": portrait},
                ],
                temperature=0.1,
                max_tokens=200,
                json_mode=True,
            ),
            timeout=12.0,
        )
        parsed = _parse_json_safe(raw)
        return _normalize_portrait_criteria(portrait, parsed)
    except Exception:
        return _normalize_portrait_criteria(portrait, {
            "query": portrait[:50],
            "okved": "",
            "city": "",
            "region_code": "",
            "employees_min": None,
            "employees_max": None,
            "revenue_min": None,
            "keywords": [],
            "must_have_gov_contracts": False,
            "prefer_growing": False,
        })


def _match_portrait(company: dict, criteria: dict) -> tuple[float, list[str], list[str]]:
    """
    Детерминированный score соответствия портрету.
    Если поле отсутствует в источнике, критерий не валит компанию, а даёт небольшой нейтральный вес.
    """
    matched: list[str] = []
    missed: list[str] = []
    score = 0.0

    # Статус (базовый фильтр качества)
    if (company.get("status") or "").upper() == "ACTIVE":
        score += 0.2
        matched.append("active")
    else:
        missed.append("active")

    # Гео
    city = (criteria.get("city") or "").strip().lower()
    company_city = (company.get("city") or "").strip().lower()
    if city:
        if city and company_city and city in company_city:
            score += 0.2
            matched.append("city")
        else:
            missed.append("city")

    # Отрасль / ОКВЭД
    okved = (criteria.get("okved") or "").strip()
    company_okved = (company.get("okved") or "").strip()
    if okved:
        if company_okved.startswith(okved[:2]):
            score += 0.25
            matched.append("okved")
        else:
            missed.append("okved")

    # Выручка — если данных нет, просто пропускаем (не штрафуем)
    revenue_min = criteria.get("revenue_min")
    revenue = company.get("revenue")
    if revenue_min is not None and revenue is not None:
        try:
            if float(revenue) >= float(revenue_min):
                score += 0.2
                matched.append("revenue")
            else:
                score -= 0.1
                missed.append("revenue_low")
        except Exception:
            pass  # нет данных — нейтрально

    # Численность — если данных нет, нейтрально (не штрафуем)
    employees_min = criteria.get("employees_min")
    employees_max = criteria.get("employees_max")
    employees = company.get("employees_count")
    if (employees_min is not None or employees_max is not None) and employees is None:
        missed.append("employees_unknown")
    elif (employees_min is not None or employees_max is not None) and employees is not None:
        try:
            e = int(employees)
            min_ok = employees_min is None or e >= int(employees_min)
            max_ok = employees_max is None or e <= int(employees_max)
            if min_ok and max_ok:
                score += 0.15
                matched.append("employees")
            else:
                score -= 0.1
                missed.append("employees_out_of_range")
        except Exception:
            pass  # нет данных — нейтрально

    # Сигналы Checko
    contracts = int(company.get("_contracts_count", 0) or 0)
    has_bankruptcy = bool(company.get("_has_bankruptcy"))
    if criteria.get("must_have_gov_contracts"):
        if contracts > 0:
            score += 0.1
            matched.append("gov_contracts")
        else:
            missed.append("gov_contracts")
    if has_bankruptcy:
        score -= 0.1
        missed.append("bankruptcy_risk")

    score = max(0.0, min(1.0, score))
    return score, matched, missed


def _build_portrait_seed_queries(
    portrait: str,
    criteria: dict,
    reference_profile: dict[str, Any] | None = None,
) -> list[str]:
    """Собирает список безопасных текстовых запросов для EGRUL поиска через Checko."""
    query = (criteria.get("query") or "").strip()
    okved = (criteria.get("okved") or "").strip()
    city = (criteria.get("city") or "").strip()
    keywords = [str(k).strip() for k in (criteria.get("keywords") or []) if str(k).strip()]
    chunks = [c.strip() for c in re.split(r"[,;]", portrait) if c.strip()]

    if query and len(query) > 40 and chunks:
        query = chunks[0]

    seeds = [query, okved, f"{okved} {city}".strip(), city, *chunks[:3], *keywords[:8], portrait[:60]]
    if reference_profile:
        ref_name = (reference_profile.get("name_short") or reference_profile.get("name") or "").strip()
        ref_okved = (reference_profile.get("okved") or "").strip()
        ref_city = (reference_profile.get("city") or "").strip()
        seeds.extend([ref_name, ref_okved, ref_city, f"{ref_okved} {ref_city}".strip()])

    # Отраслевые синонимы для IT: повышаем шанс реальных совпадений по названию компаний.
    p_low = portrait.lower()
    if " it" in f" {p_low}" or "айти" in p_low or "информац" in p_low or okved.startswith("62"):
        seeds.extend(["IT", "Айти", "Софт", "Систем", "Тех"])

    out: list[str] = []
    seen: set[str] = set()
    for s in seeds:
        norm = s.strip()
        if len(norm) < 2:
            continue
        if len(norm) > 40:
            continue
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out[:6]


def _dedup_companies(companies: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for c in companies:
        inn = (c.get("inn") or "").strip()
        key = inn or (c.get("name") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _portrait_workability_verdict(card: dict) -> dict[str, Any]:
    """
    Короткий вердикт пригодности компании к первому контакту.
    Используем результаты 4 агентов + профильные сигналы и формируем «якоря».
    """
    score = int(card.get("final_score") or 0)
    fin = card.get("financials") or {}
    lpr = card.get("lpr") or {}
    triggers = card.get("triggers") or []
    hooks = []

    if fin.get("revenue"):
        hooks.append(f"Выручка: {_fmt_money(fin.get('revenue'))}")
    if fin.get("contracts_count", 0) > 0:
        hooks.append(f"Госзакупки: {fin.get('contracts_count')} контрактов")
    if triggers:
        hooks.extend([f"Триггер: {t}" for t in triggers[:2]])
    if lpr.get("name"):
        hooks.append(f"ЛПР: {lpr.get('name')} ({lpr.get('role') or 'руководитель'})")
    if card.get("hook"):
        hooks.append(f"Крючок: {card.get('hook')}")

    if score >= 75:
        verdict = "go_now"
    elif score >= 55:
        verdict = "go_with_hypothesis"
    else:
        verdict = "nurture_first"

    return {
        "fit_verdict": verdict,
        "fit_score": score,
        "anchors": hooks[:5],
    }


def _normalize_portrait_criteria(portrait: str, criteria: dict) -> dict:
    """
    Нормализует критерии портрета и добавляет эвристики,
    чтобы поиск работал даже при слабом/нестабильном LLM-парсинге.
    """
    out = dict(criteria or {})
    text = portrait or ""
    tl = text.lower()

    # Базовые ключи и дефолты
    defaults = {
        "query": "",
        "okved": "",
        "city": "",
        "region_code": "",
        "employees_min": None,
        "employees_max": None,
        "revenue_min": None,
        "keywords": [],
        "must_have_gov_contracts": False,
        "prefer_growing": False,
    }
    for k, v in defaults.items():
        out.setdefault(k, v)

    # Эвристика города
    if not out.get("city"):
        city_map = {
            "москва": "Москва",
            "санкт-петербург": "Санкт-Петербург",
            "питер": "Санкт-Петербург",
            "екатеринбург": "Екатеринбург",
            "новосибирск": "Новосибирск",
            "казань": "Казань",
        }
        for key, city in city_map.items():
            if key in tl:
                out["city"] = city
                break

    # Эвристика численности
    if out.get("employees_min") is None:
        m = re.search(r"от\s*(\d{1,6})\s*сотруд", tl)
        if m:
            out["employees_min"] = int(m.group(1))
    if out.get("employees_max") is None:
        m = re.search(r"до\s*(\d{1,6})\s*сотруд", tl)
        if m:
            out["employees_max"] = int(m.group(1))

    # Эвристика выручки
    if out.get("revenue_min") is None:
        m = re.search(r"выручк[аи][^\\d]{0,20}от\\s*(\\d+(?:[\\.,]\\d+)?)\\s*(млрд|млн)?", tl)
        if m:
            v = float(m.group(1).replace(",", "."))
            unit = (m.group(2) or "").lower()
            if unit == "млрд":
                v *= 1_000_000_000
            elif unit == "млн":
                v *= 1_000_000
            out["revenue_min"] = v

    # Эвристика флагов
    if "госконтракт" in tl or "госзаказ" in tl or "44-фз" in tl or "223-фз" in tl:
        out["must_have_gov_contracts"] = True
    if "растущ" in tl or "рост" in tl or "инвест" in tl or "найм" in tl:
        out["prefer_growing"] = True

    # Эвристика отрасли/ОКВЭД
    if not out.get("okved"):
        if " it" in f" {tl}" or "айти" in tl or "информац" in tl or "программ" in tl:
            out["okved"] = "62"

    # Ключевые слова
    if not out.get("keywords"):
        stop = {"от", "до", "и", "в", "на", "по", "компания", "сотрудников", "выручка", "млн", "млрд"}
        kws = []
        for tok in re.findall(r"[A-Za-zА-Яа-я0-9\\-]{2,}", text):
            t = tok.strip()
            if t.lower() in stop:
                continue
            if t not in kws:
                kws.append(t)
        out["keywords"] = kws[:10]

    # Query для поиска
    q = (out.get("query") or "").strip()
    if not q or len(q) > 40:
        if out.get("city") and out.get("okved"):
            q = f"{out.get('okved')} {out.get('city')}"
        elif out.get("okved"):
            q = out.get("okved")
        elif out.get("keywords"):
            q = out["keywords"][0]
        else:
            q = text[:30]
        out["query"] = q

    return out


async def _build_reference_profile(reference_inn: str, errors: list[str]) -> dict[str, Any] | None:
    """Загружает эталонную компанию по ИНН для поиска максимально похожих компаний."""
    from leadgen.modules.checko import fetch_company, fetch_full_profile

    company = await _safe(fetch_company(reference_inn), errors, f"reference_company:{reference_inn}") or {}
    if not company:
        return None
    finances = await _safe(fetch_full_profile(reference_inn), errors, f"reference_finances:{reference_inn}") or {}
    if finances.get("revenue") is not None:
        company["revenue"] = finances.get("revenue")
    company["_contracts_count"] = finances.get("contracts_count", 0)
    company["_has_bankruptcy"] = bool(finances.get("has_bankruptcy"))
    return company


def _merge_criteria_with_reference(criteria: dict, reference_profile: dict[str, Any]) -> dict:
    """
    Если указан ИНН-эталон, усиливаем критерии реальными данными компании.
    Приоритет у явных полей из UI/портрета, но пустые поля заполняем эталоном.
    """
    out = dict(criteria)
    out["okved"] = out.get("okved") or (reference_profile.get("okved") or "")[:2]
    out["city"] = out.get("city") or reference_profile.get("city") or ""
    if out.get("revenue_min") is None and reference_profile.get("revenue"):
        # Для похожих компаний берём мягкую нижнюю границу по выручке ~50% эталона.
        try:
            out["revenue_min"] = float(reference_profile.get("revenue")) * 0.5
        except Exception:
            pass
    out["query"] = (out.get("query") or "").strip() or reference_profile.get("name_short") or reference_profile.get("name") or ""
    return out


def _score_reference_similarity(company: dict, reference_profile: dict[str, Any]) -> tuple[float, list[str]]:
    """Бонус похожести на эталонную компанию (по ИНН), чтобы ранжирование было ближе к 'аналогу'."""
    bonus = 0.0
    matched: list[str] = []

    # ОКВЭД-группа
    c_okved = (company.get("okved") or "")[:2]
    r_okved = (reference_profile.get("okved") or "")[:2]
    if c_okved and r_okved and c_okved == r_okved:
        bonus += 0.2
        matched.append("similar_okved")

    # Город
    c_city = (company.get("city") or "").lower()
    r_city = (reference_profile.get("city") or "").lower()
    if c_city and r_city and c_city == r_city:
        bonus += 0.1
        matched.append("similar_city")

    # Выручка (если обе известны)
    c_rev = company.get("revenue")
    r_rev = reference_profile.get("revenue")
    if c_rev is not None and r_rev is not None:
        try:
            c = float(c_rev)
            r = float(r_rev)
            if r > 0:
                ratio = c / r
                if 0.5 <= ratio <= 1.5:
                    bonus += 0.15
                    matched.append("similar_revenue")
        except Exception:
            pass

    # Госзакупки как сигнал B2G-профиля
    c_gov = int(company.get("_contracts_count", 0) or 0)
    r_gov = int(reference_profile.get("_contracts_count", 0) or 0)
    if c_gov > 0 and r_gov > 0:
        bonus += 0.05
        matched.append("similar_gov_contracts")

    return bonus, matched


async def _fallback_portrait_candidates_from_web(
    portrait: str,
    errors: list[str],
    limit: int = 10,
) -> list[dict]:
    """
    Fallback-кандидаты, если EGRUL текстовый поиск не отдал rows:
    1) web search по портрету
    2) извлечение ИНН из сниппетов
    3) обогащение через Checko /company
    """
    from rag.search import free_search
    from leadgen.modules.checko import fetch_company

    q = f"{portrait} компания ИНН Россия"
    web = await _safe(free_search(q, summarize=False, max_results=12), errors, "portrait_web_fallback") or {}
    blob = " ".join(
        " ".join(filter(None, [r.get("title", ""), r.get("snippet", ""), r.get("content", "")]))
        for r in (web.get("results") or [])[:12]
    )
    inns = []
    for m in re.findall(r"\b\d{10}\b", blob):
        if m not in inns:
            inns.append(m)
        if len(inns) >= limit:
            break
    if not inns:
        return []

    out: list[dict] = []
    for inn in inns:
        c = await _safe(fetch_company(inn), errors, f"portrait_web_company:{inn}")
        if c:
            out.append(c)
    return out


async def _fill_missing_portrait_fields(company: dict, criteria: dict, errors: list[str]) -> None:
    """
    Точечная добивка полей через веб-поиск, если Checko не дал нужные данные.
    Используется только для полей, которые реально запрошены в портрете.
    """
    need_employees = (
        (criteria.get("employees_min") is not None or criteria.get("employees_max") is not None)
        and company.get("employees_count") in (None, "", 0)
    )
    need_revenue = criteria.get("revenue_min") is not None and company.get("revenue") in (None, "", 0)

    if not need_employees and not need_revenue:
        return

    from rag.search import free_search

    name = company.get("name") or company.get("name_short") or ""
    inn = company.get("inn") or ""
    query = f"{name} {inn} численность сотрудников выручка"
    web = await _safe(free_search(query, summarize=False, max_results=5), errors, f"portrait_web_enrich:{inn or name}") or {}

    text_parts: list[str] = []
    for r in (web.get("results") or [])[:5]:
        text_parts.append(" ".join(filter(None, [r.get("title", ""), r.get("snippet", ""), r.get("content", "")])))
    text_blob = " ".join(text_parts).lower()

    if need_employees:
        emp = _extract_employees_from_text(text_blob)
        if emp is not None:
            company["employees_count"] = emp
            company["_employees_source"] = "web"
    if need_revenue:
        rev = _extract_revenue_from_text(text_blob)
        if rev is not None:
            company["revenue"] = rev
            company["_revenue_source"] = "web"



