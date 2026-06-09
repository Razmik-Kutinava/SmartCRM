"""Маппинг list_leads слотов → UI фильтры."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.hermes.lead_list_view import list_leads_view_from_slots


def test_stage_filter():
    v = list_leads_view_from_slots({"filter": "all", "stage": "переговоры"})
    assert v["filterStage"] == "Переговоры"


def test_industry_city():
    v = list_leads_view_from_slots({"industry": "IT", "city": "Москва"})
    assert v["industry"] == "IT"
    assert v["city"] == "Москва"


def test_stage_fuzzy_from_crm():
    v = list_leads_view_from_slots({"stage": "переговор"})
    assert v["filterStage"] == "Переговоры"
