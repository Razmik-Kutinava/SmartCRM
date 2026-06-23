"""Догрузка компании, контакта и реквизитов Битрикс24 для лида."""
from __future__ import annotations

import logging
from typing import Any

from core.lead_bitrix_extra import merge_bitrix_extra
from core.lead_contacts import merge_bitrix_contacts
from core.lead_profile import okved_section

from .bitrix24_uf import (
    extract_bitrix_extra_from_row,
    extract_domain_from_row,
    extract_employees_from_row,
    extract_inn_from_row,
    extract_okved_from_row,
    extract_products_from_row,
    normalize_inn,
    normalize_ogrn,
    normalize_website,
    uf_by_hint,
    _uf_raw,
)

logger = logging.getLogger(__name__)

ENTITY_LEAD = 1
ENTITY_COMPANY = 4


async def _bitrix_call(method: str, params: dict | None = None) -> dict:
    from .bitrix24 import bitrix_call

    return await bitrix_call(method, params or {})


async def fetch_entity(lead_id: int) -> dict | None:
    try:
        data = await _bitrix_call("crm.lead.get", {"id": lead_id})
        row = data.get("result")
        return row if isinstance(row, dict) else None
    except Exception as e:
        logger.warning("crm.lead.get %s: %s", lead_id, e)
        return None


async def _fetch_company(company_id: int) -> dict | None:
    try:
        data = await _bitrix_call("crm.company.get", {"id": company_id})
        row = data.get("result")
        return row if isinstance(row, dict) else None
    except Exception as e:
        logger.debug("crm.company.get %s: %s", company_id, e)
        return None


async def _fetch_lead_contact_items(lead_id: int) -> list[dict[str, Any]]:
    """Связи лида с контактами: crm.lead.contact.items.get."""
    try:
        data = await _bitrix_call("crm.lead.contact.items.get", {"id": lead_id})
        rows = data.get("result") or []
        if not isinstance(rows, list):
            return []
        out: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                cid = int(row.get("CONTACT_ID") or 0)
            except (TypeError, ValueError):
                continue
            if cid <= 0:
                continue
            try:
                sort = int(row.get("SORT") or 0)
            except (TypeError, ValueError):
                sort = 0
            out.append(
                {
                    "contact_id": cid,
                    "sort": sort,
                    "is_primary": str(row.get("IS_PRIMARY") or "").upper() == "Y",
                }
            )
        out.sort(key=lambda x: (not x["is_primary"], x["sort"], x["contact_id"]))
        return out
    except Exception as e:
        logger.debug("crm.lead.contact.items.get %s: %s", lead_id, e)
        return []


async def _fetch_contact(contact_id: int) -> dict | None:
    try:
        data = await _bitrix_call("crm.contact.get", {"id": contact_id})
        row = data.get("result")
        return row if isinstance(row, dict) else None
    except Exception as e:
        logger.debug("crm.contact.get %s: %s", contact_id, e)
        return None


async def _fetch_requisites(entity_type_id: int, entity_id: int) -> list[dict]:
    try:
        data = await _bitrix_call(
            "crm.requisite.list",
            {
                "filter": {"ENTITY_TYPE_ID": entity_type_id, "ENTITY_ID": entity_id},
                "select": ["ID", "RQ_INN", "RQ_OGRN", "RQ_KPP", "RQ_COMPANY_NAME", "RQ_ADDR"],
            },
        )
        rows = data.get("result") or []
        return [r for r in rows if isinstance(r, dict)]
    except Exception as e:
        logger.debug("crm.requisite.list %s/%s: %s", entity_type_id, entity_id, e)
        return []


def _first_multi(val: Any) -> str:
    from .bitrix24 import _first_multi as fm

    return fm(val)


def _contact_full_name(row: dict) -> str:
    parts = [row.get("NAME"), row.get("LAST_NAME"), row.get("SECOND_NAME")]
    return " ".join(p for p in parts if p and str(p).strip()).strip()


def _phones_from_row(row: dict) -> list[str]:
    from .bitrix24 import _all_phones

    raw = _all_phones(row.get("PHONE"))
    if raw == "—":
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _emails_from_row(row: dict) -> list[str]:
    from .bitrix24 import _first_multi

    val = row.get("EMAIL")
    if not val:
        return []
    if isinstance(val, list):
        out: list[str] = []
        for item in val:
            if isinstance(item, dict) and item.get("VALUE"):
                s = str(item["VALUE"]).strip()
                if s:
                    out.append(s)
            elif item:
                s = str(item).strip()
                if s:
                    out.append(s)
        return out
    email = _first_multi(val)
    return [email] if email and email != "—" else []


