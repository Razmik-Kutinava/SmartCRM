"""Прогноз закрытия сделки по стадии и баллу (модель Экономиста, без LLM)."""
from __future__ import annotations

from typing import Any

from core.analytics_metrics import WON_STAGE, LOST_STAGE, lead_amount_rub, normalize_stage

# Базовая вероятность закрытия по стадии воронки (историческая эвристика)
STAGE_CLOSE_BASE_PCT: dict[str, float] = {
    "Новый": 8.0,
    "Квалифицирован": 18.0,
    "КП отправлено": 35.0,
    "Переговоры": 58.0,
    "Выигран": 100.0,
    "Проигран": 0.0,
}

TIER_HIGH = "high"
TIER_MEDIUM = "medium"
TIER_LOW = "low"


def _tier(probability_pct: float) -> str:
    if probability_pct >= 55:
        return TIER_HIGH
    if probability_pct >= 25:
        return TIER_MEDIUM
    return TIER_LOW


def forecast_lead_close(
    lead: dict[str, Any],
    stages: list[str] | None = None,
) -> dict[str, Any]:
    """Вероятность закрытия одного лида: стадия + скоринг."""
    sts = stages or list(STAGE_CLOSE_BASE_PCT.keys())
    stage = normalize_stage(lead.get("stage"), sts)
    score = max(0, min(100, int(float(lead.get("score") or 50))))

    if stage == WON_STAGE:
        prob = 100.0
        rationale = "Сделка уже выиграна."
    elif stage == LOST_STAGE:
        prob = 0.0
        rationale = "Сделка проиграна."
    else:
        base = STAGE_CLOSE_BASE_PCT.get(stage, 10.0)
        # Экономист: стадия даёт базу, балл лида сдвигает прогноз
        prob = round(base * 0.55 + score * 0.45, 1)
        prob = max(1.0, min(95.0, prob))
        rationale = f"Стадия «{stage}» ({base}%) + балл {score} → оценка Экономиста."

    amount = lead_amount_rub(lead)
    expected_rub = round(amount * prob / 100) if amount is not None else None

    return {
        "leadId": lead.get("id"),
        "company": lead.get("company") or "—",
        "stage": stage,
        "score": score,
        "source": lead.get("source") or "—",
        "closeProbabilityPct": prob,
        "tier": _tier(prob),
        "expectedRub": expected_rub,
        "amountRub": amount,
        "rationale": rationale,
    }


def compute_closure_forecast(
    leads: list[dict[str, Any]],
    stages: list[str] | None = None,
    *,
    top_limit: int = 15,
) -> dict[str, Any]:
    """Сводка прогноза по активным лидам воронки."""
    sts = stages or list(STAGE_CLOSE_BASE_PCT.keys())
    active: list[dict[str, Any]] = []
    for lead in leads:
        stage = normalize_stage(lead.get("stage"), sts)
        if stage in (WON_STAGE, LOST_STAGE):
            continue
        active.append(forecast_lead_close(lead, sts))

    if not active:
        return {
            "activeLeads": 0,
            "avgProbabilityPct": 0.0,
            "expectedPipelineRub": 0,
            "tiers": {TIER_HIGH: 0, TIER_MEDIUM: 0, TIER_LOW: 0},
            "topOpportunities": [],
            "method": "economist_heuristic",
        }

    tiers = {TIER_HIGH: 0, TIER_MEDIUM: 0, TIER_LOW: 0}
    prob_sum = 0.0
    expected_total = 0
    for row in active:
        tiers[row["tier"]] = tiers.get(row["tier"], 0) + 1
        prob_sum += float(row["closeProbabilityPct"])
        if row.get("expectedRub"):
            expected_total += int(row["expectedRub"])

    ranked = sorted(
        active,
        key=lambda r: (r.get("expectedRub") or 0, r["closeProbabilityPct"]),
        reverse=True,
    )

    return {
        "activeLeads": len(active),
        "avgProbabilityPct": round(prob_sum / len(active), 1),
        "expectedPipelineRub": expected_total,
        "tiers": tiers,
        "topOpportunities": ranked[: max(top_limit, 1)],
        "method": "economist_heuristic",
    }
