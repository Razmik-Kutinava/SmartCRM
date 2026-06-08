"""Парсинг дат задач и статус SLA."""
from __future__ import annotations

import datetime as dt
import re
from typing import Optional


def parse_task_date(s: Optional[str]) -> Optional[dt.date]:
    if not s or not str(s).strip() or str(s).strip() == "—":
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(\s|$)", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    m2 = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m2:
        y, mo, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    return None


def sla_status_label(*, status: str, sla_due: Optional[str], today: Optional[dt.date] = None) -> str:
    if status == "done":
        return "done"
    if not sla_due:
        return "no_sla"
    d = parse_task_date(sla_due)
    if not d:
        return "unknown"
    ref = today or dt.date.today()
    if d < ref:
        return "overdue"
    if d == ref:
        return "today"
    return "ok"
