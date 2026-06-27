"""Ранжирование «Мой день»: этап+roadmap, тип дела, время, затухание ожидания."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Optional

from core.day_priority_config import DEFAULT_DAY_PRIORITY, merge_day_priority
from core.lead_deal_path import build_deal_path
from core.lead_task_intents import WAIT_STALE_INTENTS, classify_task_intent, intent_weight
from core.lead_task_list_flags import lead_task_flags
from core.task_dates import parse_task_datetime

HOT_STAGES = frozenset({"КП отправлено", "Переговоры", "Выигран"})


def _deal_path_progress_boost(lead: dict[str, Any], cap: int) -> int:
    path = build_deal_path(lead)
    total = done = 0
    for group in path.get("groups") or []:
        prog = group.get("progress") or {}
        total += int(prog.get("total") or 0)
        done += int(prog.get("done") or 0)
    if total <= 0:
        return 0
    return int(cap * done / total)


def _time_addon(due_raw: str, urgency: str, today: dt.date) -> float:
    parsed = parse_task_datetime(due_raw)
    if urgency == "overdue" and parsed:
        days = max(0, (today - parsed.date()).days)
        return min(days * 50, 500) + (parsed.hour * 60 + parsed.minute) / 1440.0
    if urgency == "today" and parsed:
        if parsed.hour or parsed.minute:
            return (parsed.hour * 60 + parsed.minute) / 1440.0 * 500
        return 400.0
    if urgency == "tomorrow":
        return 100.0
    if urgency == "upcoming" and parsed:
        return min(900.0, (parsed.date() - today).days * 30.0)
    return 200.0 if urgency == "open" else 0.0


def _score_boost(lead: dict[str, Any], dp: dict[str, Any]) -> int:
    sug_factor = float(dp.get("score_suggested_factor") or 0.6)
    mgr_factor = float(dp.get("score_manager_factor") or 0.4)
    sug = lead.get("suggestedScore")
    if sug is not None:
        try:
            return int(float(sug) * sug_factor)
        except (TypeError, ValueError):
            pass
    try:
        return int(float(lead.get("score") or 0) * mgr_factor)
    except (TypeError, ValueError):
        return 0


def _amount_for_tie(lead: dict[str, Any]) -> float:
    for key in ("deal_amount", "amount", "amountRub"):
        val = lead.get(key)
        if val is None:
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return 0.0


def days_without_touch(last_comm_at: Optional[dt.datetime], today: dt.date) -> int:
    if not last_comm_at:
        return 0
    d = last_comm_at.date() if hasattr(last_comm_at, "date") else last_comm_at
    return max(0, (today - d).days)


def wait_stale_penalty(
    *,
    intent_id: str,
    stage: str,
    days_no_touch: int,
    on_stage_days: int = 0,
    dp: dict[str, Any] | None = None,
) -> tuple[int, bool]:
    cfg = dp or DEFAULT_DAY_PRIORITY
    start = int(cfg.get("stale_start_days") or 14)
    per_day = int(cfg.get("stale_penalty_per_day") or 120)
    cap = int(cfg.get("stale_penalty_cap") or 8000)
    wait_days = int(cfg.get("wait_stale_days") or 21)
    if intent_id not in WAIT_STALE_INTENTS and stage not in HOT_STAGES:
        return 0, False
    if days_no_touch < start:
        return 0, False
    penalty = min(cap, (days_no_touch - start + 1) * per_day)
    if on_stage_days > 30:
        penalty += min(2000, (on_stage_days - 30) * 40)
    stale = days_no_touch >= wait_days
    return penalty, stale


def compute_needs_enrich(lead: dict[str, Any], intent_tier: str, stage: str) -> bool:
    if lead.get("coverageCardReady"):
        return False
    if intent_tier in ("A", "B"):
        return True
    return stage in HOT_STAGES


def compute_day_priority(
    lead: dict[str, Any],
    tasks: list[dict[str, Any]],
    *,
    today: Optional[dt.date] = None,
    last_comm_at: Optional[dt.datetime] = None,
    on_stage_days: int = 0,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dp = merge_day_priority(settings)
    stage_boost = dp.get("stage_boost") or {}
    urgency_base = dp.get("urgency_base") or {}
    tier_weight = dp.get("tier_weight") or {}
    ref = today or dt.date.today()
    flags = lead_task_flags(tasks, today=ref)
    stage = str(lead.get("stage") or "Новый").strip()
    title = str(flags.get("nextTaskTitle") or "")
    due_raw = str(flags.get("nextTaskDue") or "")
    note = ""
    task_intent_field = ""
    open_rows = [t for t in tasks if str(t.get("status") or "open") != "done"]
    for t in open_rows:
        if str(t.get("title") or "").strip() == title:
            task_intent_field = str(t.get("taskIntent") or "").strip()
            raw_note = str(t.get("note") or "")
            note = f"intent:{task_intent_field}" if task_intent_field else raw_note
            break

    intent_id, intent_tier = classify_task_intent(title, note)
    urgency = str(flags.get("taskUrgency") or "none")
    if flags.get("taskDueTomorrow") and urgency not in ("overdue", "today"):
        urgency = "tomorrow"

    rank = float(urgency_base.get(urgency, urgency_base.get("none", 50_000)))
    rank += _time_addon(due_raw, urgency, ref)

    money_boost = int(stage_boost.get(stage, 30)) + _deal_path_progress_boost(
        lead, int(dp.get("deal_path_progress_cap") or 50)
    )
    task_boost = intent_weight(
        intent_id,
        intent_tier,
        stage,
        tier_weight=tier_weight,
        hot_bonus=int(dp.get("hot_stage_intent_bonus") or 40),
    )
    score_boost = _score_boost(lead, dp)

    rank -= money_boost
    rank -= task_boost
    rank -= score_boost

    no_touch = days_without_touch(last_comm_at, ref)
    stale_pen, wait_stale = wait_stale_penalty(
        intent_id=intent_id,
        stage=stage,
        days_no_touch=no_touch,
        on_stage_days=on_stage_days,
        dp=dp,
    )
    rank += stale_pen

    needs = compute_needs_enrich(lead, intent_tier, stage)

    return {
        "dayRank": round(rank, 4),
        "taskIntent": intent_id,
        "taskIntentTier": intent_tier,
        "moneyBoost": money_boost,
        "taskIntentBoost": task_boost,
        "needsEnrich": needs,
        "waitStale": wait_stale,
        "daysWithoutTouch": no_touch if no_touch > 0 else None,
    }


def sort_key_for_lead(lead: dict[str, Any]) -> tuple:
    """Ключ сортировки: dayRank ↑, amount ↓, company ↑."""
    rank = lead.get("dayRank")
    try:
        r = float(rank) if rank is not None else 1e9
    except (TypeError, ValueError):
        r = 1e9
    amt = -_amount_for_tie(lead)
    company = str(lead.get("company") or "")
    return (r, amt, company)
