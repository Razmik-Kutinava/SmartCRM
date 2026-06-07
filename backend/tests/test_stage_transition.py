"""Правила перехода стадий (P2) — без БД."""
from types import SimpleNamespace

from core.stage_transition import merge_lead_patch_for_validation, validate_stage_transition


def _lead(**kwargs):
    base = dict(
        stage="Новый",
        company="ООО Тест",
        contact="—",
        email="—",
        phone="—",
        description="",
        budget="—",
        source="—",
        score=50,
        amount_rub=None,
        paid_amount_rub=None,
        position="—",
        website="—",
        employees="—",
        industry="—",
        city="—",
        responsible="Я",
        next_call="—",
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_empty_rules_allow_any_stage():
    lead = _lead()
    settings = {"stages": ["Новый", "Выигран"], "stage_transition_rules": []}
    merged = merge_lead_patch_for_validation(lead, {"stage": "Выигран"})
    assert validate_stage_transition(settings, merged, "Новый", "Выигран") == []


def test_require_email_for_won():
    lead = _lead(email="—", company="X")
    settings = {
        "stages": ["Новый", "Выигран"],
        "stage_transition_rules": [
            {"to_stage": "Выигран", "require_non_empty": ["email", "company"]},
        ],
    }
    merged = merge_lead_patch_for_validation(lead, {"stage": "Выигран"})
    errs = validate_stage_transition(settings, merged, "Новый", "Выигран")
    assert any("email" in e.lower() for e in errs)

    lead2 = _lead(email="a@b.ru", company="X")
    merged2 = merge_lead_patch_for_validation(lead2, {"stage": "Выигран"})
    assert validate_stage_transition(settings, merged2, "Новый", "Выигран") == []


def test_require_positive_amount_rub():
    lead = _lead(email="a@b.ru", company="X", amount_rub=None)
    settings = {
        "stages": ["Новый", "Выигран"],
        "stage_transition_rules": [
            {"to_stage": "Выигран", "require_positive_amount_rub": True},
        ],
    }
    merged = merge_lead_patch_for_validation(lead, {"stage": "Выигран"})
    assert len(validate_stage_transition(settings, merged, "Новый", "Выигран")) >= 1

    merged_ok = merge_lead_patch_for_validation(
        _lead(email="a@b.ru", company="X", amount_rub=100),
        {"stage": "Выигран"},
    )
    assert validate_stage_transition(settings, merged_ok, "Новый", "Выигран") == []


def test_unknown_stage_rejected():
    lead = _lead()
    settings = {"stages": ["Новый"], "stage_transition_rules": []}
    merged = merge_lead_patch_for_validation(lead, {"stage": "Фантазия"})
    errs = validate_stage_transition(settings, merged, "Новый", "Фантазия")
    assert errs and "Фантазия" in errs[0]
