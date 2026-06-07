"""Pipeline utilities."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

def _extract_employees_from_text(text: str) -> int | None:
    patterns = [
        r"численност[ьи]\s*(?:сотрудников)?\s*[:\-]?\s*(\d{1,6})",
        r"(\d{1,6})\s*(?:сотрудник(?:ов|а)?|чел(?:овек)?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 2_000_000:
                    return val
            except Exception:
                pass
    return None


def _extract_revenue_from_text(text: str) -> float | None:
    # Примеры: "выручка 120 млн", "выручка: 1.2 млрд", "оборот 450000000"
    patterns = [
        r"(?:выручк[аи]|оборот|revenue)\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*(млрд|млн|bn|billion|mln|million)?",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                num = float(m.group(1).replace(",", "."))
                unit = (m.group(2) or "").lower()
                if unit in ("млрд", "bn", "billion"):
                    num *= 1_000_000_000
                elif unit in ("млн", "mln", "million"):
                    num *= 1_000_000
                if num > 0:
                    return num
            except Exception:
                pass
    return None


async def _safe(coro, errors: list, label: str):
    """Выполняет корутину с перехватом ошибок."""
    try:
        return await coro
    except Exception as e:
        errors.append(f"{label}: {e}")
        logger.warning("Pipeline step '%s' failed: %s", label, e)
        return None


def _extract_contacts_from_web(web_search: dict) -> dict:
    """Извлекает телефоны, email и домен из результатов веб-поиска."""
    import re
    import urllib.parse

    phones: list[str] = []
    emails: list[str] = []
    website = ""

    # Паттерны
    _phone_re = re.compile(r'(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')
    _email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    _skip_emails = {"example.com", "gmail.com", "mail.ru", "yandex.ru", "bk.ru", "inbox.ru"}

    results = web_search.get("results") or []
    for r in results[:8]:
        text = " ".join(filter(None, [r.get("title", ""), r.get("snippet", ""), r.get("content", "")]))
        phones.extend(_phone_re.findall(text))
        for em in _email_re.findall(text):
            domain_em = em.split("@")[-1].lower()
            if domain_em not in _skip_emails:
                emails.append(em)
        # Первый не-новостной URL → сайт компании
        if not website:
            url = r.get("url") or r.get("link") or ""
            if url:
                try:
                    parsed = urllib.parse.urlparse(url)
                    netloc = parsed.netloc.replace("www.", "").lower()
                    _news_domains = {"rbc.ru", "ria.ru", "tass.ru", "vedomosti.ru", "kommersant.ru",
                                     "interfax.ru", "novaya-gazeta.ru", "mk.ru", "gazeta.ru"}
                    if netloc and not any(netloc.endswith(d) for d in _news_domains):
                        website = netloc
                except Exception:
                    pass

    return {
        "phones": _dedup_list(phones)[:5],
        "emails": _dedup_list(emails)[:5],
        "website": website,
    }


def _dedup_list(lst: list) -> list:
    """Дедупликация с сохранением порядка."""
    seen: set = set()
    result: list = []
    for item in lst:
        norm = str(item).strip()
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    url = url.strip().lower()
    for p in ("https://", "http://", "www."):
        if url.startswith(p):
            url = url[len(p):]
    return url.split("/")[0]


def _fmt_money(val) -> str:
    if val is None:
        return "—"
    try:
        v = float(val)
        if v >= 1_000_000_000:
            return f"{v/1_000_000_000:.1f} млрд ₽"
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f} млн ₽"
        return f"{v:,.0f} ₽"
    except Exception:
        return str(val)


def _render_script(outline: list) -> str:
    """Рендерит script_outline в читаемый текст независимо от формата шагов."""
    lines = []
    for i, step in enumerate(outline, 1):
        if isinstance(step, dict):
            label = step.get("step") or step.get("title") or f"Шаг {i}"
            text = step.get("text") or step.get("content") or step.get("phrase") or ""
            lines.append(f"{i}. {label}: {text}" if text else f"{i}. {label}")
        else:
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


def _parse_json_safe(raw: str) -> dict:
    import json, re
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"_parse_error": True, "raw": raw[:200]}


def _build_connections(company_data: dict) -> dict:
    """
    Быстро строит карту связей из уже загруженных данных компании (без доп. запросов).
    Возвращает структуру для отображения во фронтенде.
    """
    founders = company_data.get("founders") or []
    related = company_data.get("related_companies") or []

    # Разбиваем учредителей на физлиц и юрлиц
    individual_founders = [
        {"name": f["name"], "share_percent": f.get("share_percent"), "type": "INDIVIDUAL"}
        for f in founders if f.get("type") == "INDIVIDUAL" and f.get("name")
    ]
    legal_founders = [
        {"name": f["name"], "inn": f.get("inn", ""), "share_percent": f.get("share_percent"), "type": "LEGAL"}
        for f in founders if f.get("type") in ("LEGAL", "FOREIGN") and f.get("name")
    ]

    # Дочерние и аффилированные
    subsidiaries = [
        {
            "name": r.get("name_full") or r.get("name") or "—",
            "inn": r.get("inn", ""),
            "status": r.get("status", ""),
            "okved": r.get("okved", ""),
            "city": r.get("address", "")[:60] if r.get("address") else "",
        }
        for r in related
    ]

    has_connections = bool(individual_founders or legal_founders or subsidiaries)

    return {
        "has_connections": has_connections,
        "individual_founders": individual_founders,
        "legal_founders": legal_founders,
        "subsidiaries": subsidiaries,
        "total_founders": len(founders),
        "total_subsidiaries": len(subsidiaries),
    }

