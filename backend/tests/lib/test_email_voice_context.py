"""Зеркало frontend/src/lib/email/emailVoiceContext.js + voice/email_context.py."""

from __future__ import annotations

from voice.email_context import email_folder_from_filter, email_navigate_payload


def test_folder_from_filter():
    assert email_folder_from_filter("sent") == "sent"
    assert email_folder_from_filter("unread") == "inbox"
    assert email_folder_from_filter(None) == "inbox"


def test_navigate_payload_unread_hint():
    payload = email_navigate_payload({"filter": "unread"})
    assert payload["folder"] == "inbox"
    assert "Непрочитанные" in payload["hint"]


def test_navigate_payload_sent():
    payload = email_navigate_payload({"filter": "sent"})
    assert payload["folder"] == "sent"
    assert payload["hint"] == ""
