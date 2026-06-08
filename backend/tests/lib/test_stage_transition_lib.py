"""Зеркало frontend/src/lib/leads/stageTransition.js (логика подсказок)."""

FIELD_LABELS = {
    "email": "Email",
    "company": "Компания",
    "amount_rub": "Сумма ₽",
}


def audit_field_label(field: str) -> str:
    return FIELD_LABELS.get(field, field)


def describe_transition_rule(rule: dict | None) -> str:
    if not rule or not isinstance(rule, dict):
        return ""
    parts = []
    for f in rule.get("require_non_empty") or []:
        parts.append(audit_field_label(str(f)))
    if rule.get("require_positive_amount_rub"):
        parts.append("сумма ₽ > 0")
    return ", ".join(parts)


def rules_for_target_stage(rules: list | None, stage: str) -> list:
    if not isinstance(rules, list):
        return []
    return [r for r in rules if isinstance(r, dict) and r.get("to_stage") == stage]


def test_describe_transition_rule():
    rule = {"to_stage": "Выигран", "require_non_empty": ["email", "company"], "require_positive_amount_rub": True}
    text = describe_transition_rule(rule)
    assert "Email" in text
    assert "Компания" in text
    assert "сумма" in text


def test_rules_for_target_stage():
    rules = [
        {"to_stage": "Выигран", "require_non_empty": ["email"]},
        {"to_stage": "Проигран", "require_non_empty": ["phone"]},
    ]
    won = rules_for_target_stage(rules, "Выигран")
    assert len(won) == 1
    assert won[0]["require_non_empty"] == ["email"]
