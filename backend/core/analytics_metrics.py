"""Метрики воронки и KPI из списка лидов (зеркало frontend analyticsMetrics.js)."""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Any

WON_STAGE = "Выигран"
LOST_STAGE = "Проигран"

DEFAULT_STAGES = [
    "Новый",
    "Квалифицирован",
    "КП отправлено",
    "Переговоры",
    "Выигран",
    "Проигран",
]


def parse_budget_rub(raw: str | None) -> float | None:
    if not raw:
        return None
    s = re.sub(r"[^\d.,]", "", str(raw).replace(" ", ""))
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def lead_amount_rub(lead: dict[str, Any]) -> float | None:
    ar = lead.get("amountRub")
    if ar is not None and ar != "":
        try:
            v = float(ar)
            return v if v > 0 else None
        except (TypeError, ValueError):
            pass
    return parse_budget_rub(lead.get("budget"))


def parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_created_date(lead: dict[str, Any]) -> datetime | None:
    if lead.get("createdAt"):
        return parse_iso_date(str(lead["createdAt"]))
    created = lead.get("created")
    if created and created != "—":
        try:
            return datetime.strptime(str(created), "%d.%m.%Y")
        except ValueError:
            pass
    return None


def normalize_stage(stage: str | None, stages: list[str]) -> str:
    s = (stage or "Новый").strip()
    return s if s in stages else "Новый"


def compute_analytics(leads: list[dict[str, Any]], stages: list[str] | None = None) -> dict[str, Any]:
    sts = stages or DEFAULT_STAGES
    by_stage = {s: 0 for s in sts}
    total = len(leads)
    won = 0
    lost = 0
    deal_amounts: list[float] = []
    cycle_days: list[int] = []

    for lead in leads:
        st = normalize_stage(lead.get("stage"), sts)
        by_stage[st] = by_stage.get(st, 0) + 1
        if st == WON_STAGE:
            won += 1
            amt = lead_amount_rub(lead)
            if amt is not None:
                deal_amounts.append(amt)
            created = parse_created_date(lead)
            updated = parse_iso_date(lead.get("updatedAt"))
            if created and updated:
                delta = (updated - created).days
                if delta >= 0:
                    cycle_days.append(delta)
        elif st == LOST_STAGE:
            lost += 1

    funnel = []
    for stage in sts:
        count = by_stage.get(stage, 0)
        pct = round(100 * count / total, 1) if total else 0.0
        funnel.append({"stage": stage, "count": count, "pct": pct})

    conversion_pct = round(100 * won / total, 1) if total else 0.0
    win_rate_pct = round(100 * won / (won + lost), 1) if (won + lost) else None
    avg_deal_rub = round(sum(deal_amounts) / len(deal_amounts)) if deal_amounts else None
    avg_cycle_days = round(sum(cycle_days) / len(cycle_days)) if cycle_days else None
    avg_score = round(sum(float(l.get("score") or 0) for l in leads) / total) if total else 0

    return {
        "total": total,
        "wonCount": won,
        "lostCount": lost,
        "avgScore": avg_score,
        "byStage": by_stage,
        "funnel": funnel,
        "conversionPct": conversion_pct,
        "winRatePct": win_rate_pct,
        "avgDealRub": avg_deal_rub,
        "avgCycleDays": avg_cycle_days,
    }


def analytics_to_csv(metrics: dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["metric", "value"])
    w.writerow(["total", metrics["total"]])
    w.writerow(["conversionPct", metrics["conversionPct"]])
    if metrics.get("winRatePct") is not None:
        w.writerow(["winRatePct", metrics["winRatePct"]])
    w.writerow(["avgDealRub", metrics.get("avgDealRub") or ""])
    w.writerow(["avgCycleDays", metrics.get("avgCycleDays") or ""])
    w.writerow(["avgScore", metrics.get("avgScore", 0)])
    w.writerow([])
    w.writerow(["stage", "count", "pct"])
    for row in metrics["funnel"]:
        w.writerow([row["stage"], row["count"], row["pct"]])
    return buf.getvalue()
