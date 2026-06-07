"""Checko company response parsing."""
from __future__ import annotations

from .helpers import (
    _clean_city,
    _detect_mgt,
    _num,
    _parse_status,
)

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


