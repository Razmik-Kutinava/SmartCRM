"""Подсказки по этапу, срокам и документам (не меняют score в БД)."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from core.lead_deal_path import (
    DEFAULT_STAGE_DAY_LIMITS,
    PRE_KP_APPROVAL_KEYS,
    QUALIFICATION_FIELD_STEPS,
    WON_APPROVAL_KEYS,
)
from core.lead_approvals import APPROVAL_LABELS_RU
from core.lead_contacts import contacts_for_api, has_established_lpr
from core.lead_day_priority import days_without_touch
from core.lead_task_intents import WAIT_STALE_INTENTS, classify_task_intent


def _hint(severity: str, code: str, message: str, **extra: Any) -> dict[str, Any]:
    row = {"severity": severity, "code": code, "message": message}
    row.update(extra)
    return row


def _parse_iso(s: Any) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def days_on_stage(stage_entered_at: Optional[dt.datetime], today: dt.date) -> int:
    if not stage_entered_at:
        return 0
    d = stage_entered_at.date() if hasattr(stage_entered_at, "date") else stage_entered_at
    return max(0, (today - d).days)


def _field_done(lead: dict[str, Any], key: str) -> bool:
    if key == "phone_or_email":
        phone = str(lead.get("phone") or "").strip()
        email = str(lead.get("email") or "").strip()
        return bool(phone and phone != "—") or bool(email and email != "—")
    val = str(lead.get(key) or "").strip()
    return bool(val) and val != "—"


def _merge_limits(settings: dict[str, Any]) -> dict[str, int]:
    raw = settings.get("stage_nudge_limits")
    if not isinstance(raw, dict):
        return dict(DEFAULT_STAGE_DAY_LIMITS)
    out = dict(DEFAULT_STAGE_DAY_LIMITS)
    for k, v in raw.items():
        try:
            out[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    return out


def compute_stage_hints(
    lead: dict[str, Any],
    *,
    stage_entered_at: Optional[dt.datetime],
    last_comm_at: Optional[dt.datetime],
    settings: dict[str, Any],
    score_advisory: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    today = dt.date.today()
    now = dt.datetime.now(dt.timezone.utc)
    stage = str(lead.get("stage") or "Новый").strip()
    limits = _merge_limits(settings)
    limit = limits.get(stage)
    on_stage = days_on_stage(stage_entered_at, today)

    if limit is not None and on_stage >= limit:
        hints.append(
            _hint(
                "critical",
                "stage_stale",
                f"Лид уже {on_stage} дн. на этапе «{stage}» — пора двигать дальше или закрывать.",
                daysOnStage=on_stage,
                stageLimit=limit,
            )
        )
    elif limit is not None and on_stage >= max(1, limit - 1):
        hints.append(
            _hint(
                "warn",
                "stage_stale_soon",
                f"Скоро дедлайн: {on_stage} из {limit} дн. на «{stage}». Закрой шаги и переведи этап.",
                daysOnStage=on_stage,
                stageLimit=limit,
            )
        )

    approvals = lead.get("approvals") if isinstance(lead.get("approvals"), dict) else {}

    if stage == "Новый":
        if not _field_done(lead, "contact") or not _field_done(lead, "company"):
            hints.append(_hint("warn", "qual_fields", "Заполни компанию и контакт — без этого не квалифицируем."))
        if not has_established_lpr(contacts_for_api(lead)):
            hints.append(_hint("warn", "lpr_missing", "Добавь контакт с ролью ЛПР справа — имя, должность и телефон или email."))

    if stage == "Квалифицирован":
        for key in PRE_KP_APPROVAL_KEYS:
            if not approvals.get(key):
                label = APPROVAL_LABELS_RU.get(key, key)
                hints.append(
                    _hint("warn", f"approval_missing_{key}", f"До КП: отметь «{label}» в пути сделки.")
                )
                break

    if stage in ("КП отправлено", "Переговоры"):
        if not approvals.get("kpSent"):
            hints.append(_hint("critical", "kp_not_marked", "КП не отмечено как отправленное — отметь в пути сделки."))
        comm_day = last_comm_at.date() if last_comm_at else None
        if comm_day != today:
            hints.append(
                _hint(
                    "warn",
                    "kp_daily_touch",
                    "Сегодня не было касания по КП — позвони или напиши, ждём ответ клиента.",
                )
            )

    if stage == "Выигран":
        for key in WON_APPROVAL_KEYS:
            if not approvals.get(key):
                label = APPROVAL_LABELS_RU.get(key, key)
                hints.append(
                    _hint("warn", f"won_doc_{key}", f"Выигран, но не закрыто: «{label}».")
                )

    title = str(lead.get("nextTaskTitle") or "").strip()
    if title and last_comm_at is not None:
        intent_id, _ = classify_task_intent(title)
        no_touch = days_without_touch(last_comm_at, today)
        if intent_id in WAIT_STALE_INTENTS or stage in ("КП отправлено", "Переговоры"):
            if no_touch >= 21:
                hints.append(
                    _hint(
                        "warn",
                        "wait_stale",
                        f"Нет касания {no_touch} дн. по делу «{title[:60]}» — перенеси срок, закрой или отметь проигран.",
                        daysWithoutTouch=no_touch,
                    )
                )
            elif no_touch >= 14:
                hints.append(
                    _hint(
                        "info",
                        "repeat_wait_task",
                        f"Долгое ожидание ({no_touch} дн.) — проверь, актуален ли лид.",
                        daysWithoutTouch=no_touch,
                    )
                )

    if score_advisory:
        for w in score_advisory.get("warnings") or []:
            if not w:
                continue
            sev = "warn" if "отличается" in str(w) else "info"
            hints.append(_hint(sev, "score_advisory", str(w)))

    # дедуп по code, сохраняем порядок (critical first)
    order = {"critical": 0, "warn": 1, "info": 2}
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for h in sorted(hints, key=lambda x: order.get(x["severity"], 9)):
        if h["code"] in seen:
            continue
        seen.add(h["code"])
        unique.append(h)
    return unique[:8]
