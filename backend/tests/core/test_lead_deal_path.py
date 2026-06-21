"""Путь сделки и подсказки по этапу."""
from __future__ import annotations

import datetime as dt

from core.lead_deal_path import PRE_KP_APPROVAL_KEYS, build_deal_path, next_incomplete_step
from core.lead_stage_hints import compute_stage_hints, days_on_stage


def test_deal_path_order_includes_kp_after_rebate():
    lead = {
        "company": "ООО Тест",
        "contact": "Иван",
        "phone": "+7",
        "email": "—",
        "stage": "Квалифицирован",
        "approvals": {k: False for k in PRE_KP_APPROVAL_KEYS},
    }
    path = build_deal_path(lead)
    pre = next(g for g in path["groups"] if g["id"] == "pre_kp")
    keys = [s["key"] for s in pre["steps"]]
    assert keys.index("rebateAgreed") < keys.index("kpSent")


def test_stage_stale_hint_critical():
    lead = {"stage": "Новый", "approvals": {}, "company": "X", "contact": "Y", "phone": "1"}
    entered = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=4)
    hints = compute_stage_hints(lead, stage_entered_at=entered, last_comm_at=None, settings={})
    codes = [h["code"] for h in hints]
    assert "stage_stale" in codes
    assert hints[0]["severity"] == "critical"


def test_deal_path_lpr_from_contacts():
    lead = {
        "company": "A",
        "contact": "—",
        "phone": "—",
        "email": "—",
        "contacts": [
            {
                "name": "Иван",
                "role": "lpr",
                "position": "ГД",
                "phones": ["+7999"],
                "emails": [],
                "messengers": [],
            }
        ],
        "approvals": {},
    }
    path = build_deal_path(lead)
    qual = next(g for g in path["groups"] if g["id"] == "qualification")
    lpr_step = next(s for s in qual["steps"] if s["key"] == "lprEstablished")
    assert lpr_step["done"] is True
    assert lpr_step["kind"] == "derived"


def test_next_incomplete_step_lpr():
    lead = {
        "company": "A",
        "contact": "B",
        "phone": "1",
        "email": "—",
        "approvals": {},
    }
    nxt = next_incomplete_step(lead)
    assert nxt is not None
    assert nxt["key"] in ("company", "contact", "phone_or_email", "lprEstablished")


def test_days_on_stage():
    today = dt.date(2026, 6, 19)
    entered = dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc)
    assert days_on_stage(entered, today) == 4
