"""Цепочка квалификации и документов по лиду (порядок шагов для UI и подсказок)."""
from __future__ import annotations

from typing import Any

from core.lead_approvals import APPROVAL_LABELS_RU
from core.lead_contacts import contacts_for_api, has_established_lpr

DEFAULT_STAGE_DAY_LIMITS: dict[str, int] = {
    "Новый": 3,
    "Квалифицирован": 8,
    "Переговоры": 5,
}

# Поля квалификации до «Квалифицирован»
QUALIFICATION_FIELD_STEPS: tuple[dict[str, str], ...] = (
    {"key": "company", "label": "Компания"},
    {"key": "contact", "label": "Контакт"},
    {"key": "phone_or_email", "label": "Телефон или email"},
)

PRE_KP_APPROVAL_KEYS: tuple[str, ...] = (
    "assortmentAgreed",
    "priceAgreed",
    "termsAgreed",
    "paymentTermsAgreed",
    "securityPassed",
    "rebateAgreed",
    "kpSent",
)

WON_APPROVAL_KEYS: tuple[str, ...] = (
    "invoiceIssued",
    "contractSent",
    "contractSigned",
    "contractSignedDoc",
    "presentationSent",
    "licenseShipped",
)

DEAL_PATH_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "id": "qualification",
        "title": "Квалификация",
        "subtitle": "До этапа «Квалифицирован», макс. 3 дня в «Новый»",
        "relatedStages": ("Новый", "Квалифицирован"),
    },
    {
        "id": "pre_kp",
        "title": "Документы до КП",
        "subtitle": "От ассортимента до скидки и отправки КП, макс. 8 дней в «Квалифицирован»",
        "relatedStages": ("Квалифицирован", "КП отправлено"),
    },
    {
        "id": "won",
        "title": "Закрытие сделки",
        "subtitle": "После «Выигран» — счёт, договор, презентация, отгрузка",
        "relatedStages": ("Выигран",),
    },
)


def _field_done(lead: dict[str, Any], key: str) -> bool:
    if key == "phone_or_email":
        phone = str(lead.get("phone") or "").strip()
        email = str(lead.get("email") or "").strip()
        return bool(phone and phone != "—") or bool(email and email != "—")
    val = str(lead.get(key) or "").strip()
    return bool(val) and val != "—"


def _approval_done(approvals: dict[str, bool], key: str) -> bool:
    return bool(approvals.get(key))


def _lpr_established(lead: dict[str, Any], approvals: dict[str, bool]) -> bool:
    if has_established_lpr(contacts_for_api(lead)):
        return True
    return _approval_done(approvals, "lprEstablished")


def _step_row(*, key: str, label: str, kind: str, done: bool) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": kind, "done": done}


def build_deal_path(lead: dict[str, Any]) -> dict[str, Any]:
    approvals = lead.get("approvals") if isinstance(lead.get("approvals"), dict) else {}
    groups: list[dict[str, Any]] = []

    qual_steps = [
        _step_row(key=s["key"], label=s["label"], kind="field", done=_field_done(lead, s["key"]))
        for s in QUALIFICATION_FIELD_STEPS
    ]
    qual_steps.append(
        _step_row(
            key="lprEstablished",
            label=APPROVAL_LABELS_RU["lprEstablished"],
            kind="derived",
            done=_lpr_established(lead, approvals),
        )
    )
    groups.append(_pack_group("qualification", qual_steps))

    pre_kp_steps = [
        _step_row(
            key=k,
            label=APPROVAL_LABELS_RU.get(k, k),
            kind="approval",
            done=_approval_done(approvals, k),
        )
        for k in PRE_KP_APPROVAL_KEYS
    ]
    groups.append(_pack_group("pre_kp", pre_kp_steps))

    won_steps = [
        _step_row(
            key=k,
            label=APPROVAL_LABELS_RU.get(k, k),
            kind="approval",
            done=_approval_done(approvals, k),
        )
        for k in WON_APPROVAL_KEYS
    ]
    groups.append(_pack_group("won", won_steps))

    nxt = _first_incomplete(groups)
    return {"groups": groups, "stageDayLimits": dict(DEFAULT_STAGE_DAY_LIMITS), "nextStep": nxt}


def _pack_group(group_id: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    meta = next(g for g in DEAL_PATH_GROUPS if g["id"] == group_id)
    done_n = sum(1 for s in steps if s["done"])
    return {
        "id": group_id,
        "title": meta["title"],
        "subtitle": meta["subtitle"],
        "relatedStages": list(meta["relatedStages"]),
        "steps": steps,
        "progress": {"done": done_n, "total": len(steps)},
    }


def _first_incomplete(groups: list[dict[str, Any]]) -> dict[str, Any] | None:
    for group in groups:
        for step in group["steps"]:
            if not step["done"]:
                return {**step, "groupId": group["id"], "groupTitle": group["title"]}
    return None


def next_incomplete_step(lead: dict[str, Any]) -> dict[str, Any] | None:
    path = build_deal_path(lead)
    return path.get("nextStep")
