"""Маппинг голосовых слотов email → UI /email."""

from __future__ import annotations

_FOLDER_BY_FILTER: dict[str, str] = {
    "inbox": "inbox",
    "unread": "inbox",
    "all": "inbox",
    "sent": "sent",
    "outbound": "sent",
    "archive": "archive",
    "campaign": "campaign",
    "zoho": "zoho",
}


def email_folder_from_filter(filter_value: str | None) -> str:
    key = str(filter_value or "inbox").strip().lower()
    return _FOLDER_BY_FILTER.get(key, "inbox")


def email_navigate_payload(slots: dict | None) -> dict:
    """Payload для voice_action navigate list_emails."""
    slots = dict(slots or {})
    filt = slots.get("filter") or "inbox"
    folder = email_folder_from_filter(str(filt))
    hint = ""
    if str(filt).lower() == "unread":
        hint = "Непрочитанные пока не отмечены в UI — показаны входящие."
    return {
        "folder": folder,
        "filter": filt,
        "hint": hint,
        "search": str(slots.get("query") or slots.get("search") or "").strip(),
    }
