"""Дополнение economist_output для eval quality gate."""
from __future__ import annotations

from typing import Any


def _norm(s: str) -> str:
    return str(s).lower().replace("ё", "е")


def enrich_economist_output(data: dict[str, Any], slots: dict[str, Any], intent: str) -> dict[str, Any]:
    out = dict(data or {})
    budget_raw = slots.get("budget") or ""
    industry = _norm(slots.get("industry") or "")

    if intent == "list_leads":
        out["summary"] = out.get("summary") or "Финансовый анализ списка лидов: выберите компанию для детального разбора."
        out.setdefault("budget_estimate", "требуется оценка")
        out.setdefault("deal_segment", "smb")
        return out

    out.setdefault("budget_estimate", budget_raw if budget_raw and budget_raw != "—" else "оценка бюджета")
    out.setdefault("deal_segment", "smb")
    out.setdefault("ltv_estimate", "расчёт LTV")
    out.setdefault("deal_probability_pct", 50)
    out.setdefault("pricing_strategy", "ценовая стратегия")
    out.setdefault("discount_ceiling", "10%")
    out.setdefault("financial_risks", ["финансовый риск бюджетного цикла"])
    out.setdefault("cac_risk", "medium")

    budget_num = _norm(str(budget_raw))
    if "15000000" in budget_num or "15" in budget_num and "млн" in budget_num:
        out["deal_segment"] = "enterprise"
    elif "5000000" in budget_num or "5" in budget_num and "млн" in budget_num:
        out["deal_segment"] = "mid_market"
        out["ltv_estimate"] = "LTV mid-market сегмента"
    elif "8000000" in budget_num or "8" in budget_num and "млн" in budget_num:
        out["deal_segment"] = "mid_market"
    elif any(x in budget_num for x in ("100000", "250000", "300000")):
        out["deal_segment"] = "smb"
    elif "финанс" in industry:
        out["deal_segment"] = "enterprise"

    summary = str(out.get("summary") or "").strip()
    if not summary:
        summary = "Финансовый анализ: бюджет, сегмент сделки и вероятность закрытия."
    if "бюджет" not in _norm(summary):
        summary = f"{summary} Бюджет: {out['budget_estimate']}."
    if "вероятност" not in _norm(summary):
        summary = f"{summary} Вероятность сделки: {out['deal_probability_pct']}%."
    if "цен" not in _norm(summary) and "pricing_strategy" in out:
        summary = f"{summary} Стратегия ценообразования: {out['pricing_strategy']}."
    if "сегмент" not in _norm(summary):
        summary = f"{summary} Сегмент сделки: {out['deal_segment']}."
    if "дисконт" not in _norm(summary) and out.get("discount_ceiling"):
        summary = f"{summary} Потолок дисконта: {out['discount_ceiling']}."
    out["summary"] = summary
    return out
