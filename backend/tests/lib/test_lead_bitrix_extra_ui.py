"""Зеркало frontend/src/lib/leads/leadBitrixExtra.js."""
from __future__ import annotations

LICENSE_DISPLAY_FIELDS = [
    {"key": "subscriptionEnd", "label": "Подписка до"},
    {"key": "deliveryType", "label": "Тип поставки"},
    {"key": "licenseTerm", "label": "Срок лицензии"},
    {"key": "reservedUntil", "label": "Резерв до"},
    {"key": "licenseRegistration", "label": "Licensing email"},
    {"key": "sublicensee", "label": "Сублицензиат"},
    {"key": "payerPartner", "label": "Плательщик / партнёр"},
    {"key": "manager", "label": "Менеджер"},
    {"key": "participant", "label": "Участник"},
]


def _display_value(val) -> str:
    if val is None or val == "" or val is False:
        return ""
    if isinstance(val, bool):
        return "Да" if val else ""
    return str(val).strip()


def bitrix_extra_from_lead(lead: dict | None) -> dict:
    if not lead:
        return {}
    extra = lead.get("bitrixExtra")
    return extra if isinstance(extra, dict) else {}


def license_display_rows(lead: dict | None) -> list[dict]:
    extra = bitrix_extra_from_lead(lead)
    rows = []
    for item in LICENSE_DISPLAY_FIELDS:
        value = _display_value(extra.get(item["key"]))
        if value:
            rows.append({"key": item["key"], "label": item["label"], "value": value})
    return rows


def is_repeat_lead(lead: dict | None) -> bool:
    return bool(bitrix_extra_from_lead(lead).get("isRepeatLead"))


def _format_uf_value(raw) -> str:
    if raw is None:
        return ""
    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, dict) and "VALUE" in item:
                parts.append(str(item.get("VALUE") or ""))
            else:
                parts.append(str(item or ""))
        return ", ".join(p for p in parts if p)
    if isinstance(raw, dict):
        v = raw.get("VALUE", raw.get("value"))
        return str(v) if v is not None else str(raw)
    return str(raw)


def raw_bitrix_uf_entries(lead: dict | None) -> list[dict]:
    if not lead:
        return []
    tech = lead.get("tech") or {}
    b24 = tech.get("bitrix24") or {}
    uf = b24.get("uf")
    if not isinstance(uf, dict):
        return []
    return [
        {"key": key, "value": _format_uf_value(val)}
        for key, val in sorted(uf.items(), key=lambda kv: kv[0])
        if _format_uf_value(val)
    ]


def license_preview_text(lead: dict | None) -> str:
    rows = license_display_rows(lead)
    if not rows:
        return ""
    first = rows[0]
    if len(rows) > 1:
        return f"{first['label']}: {first['value']} (+{len(rows) - 1})"
    return f"{first['label']}: {first['value']}"


def test_license_display_rows_x5_like():
    lead = {
        "bitrixExtra": {
            "subscriptionEnd": "2026-12-31",
            "deliveryType": "Подписка",
            "licenseTerm": "12 мес.",
            "isRepeatLead": True,
        }
    }
    rows = license_display_rows(lead)
    keys = [r["key"] for r in rows]
    assert "subscriptionEnd" in keys
    assert "deliveryType" in keys
    assert "licenseTerm" in keys
    assert "isRepeatLead" not in keys


def test_is_repeat_lead():
    assert is_repeat_lead({"bitrixExtra": {"isRepeatLead": True}})
    assert not is_repeat_lead({"bitrixExtra": {"isRepeatLead": False}})
    assert not is_repeat_lead({})


def test_raw_bitrix_uf_entries():
    lead = {
        "tech": {
            "bitrix24": {
                "uf": {
                    "UF_CRM_123": "foo",
                    "UF_CRM_456": [{"VALUE": "bar"}, {"VALUE": "baz"}],
                }
            }
        }
    }
    entries = raw_bitrix_uf_entries(lead)
    assert len(entries) == 2
    assert entries[0]["key"] == "UF_CRM_123"
    assert entries[1]["value"] == "bar, baz"


def test_license_preview_text():
    lead = {
        "bitrixExtra": {
            "subscriptionEnd": "2026-12-31",
            "deliveryType": "Подписка",
        }
    }
    assert license_preview_text(lead) == "Подписка до: 2026-12-31 (+1)"