def _contact_entry(contact_id: int, row: dict, *, is_primary: bool = False) -> dict[str, Any]:
    name = _contact_full_name(row) or "Контакт"
    return {
        "id": f"b24-contact-{contact_id}",
        "name": name,
        "role": "lpr" if is_primary else "other",
        "position": str(row.get("POST") or "").strip(),
        "phones": _phones_from_row(row),
        "emails": _emails_from_row(row),
        "messengers": [],
    }


def _flat_fields_from_primary(contact: dict[str, Any]) -> dict[str, str]:
    patch: dict[str, str] = {}
    name = str(contact.get("name") or "").strip()
    if name:
        patch["contact"] = name[:255]
    post = str(contact.get("position") or "").strip()
    if post:
        patch["position"] = post[:255]
    emails = contact.get("emails") or []
    phones = contact.get("phones") or []
    if emails:
        patch["email"] = str(emails[0])[:255]
    if phones:
        patch["phone"] = str(phones[0])[:100]
    return patch


async def _contacts_from_bitrix_lead(
    row: dict,
    *,
    primary_contact: dict | None,
    primary_contact_id: int | None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    import asyncio

    lead_id = int(row["ID"])
    items = await _fetch_lead_contact_items(lead_id)
    if not items and primary_contact_id:
        items = [{"contact_id": primary_contact_id, "sort": 0, "is_primary": True}]

    contacts: list[dict[str, Any]] = []
    flat: dict[str, str] = {}
    if not items:
        return contacts, flat

    fetched = await asyncio.gather(
        *[_fetch_contact(item["contact_id"]) for item in items],
        return_exceptions=True,
    )
    primary_set = False
    for item, contact_row in zip(items, fetched):
        if isinstance(contact_row, Exception) or not contact_row:
            continue
        cid = int(item["contact_id"])
        is_primary = bool(item.get("is_primary")) or not primary_set
        entry = _contact_entry(cid, contact_row, is_primary=is_primary)
        contacts.append(entry)
        if is_primary and not flat:
            flat = _flat_fields_from_primary(entry)
            primary_set = True

    if contacts and not flat:
        flat = _flat_fields_from_primary(contacts[0])
    return contacts, flat


def _requisite_ids(reqs: list[dict]) -> tuple[str | None, str | None]:
    for req in reqs:
        inn = normalize_inn(req.get("RQ_INN"))
        ogrn = normalize_ogrn(req.get("RQ_OGRN"))
        if inn or ogrn:
            return inn, ogrn
    return None, None


async def enrich_fields_from_bitrix_row(row: dict) -> dict[str, Any]:
    """Доп. поля Lead из связанных сущностей и UF (поверх row_to_lead_fields)."""
    import asyncio

    extra: dict[str, Any] = {}
    inn = extract_inn_from_row(row)
    ogrn = None

    company_id = row.get("COMPANY_ID")
    contact_id = row.get("CONTACT_ID")
    try:
        cid = int(company_id) if company_id not in (None, "", "0") else None
    except (TypeError, ValueError):
        cid = None
    try:
        ctid = int(contact_id) if contact_id not in (None, "", "0") else None
    except (TypeError, ValueError):
        ctid = None

    company_coro = _fetch_company(cid) if cid else asyncio.sleep(0, result=None)
    contact_coro = _fetch_contact(ctid) if ctid else asyncio.sleep(0, result=None)
    contacts_coro = _contacts_from_bitrix_lead(
        row,
        primary_contact=None,
        primary_contact_id=ctid,
    )
    req_company = _fetch_requisites(ENTITY_COMPANY, cid) if cid else asyncio.sleep(0, result=[])
    req_lead = _fetch_requisites(ENTITY_LEAD, int(row["ID"]))

    company, contact, contacts_pack, reqs_co, reqs_lead = await asyncio.gather(
        company_coro,
        contact_coro,
        contacts_coro,
        req_company,
        req_lead,
        return_exceptions=True,
    )
    if isinstance(company, Exception):
        company = None
    if isinstance(contact, Exception):
        contact = None
    if isinstance(contacts_pack, Exception):
        contacts_pack = ([], {})
    if isinstance(reqs_co, Exception):
        reqs_co = []
    if isinstance(reqs_lead, Exception):
        reqs_lead = []

    inn_req, ogrn_req = _requisite_ids(list(reqs_co) + list(reqs_lead))
    if inn_req:
        inn = inn_req
    if ogrn_req:
        ogrn = ogrn_req

    if inn:
        extra["inn"] = inn
    if ogrn:
        extra["ogrn"] = ogrn

    domain = extract_domain_from_row(row)
    website = _first_multi(row.get("WEB"))
    if website == "—":
        website = ""
    if not website and domain:
        website = domain
    if website:
        extra["website"] = normalize_website(website)

    products = extract_products_from_row(row)
    if products:
        extra["products_owned"] = products

    try:
        from integrations.bitrix24_products import fetch_bitrix_lead_products
        from core.lead_products import products_owned_names

        b_id = int(row["ID"])
        lead_products = await fetch_bitrix_lead_products(b_id, row)
        if lead_products:
            extra["lead_products"] = lead_products
            owned = products_owned_names(lead_products)
            if owned:
                extra["products_owned"] = owned
    except Exception as e:
        logger.warning("fetch_bitrix_lead_products #%s: %s", row.get("ID"), e)

    industry = uf_by_hint(row, "industry", "отрасл", "сфера")
    if company and isinstance(company, dict):
        if not industry:
            industry = str(company.get("INDUSTRY") or company.get("COMPANY_TYPE") or "").strip()
        if not extra.get("website") or extra.get("website") == "—":
            cw = _first_multi(company.get("WEB"))
            if cw and cw != "—":
                extra["website"] = normalize_website(cw)
    if industry and industry != "—":
        extra["industry"] = industry[:255]

    okved_code, okved_name = extract_okved_from_row(row)
    if company and isinstance(company, dict) and not okved_code:
        c_code, c_name = extract_okved_from_row(company)
        okved_code = okved_code or c_code
        okved_name = okved_name or c_name
    if okved_code:
        extra["okved_main"] = okved_code
        if okved_name:
            extra["okved_name"] = okved_name[:500]
        extra["okved_section"] = okved_section(okved_code)
        if not extra.get("industry"):
            extra["industry"] = (okved_name or okved_code)[:255]

    employees = extract_employees_from_row(row)
    if not employees and company and isinstance(company, dict):
        employees = extract_employees_from_row(company)
    if employees and employees != "—":
        extra["employees"] = employees[:100]

    contacts, contact_flat = contacts_pack if isinstance(contacts_pack, tuple) else ([], {})
    if contacts:
        extra["contacts"] = contacts
        extra.update(contact_flat)
    elif contact and isinstance(contact, dict) and ctid:
        entry = _contact_entry(ctid, contact, is_primary=True)
        extra["contacts"] = [entry]
        extra.update(_flat_fields_from_primary(entry))

    company_title = ""
    if company and isinstance(company, dict):
        company_title = str(company.get("TITLE") or "").strip()
    if company_title and company_title != "—":
        extra["company"] = company_title[:255]

    bx = extract_bitrix_extra_from_row(row)
    if bx:
        extra["bitrix_extra"] = bx

    return extra


def merge_bitrix_field_updates(existing: Any, patch: dict[str, Any]) -> dict[str, Any]:
    """Не затирать inn/ogrn/contacts/bitrix_extra пустыми значениями при upsert."""
    out = dict(patch)
    for key in ("inn", "ogrn"):
        if not out.get(key) and getattr(existing, key, None):
            out.pop(key, None)
    for key in ("deal_amount", "deal_currency"):
        if not out.get(key) and getattr(existing, key, None):
            out.pop(key, None)
    if not out.get("contacts") and getattr(existing, "contacts", None):
        out.pop("contacts", None)
    elif "contacts" in out:
        merged = merge_bitrix_contacts(getattr(existing, "contacts", None), out.get("contacts"))
        if merged:
            out["contacts"] = merged
        else:
            out.pop("contacts", None)
    if "bitrix_extra" in out:
        merged = merge_bitrix_extra(
            getattr(existing, "bitrix_extra", None),
            out.get("bitrix_extra"),
        )
        if merged:
            out["bitrix_extra"] = merged
        else:
            out.pop("bitrix_extra", None)
    return out
