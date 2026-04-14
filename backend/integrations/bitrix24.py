"""
Клиент входящего вебхука Битрикс24: выгрузка лидов в SmartCRM.
Переменная окружения: BITRIX24_WEBHOOK_URL — базовый URL без имени метода, напр.
https://ваш-портал/rest/112/секрет/
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead import Lead

logger = logging.getLogger(__name__)

_DEFAULT_DATE_FROM = "2023-01-01"
_PAGE = 50


class BitrixWebhookError(RuntimeError):
    """Ошибка URL/секрета вебхука или отсутствие нужных прав (scope) в Битрикс24."""


def webhook_base() -> str:
    raw = (os.getenv("BITRIX24_WEBHOOK_URL") or "").strip()
    if len(raw) >= 2 and raw[0] in "\"'" and raw[0] == raw[-1]:
        raw = raw[1:-1].strip()
    return raw.rstrip("/")


def _handle_bitrix_http(method: str, r: httpx.Response) -> dict[str, Any]:
    """Разбирает ответ Битрикс24: ошибки часто приходят в JSON при HTTP 401, не только 200."""
    text = r.text or ""
    try:
        data = r.json()
    except Exception:
        snippet = text[:400].replace("\n", " ")
        if r.status_code == 401:
            raise BitrixWebhookError(
                f"Битрикс24 отклонил запрос {method} (HTTP 401). "
                "Проверьте BITRIX24_WEBHOOK_URL, что вебхук не отозван и что у него есть права CRM."
            ) from None
        raise BitrixWebhookError(
            f"Битрикс24 {method}: ответ не JSON (HTTP {r.status_code}): {snippet}"
        ) from None

    if not isinstance(data, dict):
        raise BitrixWebhookError(f"Битрикс24 {method}: неожиданный формат ответа")

    err = data.get("error")
    desc = (data.get("error_description") or "").strip()
    combined = f"{err} {desc}".lower()

    if r.status_code >= 400 or err:
        code = str(err or "")

        if (
            r.status_code == 401
            and (
                code == "insufficient_scope"
                or "insufficient_scope" in combined
                or "requires higher privileges" in combined
            )
        ):
            raise BitrixWebhookError(
                "У вебхука нет прав на CRM (insufficient_scope). В Битрикс24: разработчикам → вебхуки "
                "→ ваш входящий вебхук → настройка прав: включите «CRM (crm)» и «Пользователи (user)», "
                "сохраните, скопируйте новый URL в .env как BITRIX24_WEBHOOK_URL и перезапустите бэкенд."
            ) from None

        if code in ("NO_AUTH_FOUND", "INVALID_CREDENTIALS", "expired_token"):
            raise BitrixWebhookError(
                "Битрикс24: INVALID_CREDENTIALS — секрет в URL не совпадает с вебхуком. "
                "Скопируйте полный URL ещё раз из карточки вебхука (строка «Вебхук для вызова rest api», "
                "со слэшем в конце, без текста `.json` в пути) в файл .env в корне проекта SmartCRM: "
                "BITRIX24_WEBHOOK_URL=https://.../rest/USER/секрет/ "
                "Перезапустите uvicorn. Если только что меняли права — Битрикс мог выдать новый секрет."
            ) from None

        if r.status_code == 401:
            raise BitrixWebhookError(
                f"Битрикс24 отклонил {method} (HTTP 401): {desc or code or text[:200]}"
            ) from None

        if err:
            raise BitrixWebhookError(f"Битрикс24 {method}: {desc or code}") from None

        raise BitrixWebhookError(f"Битрикс24 {method}: HTTP {r.status_code} — {desc or text[:200]}") from None

    if data.get("error"):
        raise BitrixWebhookError(
            f"Битрикс24 {method}: {data.get('error_description') or data.get('error')}"
        )

    return data


async def bitrix_call(method: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    base = webhook_base()
    if not base:
        raise BitrixWebhookError(
            "В .env не задан BITRIX24_WEBHOOK_URL. Укажите базовый URL вебхука со слэшем в конце, "
            "например: https://ваш-портал/rest/112/секрет/"
        )
    url = f"{base}/{method}"
    payload = params or {}
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, json=payload)
    return _handle_bitrix_http(method, r)


def _first_multi(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, str) and val.strip():
        return val.strip()
    if isinstance(val, list) and val:
        item = val[0]
        if isinstance(item, dict):
            v = item.get("VALUE")
            return str(v).strip() if v else "—"
        return str(item)
    if isinstance(val, dict) and "VALUE" in val:
        return str(val.get("VALUE") or "").strip() or "—"
    return "—"


def _all_phones(val: Any) -> str:
    if not val:
        return "—"
    if isinstance(val, list):
        parts = []
        for item in val:
            if isinstance(item, dict) and item.get("VALUE"):
                parts.append(str(item["VALUE"]).strip())
        return ", ".join(parts) if parts else "—"
    return _first_multi(val)


def _budget(row: dict) -> str:
    opp = row.get("OPPORTUNITY")
    cur = row.get("CURRENCY_ID") or ""
    if opp in (None, "", False):
        return "—"
    try:
        num = float(opp)
        if num == int(num):
            num_s = str(int(num))
        else:
            num_s = str(num)
    except (TypeError, ValueError):
        num_s = str(opp)
    return f"{num_s} {cur}".strip() if cur else num_s


def _guess_inn(row: dict) -> Optional[str]:
    inn_re = re.compile(r"^\d{10}(\d{2})?$")
    for key, val in row.items():
        if not str(key).startswith("UF_"):
            continue
        if isinstance(val, list) and val and isinstance(val[0], dict):
            val = val[0].get("VALUE")
        if isinstance(val, str) and inn_re.match(val.strip()):
            return val.strip()
    return None


def _contact_name(row: dict) -> str:
    parts = [row.get("NAME"), row.get("LAST_NAME"), row.get("SECOND_NAME")]
    s = " ".join(p for p in parts if p and str(p).strip())
    return s.strip() or "—"


def _company_title(row: dict) -> str:
    t = (row.get("TITLE") or "").strip()
    c = (row.get("COMPANY_TITLE") or "").strip()
    if t:
        return t
    if c:
        return c
    return "Без названия"


def _tech_json_for_row(row: dict, b_id: int) -> str:
    uf = {k: v for k, v in row.items() if str(k).startswith("UF_")}
    blob = {
        "bitrix24": {
            "lead_id": b_id,
            "status_id": row.get("STATUS_ID"),
            "source_id": row.get("SOURCE_ID"),
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "uf": uf,
        }
    }
    return json.dumps(blob, ensure_ascii=False)


async def _load_source_names() -> dict[str, str]:
    names: dict[str, str] = {}
    try:
        data = await bitrix_call(
            "crm.status.list",
            {"filter": {"ENTITY_ID": "SOURCE"}, "order": {"SORT": "ASC"}},
        )
        for row in data.get("result", []):
            sid = row.get("STATUS_ID")
            if sid:
                names[str(sid)] = (row.get("NAME") or sid)[:100]
    except BitrixWebhookError:
        raise
    except Exception as e:
        logger.warning("crm.status.list SOURCE: %s", e)
    return names


async def _load_status_names() -> dict[str, str]:
    """STATUS_ID → человекочитаемое имя (лиды)."""
    names: dict[str, str] = {}
    try:
        data = await bitrix_call(
            "crm.status.list",
            {"filter": {"ENTITY_ID": "STATUS"}, "order": {"SORT": "ASC"}},
        )
        for row in data.get("result", []):
            sid = row.get("STATUS_ID")
            if sid:
                names[str(sid)] = (row.get("NAME") or sid)[:100]
    except BitrixWebhookError:
        raise
    except Exception as e:
        logger.warning("crm.status.list: %s", e)
    return names


_user_cache: dict[int, str] = {}


async def _load_user_names(ids: set[int]) -> dict[int, str]:
    out: dict[int, str] = {}
    for uid in ids:
        if uid in _user_cache:
            out[uid] = _user_cache[uid]
            continue
        try:
            data = await bitrix_call("user.get", {"ID": uid})
            rows = data.get("result")
            if not rows:
                _user_cache[uid] = f"#{uid}"
                out[uid] = _user_cache[uid]
                continue
            u = rows[0] if isinstance(rows, list) else rows
            name = " ".join(
                x for x in [u.get("NAME"), u.get("LAST_NAME")] if x
            ).strip()
            label = (name or u.get("EMAIL") or str(uid))[:255]
            _user_cache[uid] = label
            out[uid] = label
        except BitrixWebhookError:
            raise
        except Exception as e:
            logger.debug("user.get %s: %s", uid, e)
            _user_cache[uid] = f"#{uid}"
            out[uid] = _user_cache[uid]
    return out


def row_to_lead_fields(
    row: dict,
    *,
    status_names: dict[str, str],
    user_names: dict[int, str],
    source_names: dict[str, str],
) -> dict[str, Any]:
    b_id = int(row["ID"])
    assigned = row.get("ASSIGNED_BY_ID")
    try:
        aid = int(assigned) if assigned is not None else None
    except (TypeError, ValueError):
        aid = None
    responsible = user_names.get(aid, "—") if aid is not None else "—"

    st = row.get("STATUS_ID")
    stage = status_names.get(str(st), str(st)[:100] if st is not None else "Новый")

    city = (row.get("ADDRESS_CITY") or "").strip() or "—"
    country = (row.get("ADDRESS_COUNTRY") or "").strip()
    industry = country if country else "—"

    inn = _guess_inn(row)
    desc = (row.get("COMMENTS") or "").strip()
    if row.get("SOURCE_DESCRIPTION"):
        desc = (desc + "\n" + str(row["SOURCE_DESCRIPTION"])).strip()

    return {
        "company": _company_title(row)[:255],
        "contact": _contact_name(row)[:255],
        "email": _first_multi(row.get("EMAIL"))[:255],
        "phone": _all_phones(row.get("PHONE"))[:100],
        "stage": stage or "—",
        "score": 50,
        "source": (
            source_names.get(str(row.get("SOURCE_ID") or ""), str(row.get("SOURCE_ID") or "—"))
            if row.get("SOURCE_ID") not in (None, "")
            else "—"
        )[:100],
        "budget": _budget(row)[:100],
        "position": (str(row.get("POST") or "—"))[:255],
        "website": _first_multi(row.get("WEB"))[:255] if row.get("WEB") else "—",
        "employees": "—",
        "industry": industry[:255],
        "city": city[:255],
        "responsible": responsible[:255],
        "next_call": "—",
        "description": desc,
        "inn": inn,
        "bitrix_lead_id": b_id,
        "tech_json": _tech_json_for_row(row, b_id),
    }


async def import_leads_from_bitrix(
    db: AsyncSession,
    *,
    date_from: str = _DEFAULT_DATE_FROM,
    max_items: int = 10000,
) -> dict[str, Any]:
    """
    Постранично тянет crm.lead.list с DATE_CREATE >= date_from, upsert по bitrix_lead_id.
    """
    status_names = await _load_status_names()
    source_names = await _load_source_names()
    start = 0
    imported = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    # Существующие bitrix ids
    res = await db.execute(select(Lead.bitrix_lead_id).where(Lead.bitrix_lead_id.isnot(None)))
    existing_ids = {row[0] for row in res.fetchall() if row[0] is not None}

    total_processed = 0
    while total_processed < max_items:
        user_ids: set[int] = set()
        try:
            data = await bitrix_call(
                "crm.lead.list",
                {
                    "filter": {">=DATE_CREATE": date_from},
                    "select": ["*"],
                    "order": {"DATE_CREATE": "DESC"},
                    "start": start,
                },
            )
        except BitrixWebhookError:
            raise
        except Exception as e:
            errors.append(str(e))
            logger.exception("crm.lead.list failed at start=%s", start)
            break

        rows = data.get("result") or []
        if not rows:
            break

        for row in rows:
            uid = row.get("ASSIGNED_BY_ID")
            try:
                if uid is not None:
                    user_ids.add(int(uid))
            except (TypeError, ValueError):
                pass

        user_names = await _load_user_names(user_ids)
        user_ids.clear()

        for row in rows:
            if total_processed >= max_items:
                break
            total_processed += 1
            try:
                b_id = int(row["ID"])
                fields = row_to_lead_fields(
                    row,
                    status_names=status_names,
                    user_names=user_names,
                    source_names=source_names,
                )

                if b_id in existing_ids:
                    r2 = await db.execute(select(Lead).where(Lead.bitrix_lead_id == b_id))
                    lead = r2.scalar_one_or_none()
                    if lead:
                        for k, v in fields.items():
                            if k == "score":
                                continue
                            setattr(lead, k, v)
                        updated += 1
                    else:
                        skipped += 1
                else:
                    lead = Lead(**fields)
                    db.add(lead)
                    existing_ids.add(b_id)
                    imported += 1

            except Exception as e:
                errors.append(f"lead {row.get('ID')}: {e}")
                logger.exception("import row")

        await db.commit()

        if "next" in data and data["next"] is not None:
            start = int(data["next"])
        else:
            break

    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "total_processed": total_processed,
        "errors": errors[:20],
        "error_count": len(errors),
    }
