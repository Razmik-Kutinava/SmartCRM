"""
Подсказка балла и предупреждения по воронке (не перезаписывает score в БД).
Менеджер задаёт score; сервис только подсвечивает риски и даёт suggestedScore 0–100.
"""
from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal
from typing import Any, Optional

DEFAULT_SCORING_ADVISORY: dict[str, Any] = {
    "stages_requiring_amount_rub": ["КП отправлено", "Переговоры", "Выигран"],
    "late_stage_min_amount_rub": Decimal("1"),
    # Вклад в подсказку (0–100) за отмеченные апрувы; сумма режется approval_bonus_cap
    "approval_weights": {
        "lprEstablished": 5,
        "assortmentAgreed": 3,
        "priceAgreed": 4,
        "termsAgreed": 3,
        "paymentTermsAgreed": 3,
        "securityPassed": 4,
        "rebateAgreed": 2,
        "contractSigned": 5,
        "invoiceIssued": 3,
        "contractSent": 2,
        "contractSignedDoc": 3,
        "kpSent": 2,
        "presentationSent": 2,
        "licenseShipped": 4,
    },
    "approval_bonus_cap": 28,
    "suggested_score_by_stage": {
        "Новый": 28,
        "Квалифицирован": 42,
        "КП отправлено": 55,
        "Переговоры": 68,
        "Выигран": 88,
        "Проигран": 12,
    },
    "amount_bonus_cap": 18,
    "amount_bonus_per_100k_rub": 3,
    "overdue_open_task_penalty": 8,
    "overdue_penalty_cap": 24,
    "manager_score_divergence_warn_ratio": 0.32,
}


def _parse_due(s: Optional[str]) -> Optional[dt.date]:
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


def _decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _merge_advisory(settings: dict[str, Any]) -> dict[str, Any]:
    raw = settings.get("scoring_advisory")
    if not isinstance(raw, dict):
        raw = {}
    merged = {**DEFAULT_SCORING_ADVISORY, **raw}
    if isinstance(merged.get("late_stage_min_amount_rub"), (int, float, str)):
        merged["late_stage_min_amount_rub"] = _decimal(merged["late_stage_min_amount_rub"]) or Decimal("1")
    if isinstance(merged.get("suggested_score_by_stage"), dict):
        merged["suggested_score_by_stage"] = {
            str(k): int(v) for k, v in merged["suggested_score_by_stage"].items()
        }
    return merged


def _approval_bonus_points(lead: dict[str, Any], adv: dict[str, Any]) -> tuple[int, dict[str, int]]:
    ap = lead.get("approvals")
    if not isinstance(ap, dict):
        return 0, {}
    raw_w = adv.get("approval_weights")
    if not isinstance(raw_w, dict):
        return 0, {}
    weights: dict[str, int] = {}
    for k, v in raw_w.items():
        try:
            weights[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    detail: dict[str, int] = {}
    total = 0
    for k, wi in weights.items():
        if ap.get(k) is True:
            total += wi
            detail[k] = wi
    cap = int(adv.get("approval_bonus_cap") or 28)
    return min(total, cap), detail


def count_overdue_open_tasks(tasks: list[dict[str, Any]], today: dt.date) -> int:
    n = 0
    for t in tasks:
        if t.get("status") != "open":
            continue
        d = _parse_due(t.get("due")) or _parse_due(t.get("slaDue"))
        if d and d < today:
            n += 1
    return n


def compute_lead_score_advisory(
    lead: dict[str, Any],
    tasks: list[dict[str, Any]],
    settings: dict[str, Any],
) -> dict[str, Any]:
    """
    Возвращает suggestedScore (0–100), warnings (строки для UI), breakdown.
    Не изменяет lead в БД.
    """
    adv = _merge_advisory(settings)
    stages_req = [str(x).strip() for x in (adv.get("stages_requiring_amount_rub") or []) if str(x).strip()]
    min_amt: Decimal = adv["late_stage_min_amount_rub"]
    by_stage: dict[str, int] = adv.get("suggested_score_by_stage") or {}
    today = dt.date.today()

    stage = str(lead.get("stage") or "Новый").strip()
    manager_score = int(lead.get("score") or 0)
    manager_score = max(0, min(100, manager_score))

    amount = _decimal(lead.get("amountRub") or lead.get("amount_rub"))
    paid = _decimal(lead.get("paidAmountRub") or lead.get("paid_amount_rub"))

    warnings: list[str] = []
    breakdown: dict[str, Any] = {"stage": stage, "managerScore": manager_score}

    if stage in stages_req:
        if amount is None or amount < min_amt:
            warnings.append(
                f"На этапе «{stage}» обычно нужна сумма сделки в ₽. Укажите сумму, чтобы сопоставлять оплату и приоритет."
            )

    if amount is not None and paid is not None and paid > amount:
        warnings.append("Оплачено больше, чем сумма сделки — проверьте суммы (₽).")

    overdue_n = count_overdue_open_tasks(tasks, today)
    breakdown["overdueOpenTasks"] = overdue_n
    if overdue_n > 0:
        warnings.append(f"Есть просроченные открытые задачи: {overdue_n}. Закройте или перенесите срок.")

    base = int(by_stage.get(stage, 45))
    breakdown["baseFromStage"] = base

    amount_bonus = 0
    if amount is not None and amount > 0:
        per_100k = float(adv.get("amount_bonus_per_100k_rub") or 3)
        cap = int(adv.get("amount_bonus_cap") or 18)
        step = float(amount) / 100_000.0 * per_100k
        amount_bonus = min(cap, int(round(step)))
    breakdown["amountBonus"] = amount_bonus

    ap_bonus, ap_detail = _approval_bonus_points(lead, adv)
    breakdown["approvalBonus"] = ap_bonus
    breakdown["approvalDetails"] = ap_detail

    pen = int(adv.get("overdue_open_task_penalty") or 8)
    cap_pen = int(adv.get("overdue_penalty_cap") or 24)
    overdue_penalty = min(cap_pen, overdue_n * pen)
    breakdown["overduePenalty"] = overdue_penalty

    suggested = base + amount_bonus + ap_bonus - overdue_penalty
    suggested = max(0, min(100, int(round(suggested))))
    breakdown["suggestedScore"] = suggested

    ratio = float(adv.get("manager_score_divergence_warn_ratio") or 0.32)
    if abs(manager_score - suggested) / 100.0 >= ratio:
        warnings.append(
            f"Балл менеджера ({manager_score}) заметно отличается от расчётной подсказки ({suggested}). Проверьте актуальность этапа, сумм и задач."
        )

    return {
        "suggestedScore": suggested,
        "warnings": warnings,
        "breakdown": breakdown,
    }
