"""Cluster search around anchor INN."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .utils import _safe

logger = logging.getLogger(__name__)

async def run_cluster(inn: str) -> dict[str, Any]:
    """
    Кластер-поиск: по ИНН якоря находит связанные компании (2 уровня).
    Источники связей:
    1. СвязУчред якоря (Checko) — компании где якорь является учредителем
    2. Учредители-юрлица якоря → их полный профиль + их дочерние (2й уровень)
    3. Дочерние якоря → их учредители-юрлица → другие их дочерние (сестринские)
    4. Финансы якоря через Checko /finances
    """
    from leadgen.modules.checko import (
        fetch_company as checko_company, fetch_finances, fetch_person,
        _available as checko_ok,
    )
    errors: list[str] = []

    anchor = await _safe(checko_company(inn), errors, "cluster_anchor")
    if not anchor:
        return {"status": "error", "message": f"Компания с ИНН {inn} не найдена", "errors": errors}

    related: list[dict] = []
    seen_inns: set[str] = {inn}       # ИНН юрлиц (уже обработаны)
    seen_person_inns: set[str] = set() # ИНН физлиц (уже обработаны)

    # ── 1. Дочерние якоря (СвязУчред) ───────────────────────────────────────
    subsidiaries_inns: list[str] = []
    for rel in (anchor.get("related_companies") or []):
        r_inn = rel.get("inn", "")
        if r_inn and r_inn not in seen_inns:
            seen_inns.add(r_inn)
            subsidiaries_inns.append(r_inn)
            entry = dict(rel)
            entry["_relation"] = "дочерняя компания"
            entry["_level"] = 1
            related.append(entry)

    # ── 2. Учредители якоря ──────────────────────────────────────────────────
    parent_inns: list[str] = []
    individual_founders_to_expand: list[dict] = []  # физлица с ИНН

    for founder in (anchor.get("founders") or []):
        f_inn = founder.get("inn", "")
        f_type = founder.get("type", "")
        f_name = founder.get("name", "")
        f_pct = founder.get("share_percent")

        if f_type == "LEGAL" and f_inn and f_inn not in seen_inns:
            # Юрлицо-учредитель → полный профиль
            seen_inns.add(f_inn)
            parent_inns.append(f_inn)
            f_data = await _safe(checko_company(f_inn), errors, f"cluster_parent_{f_inn}")
            if f_data:
                pct_str = f"{f_pct}%" if f_pct is not None else "?"
                f_data["_relation"] = f"материнская компания ({pct_str})"
                f_data["_level"] = 1
                related.append(f_data)

        elif f_type == "INDIVIDUAL" and f_inn and f_inn not in seen_person_inns:
            # Физлицо-учредитель → раскроем через /person
            seen_person_inns.add(f_inn)
            individual_founders_to_expand.append({"inn": f_inn, "name": f_name, "share_percent": f_pct})

    # ── 3. Раскрытие физлиц-учредителей через /person ────────────────────────
    persons_data: list[dict] = []
    for person in individual_founders_to_expand:
        p_data = await _safe(fetch_person(person["inn"]), errors, f"cluster_person_{person['inn']}")
        if not p_data:
            continue
        persons_data.append(p_data)

        # 3a. Другие компании где это физлицо — учредитель
        for c in (p_data.get("founder_companies") or []):
            c_inn = c.get("inn", "")
            if c_inn and c_inn not in seen_inns and c_inn != inn:
                seen_inns.add(c_inn)
                entry = dict(c)
                entry["_relation"] = f"другая компания учредителя {person['name']}"
                entry["_level"] = 2
                related.append(entry)

        # 3b. Компании где это физлицо — директор
        for c in (p_data.get("director_companies") or []):
            c_inn = c.get("inn", "")
            if c_inn and c_inn not in seen_inns and c_inn != inn:
                seen_inns.add(c_inn)
                entry = dict(c)
                entry["_relation"] = f"другая компания (директор: {person['name']})"
                entry["_level"] = 2
                related.append(entry)

        # 3c. ИП физлица — как отдельный «субъект»
        for ip in (p_data.get("ip_list") or []):
            if ip.get("ogrnip") and ip["ogrnip"] not in seen_inns:
                seen_inns.add(ip["ogrnip"])
                ip["_relation"] = f"ИП учредителя {person['name']}"
                ip["_level"] = 2
                ip["_type"] = "IP"
                related.append(ip)

    # ── 4. Уровень 2: сестринские (дочерние родителя-юрлица) ────────────────
    for p_inn in parent_inns:
        parent = next((r for r in related if r.get("inn") == p_inn), None)
        if not parent:
            continue
        for sib in (parent.get("related_companies") or []):
            s_inn = sib.get("inn", "")
            if s_inn and s_inn not in seen_inns:
                seen_inns.add(s_inn)
                entry = dict(sib)
                parent_name = parent.get("name_short") or parent.get("name") or p_inn
                entry["_relation"] = f"сестринская (через {parent_name})"
                entry["_level"] = 2
                related.append(entry)

    # ── 5. Финансы якоря ─────────────────────────────────────────────────────
    anchor_finances = {}
    if checko_ok() and inn:
        anchor_finances = await _safe(fetch_finances(inn), errors, "cluster_anchor_finances") or {}

    # ── 6. Суммарный оборот группы ───────────────────────────────────────────
    total_revenue = 0.0
    anchor_rev = anchor_finances.get("revenue") or anchor.get("revenue") or 0
    try:
        total_revenue += float(anchor_rev)
    except Exception:
        pass
    for company in related:
        rev = company.get("revenue") or 0
        try:
            total_revenue += float(rev)
        except Exception:
            pass

    # ── 7. Группировка по типу связи ─────────────────────────────────────────
    subsidiaries = [r for r in related if "дочерняя" in r.get("_relation", "")]
    parents      = [r for r in related if "материнская" in r.get("_relation", "")]
    siblings     = [r for r in related if "сестринская" in r.get("_relation", "")]
    person_cos   = [r for r in related if "другая компания" in r.get("_relation", "")]
    ips          = [r for r in related if r.get("_type") == "IP"]
    other        = [r for r in related if r not in subsidiaries + parents + siblings + person_cos + ips]

    return {
        "status": "ok",
        "anchor": {**anchor, "finances": anchor_finances},
        "related": related,
        "persons": persons_data,   # профили физлиц-учредителей
        "groups": {
            "subsidiaries": subsidiaries,
            "parents": parents,
            "siblings": siblings,
            "person_companies": person_cos,  # через физлиц
            "ips": ips,
            "other": other,
        },
        "total_companies": 1 + len(related),
        "total_revenue_estimate": total_revenue,
        "errors": errors,
    }



