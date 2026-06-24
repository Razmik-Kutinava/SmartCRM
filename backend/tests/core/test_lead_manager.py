"""Менеджер лида — core/lead_manager.py."""
from __future__ import annotations

from core.lead_manager import (
    catalog_managers,
    lead_manager_label,
    lead_manager_names,
    lead_matches_manager_filter,
    normalize_manager_key,
)
from core.lead_manager_attach import attach_lead_manager_labels


def test_manager_label_from_bitrix_extra():
    lead = {
        "responsible": "Иванов",
        "bitrixExtra": {"manager": "Гюрджян Размик"},
    }
    assert lead_manager_label(lead) == "Гюрджян Размик"
    assert "Гюрджян Размик" in lead_manager_names(lead)
    assert "Иванов" in lead_manager_names(lead)


def test_manager_label_fallback_responsible():
    lead = {"responsible": "Петров", "bitrixExtra": {}}
    assert lead_manager_label(lead) == "Петров"


def test_manager_filter_matches_either_field():
    lead = {"responsible": "Иванов", "bitrixExtra": {"manager": "Гюрджян Размик"}}
    assert lead_matches_manager_filter(lead, "Гюрджян Размик")
    assert lead_matches_manager_filter(lead, "иванов")
    assert not lead_matches_manager_filter(lead, "Сидоров")


def test_catalog_managers_counts():
    leads = [
        {"responsible": "А", "bitrixExtra": {}},
        {"responsible": "А", "bitrixExtra": {"manager": "Б"}},
        {"responsible": "Б", "bitrixExtra": {}},
    ]
    cat = catalog_managers(leads)
    names = {row["name"]: row["count"] for row in cat}
    assert names["А"] == 2
    assert names["Б"] == 2


def test_attach_manager_name():
    leads = [{"responsible": "Менеджер", "bitrixExtra": {}}]
    out = attach_lead_manager_labels(leads)
    assert out[0]["managerName"] == "Менеджер"
    assert out[0]["managerNames"] == ["Менеджер"]


def test_normalize_manager_key():
    assert normalize_manager_key("  Гюрджян   Размик ") == "гюрджян размик"
