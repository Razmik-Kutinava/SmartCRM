"""Сегменты полноты карточки лида — core/lead_coverage.py."""
from __future__ import annotations

import json

from core.lead_coverage import (
    lead_coverage_flags,
    lead_coverage_segments,
    summarize_coverage,
)
from core.lead_coverage_attach import attach_lead_coverage_flags


def test_bitrix_full_segment():
    lead = {
        "id": 1,
        "bitrixLeadId": 100,
        "bitrixExtra": {"foo": "bar"},
        "contacts": [{"name": "Иван"}],
        "amount": "15000",
        "stage": "Новый",
    }
    segs = lead_coverage_segments(lead, tasks=[{"id": 1}])
    assert "bitrix_full" in segs
    assert "bitrix_empty" not in segs
    assert "no_tasks" not in segs


def test_bitrix_empty_with_bitrix_id():
    lead = {"id": 2, "bitrix_lead_id": 200, "stage": "Новый"}
    segs = lead_coverage_segments(lead, tasks=[])
    assert "bitrix_empty" in segs
    assert "no_tasks" in segs


def test_passport_from_inn():
    lead = {"id": 3, "inn": "7707083893", "stage": "Новый"}
    flags = lead_coverage_flags(lead, tasks=[{"id": 1}])
    assert flags["coveragePassport"] is True
    assert "passport" in flags["coverageSegments"]


def test_passport_from_tech_json():
    lead = {
        "id": 4,
        "tech_json": json.dumps({"checko": {"name": "ООО Тест"}}),
        "stage": "Новый",
    }
    assert lead_coverage_flags(lead)["coveragePassport"] is True


def test_lost_stage_segment():
    lead = {"id": 5, "stage": "Проигран", "company": "X"}
    segs = lead_coverage_segments(lead)
    assert "lost" in segs
    assert lead_coverage_flags(lead)["coverageLost"] is True


def test_card_ready_partial_with_passport():
    lead = {
        "id": 6,
        "bitrixLeadId": 1,
        "contacts": [{"name": "A"}],
        "inn": "123",
        "stage": "Новый",
    }
    segs = lead_coverage_segments(lead, tasks=[{"id": 1}])
    assert "bitrix_partial" in segs
    assert "card_ready" in segs


def test_attach_and_summarize():
    leads = [
        {"id": 1, "stage": "Новый", "bitrixLeadId": 1, "contacts": [{"n": 1}], "amount": "1"},
        {"id": 2, "stage": "Проигран"},
    ]
    tasks_by_lead = {1: [{"id": 10}], 2: []}
    enriched = attach_lead_coverage_flags(leads, tasks_by_lead)
    assert enriched[0]["coverageBitrixPartial"] is True
    assert enriched[1]["coverageLost"] is True
    assert enriched[1]["coverageNoTasks"] is True
    summary = summarize_coverage(enriched)
    assert summary["lost"] == 1
    assert summary["no_tasks"] == 1
