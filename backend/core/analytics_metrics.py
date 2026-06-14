"""Метрики воронки и KPI из списка лидов (зеркало frontend analyticsMetrics.js)."""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timedelta, timezone
from typing import Any

PERIOD_DAYS: dict[str, int] = {
    "week": 7,
    "month": 30,
    "quarter": 90,
    "year": 365,
}

PERIOD_LABELS: dict[str, str] = {
    "week": "неделя",
    "month": "месяц",
    "quarter": "квартал",
    "year": "год",
    "last_year": "прошлый год",
}

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


def period_days(period: str) -> int:
    return PERIOD_DAYS.get(period, 7)


def period_label(period: str) -> str:
    return PERIOD_LABELS.get(period, period)


def lead_source(lead: dict[str, Any]) -> str:
    return str(lead.get("source") or "—").strip() or "—"


def filter_leads_by_period(
    leads: list[dict[str, Any]],
    period: str | None,
) -> list[dict[str, Any]]:
    if not period:
        return leads
    now = datetime.now(timezone.utc)
    if period == "last_year":
        start = datetime(now.year - 1, 1, 1, tzinfo=timezone.utc)
        end = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    else:
        cutoff = now - timedelta(days=period_days(period))
        start, end = cutoff, None
    out: list[dict[str, Any]] = []
    for lead in leads:
        created = parse_created_date(lead)
        if created is None:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if period == "last_year":
            if start <= created < end:
                out.append(lead)
        elif created >= start:
            out.append(lead)
    return out


def filter_leads_by_source(
    leads: list[dict[str, Any]],
    source: str | None,
) -> list[dict[str, Any]]:
    if not source:
        return leads
    needle = str(source).strip().lower()
    return [lead for lead in leads if needle in lead_source(lead).lower()]


def apply_analytics_filters(
    leads: list[dict[str, Any]],
    *,
    period: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    return filter_leads_by_source(filter_leads_by_period(leads, period), source)


def compute_conversion_by_source(
    leads: list[dict[str, Any]],
    stages: list[str] | None = None,
) -> list[dict[str, Any]]:
    sts = stages or DEFAULT_STAGES
    buckets: dict[str, dict[str, Any]] = {}
    for lead in leads:
        src = lead_source(lead)
        row = buckets.setdefault(src, {"source": src, "total": 0, "won": 0})
        row["total"] += 1
        if normalize_stage(lead.get("stage"), sts) == WON_STAGE:
            row["won"] += 1
    out: list[dict[str, Any]] = []
    for row in sorted(buckets.values(), key=lambda item: -int(item["total"])):
        total = int(row["total"])
        won = int(row["won"])
        row["conversionPct"] = round(100 * won / total, 1) if total else 0.0
        out.append(row)
    return out


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


def compute_analytics_report(
    leads: list[dict[str, Any]],
    stages: list[str] | None = None,
    *,
    period: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    sts = stages or DEFAULT_STAGES
    filtered = apply_analytics_filters(leads, period=period, source=source)
    metrics = compute_analytics(filtered, sts)
    metrics["conversionBySource"] = compute_conversion_by_source(filtered, sts)
    metrics["filters"] = {
        "period": period or "",
        "periodLabel": period_label(period) if period else "",
        "source": source or "",
    }
    return metrics


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
    by_src = metrics.get("conversionBySource") or []
    if by_src:
        w.writerow([])
        w.writerow(["source", "total", "won", "conversionPct"])
        for row in by_src:
            w.writerow([row["source"], row["total"], row["won"], row["conversionPct"]])
    return buf.getvalue()
