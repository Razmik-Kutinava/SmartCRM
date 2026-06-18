"""Календарь дедлайнов тендеров и скан напоминаний."""
from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict
from typing import Any

from api.routes.tenders.helpers import _parse_any_date
from core import ops_store
from services.tender_notifications import add_notification
from services.tender_tracked import list_tracked, tender_row_for_calendar

# дни до дедлайна → уведомление
_DEADLINE_THRESHOLDS: tuple[tuple[int, str, str], ...] = (
    (7, "deadline_7d", "Через 7 дней дедлайн"),
    (3, "deadline_3d", "Через 3 дня дедлайн"),
    (1, "deadline_1d", "Завтра дедлайн подачи"),
    (0, "deadline_today", "Сегодня дедлайн подачи"),
)


def parse_tender_deadline(raw: Any) -> dt.date | None:
    if raw is None:
        return None
    if isinstance(raw, dt.date) and not isinstance(raw, dt.datetime):
        return raw
    if isinstance(raw, dt.datetime):
        return raw.date()
    parsed = _parse_any_date(str(raw))
    if isinstance(parsed, dt.datetime):
        return parsed.date()
    if isinstance(parsed, dt.date):
        return parsed
    return None


def _days_until(deadline: dt.date, today: dt.date | None = None) -> int:
    ref = today or dt.date.today()
    return (deadline - ref).days


async def collect_tender_rows(db) -> list[dict[str, Any]]:
    """Сохранённые «Мои» + отслеживаемые мониторингом."""
    from sqlalchemy import select

    from db.models.tender_saved import TenderSaved

    rows: list[dict[str, Any]] = []
    result = await db.execute(
        select(TenderSaved).where(TenderSaved.status == "saved").order_by(TenderSaved.updated_at.desc())
    )
    for row in result.scalars().all():
        snap = row.snapshot_json or {}
        fp = f"saved:{row.external_id}"
        rows.append(
            tender_row_for_calendar(
                fp=fp,
                title=row.to_dict().get("title") or "Тендер",
                deadline=snap.get("deadline") or snap.get("date_end"),
                url=snap.get("url") or "#",
                source=row.source or snap.get("source") or "",
                saved_id=row.id,
            )
        )
    for t in list_tracked():
        rows.append(
            tender_row_for_calendar(
                fp=t.get("fp") or "",
                title=t.get("title") or "Тендер",
                deadline=t.get("deadline"),
                url=t.get("url") or "#",
                source=t.get("source") or "",
                watch_id=t.get("watch_id"),
            )
        )
    return rows


async def calendar_month(db, year: int, month: int) -> dict[str, Any]:
    weeks = calendar.monthcalendar(year, month)
    by_day: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, int]] = set()

    for row in await collect_tender_rows(db):
        d = parse_tender_deadline(row.get("deadline"))
        if not d or d.year != year or d.month != month:
            continue
        key = (row.get("fp") or row.get("title", ""), d.day)
        if key in seen:
            continue
        seen.add(key)
        entry = dict(row)
        entry["deadlineDate"] = d.isoformat()
        entry["daysLeft"] = _days_until(d)
        by_day[d.day].append(entry)

    return {
        "year": year,
        "month": month,
        "weeks": weeks,
        "weekday_labels": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "tenders_by_day": {str(k): v for k, v in sorted(by_day.items())},
        "total_with_deadline": sum(len(v) for v in by_day.values()),
    }


def _push_ops_urgent(title: str, detail: str, key: str) -> None:
    qid = f"auto-tender-deadline-{key}"[:120]
    items = ops_store.load_queue()
    if any(x.get("id") == qid and x.get("status") == "open" for x in items):
        return
    items.insert(
        0,
        {
            "id": qid,
            "severity": "high",
            "title": title,
            "detail": detail,
            "kind": "tender_deadline",
            "status": "open",
            "created_ts": __import__("time").time(),
            "trace_ids": [],
        },
    )
    ops_store.save_queue(items)


async def scan_deadline_notifications(db) -> dict[str, Any]:
    today = dt.date.today()
    created = 0
    ops = 0

    for row in await collect_tender_rows(db):
        d = parse_tender_deadline(row.get("deadline"))
        if not d:
            continue
        days = _days_until(d, today)
        fp = row.get("fp") or row.get("title", "")
        title = (row.get("title") or "Тендер")[:120]
        url = row.get("url") or ""

        if days < 0:
            key = f"{fp}:overdue"
            if add_notification(
                kind="deadline_overdue",
                title=f"Просрочен дедлайн: {title}",
                detail=f"Дедлайн был {d.strftime('%d.%m.%Y')}. {url}",
                dedupe_key=key,
                tender=row,
                severity="high",
            ):
                created += 1
                _push_ops_urgent(f"Просрочен тендер: {title}", f"Дедлайн {d.strftime('%d.%m.%Y')}", key)
                ops += 1
            continue

        for threshold, kind, prefix in _DEADLINE_THRESHOLDS:
            if days != threshold:
                continue
            key = f"{fp}:{kind}"
            if add_notification(
                kind=kind,
                title=f"{prefix}: {title}",
                detail=f"Подать до {d.strftime('%d.%m.%Y')}. {url}",
                dedupe_key=key,
                tender=row,
                severity="high" if threshold <= 1 else "medium",
            ):
                created += 1
                if threshold <= 1:
                    _push_ops_urgent(f"{prefix}: {title}", f"До {d.strftime('%d.%m.%Y')}", key)
                    ops += 1

    return {"notifications_created": created, "ops_queued": ops, "scanned": True}
