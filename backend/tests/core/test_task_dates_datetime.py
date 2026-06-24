"""parse_task_datetime."""
from __future__ import annotations

import datetime as dt

from core.task_dates import parse_task_datetime


def test_parse_with_time():
    out = parse_task_datetime("24.06.2026 08:30")
    assert out == dt.datetime(2026, 6, 24, 8, 30)


def test_parse_date_only():
    out = parse_task_datetime("24.06.2026")
    assert out == dt.datetime(2026, 6, 24, 0, 0)
