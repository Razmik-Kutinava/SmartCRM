"""
Валидация смены стадии лида (P2) — правила из crm_settings.stage_transition_rules.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any


VALIDATION_KEYS = frozenset(
    {
        "stage",
        "company",
        "contact",
        "email",
        "phone",
        "description",
        "budget",
        "source",
        "score",
        "amount_rub",
        "paid_amount_rub",
        "position",
        "website",
        "employees",
        "industry",
        "city",
        "responsible",
        "next_call",
    }
)


def _is_nonempty_scalar(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, Decimal):
        return val != 0
    if isinstance(val, (int, float)):
        return True
    s = str(val).strip()
    return bool(s) and s != "—"


def merge_lead_patch_for_validation(lead: Any, patch: dict[str, Any]) -> dict[str, Any]:
    """Снимок полей после применения patch (без записи в ORM)."""
    merged: dict[str, Any] = {}
    for k in VALIDATION_KEYS:
        merged[k] = getattr(lead, k, None)
    for k, v in patch.items():
        if k in VALIDATION_KEYS:
            merged[k] = v
    return merged


def validate_stage_transition(
    settings: dict[str, Any],
    merged_lead: dict[str, Any],
    old_stage: str,
    new_stage: str,
) -> list[str]:
    """
    Возвращает список сообщений об ошибках; пустой список = можно переходить.
    """
    if new_stage == old_stage:
        return []
    stages = settings.get("stages") or []
    if stages and new_stage not in stages:
        return [f"Стадия «{new_stage}» не входит в конфигурацию воронки."]
    rules = settings.get("stage_transition_rules") or []
    if not isinstance(rules, list):
        return []
    errors: list[str] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("to_stage") != new_stage:
            continue
        for field in rule.get("require_non_empty") or []:
            if field not in VALIDATION_KEYS:
                errors.append(f"Правило ссылается на неизвестное поле: {field}")
                continue
            if not _is_nonempty_scalar(merged_lead.get(field)):
                label = str(field)
                errors.append(
                    f"Переход в «{new_stage}» требует заполненного поля «{label}»."
                )
        if rule.get("require_positive_amount_rub"):
            amt = merged_lead.get("amount_rub")
            ok = False
            if isinstance(amt, Decimal):
                ok = amt > 0
            elif isinstance(amt, (int, float)):
                ok = amt > 0
            if not ok:
                errors.append(
                    f"Переход в «{new_stage}» требует суммы сделки (amount_rub) больше 0."
                )
    return errors
