"""Парсинг дат и SLA задач."""
from __future__ import annotations

import datetime as dt

from core.task_dates import parse_task_date, sla_status_label


def test_parse_task_date_dot_format():
    assert parse_task_date("18.04.2026") == dt.date(2026, 4, 18)


def test_parse_task_date_iso():
    assert parse_task_date("2026-04-18") == dt.date(2026, 4, 18)


def test_sla_status_overdue():
    assert (
        sla_status_label(status="open", sla_due="01.01.2020", today=dt.date(2026, 6, 8))
        == "overdue"
    )


def test_sla_status_done():
    assert sla_status_label(status="done", sla_due="01.01.2020") == "done"
