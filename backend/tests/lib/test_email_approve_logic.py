"""Зеркало frontend/src/lib/email/emailApproveLogic.js."""

from __future__ import annotations


def reply_recipient_from_messages(messages: list[dict]) -> str:
    inbound = [m for m in messages if m.get("direction") == "inbound"]
    if not inbound:
        return ""
    return str(inbound[-1].get("sender") or "").strip()


def build_reply_approve_preview(*, thread: dict, messages: list[dict], body: str) -> dict:
    return {
        "title": "Отправить ответ?",
        "kind": "reply",
        "to": reply_recipient_from_messages(messages),
        "subject": str(thread.get("subject") or "").strip(),
        "body": str(body or "").strip(),
    }


def build_compose_approve_preview(*, to: str, subject: str, body: str) -> dict:
    return {
        "title": "Отправить письмо?",
        "kind": "compose",
        "to": str(to or "").strip(),
        "subject": str(subject or "").strip(),
        "body": str(body or "").strip(),
    }


def test_reply_recipient_from_inbound():
    msgs = [
        {"direction": "inbound", "sender": "a@test.com"},
        {"direction": "outbound", "sender": "me@test.com"},
        {"direction": "inbound", "sender": "client@example.com"},
    ]
    assert reply_recipient_from_messages(msgs) == "client@example.com"


def test_build_reply_preview():
    prev = build_reply_approve_preview(
        thread={"subject": "Прайс"},
        messages=[{"direction": "inbound", "sender": "c@x.com"}],
        body="Текст ответа",
    )
    assert prev["kind"] == "reply"
    assert prev["to"] == "c@x.com"
    assert prev["subject"] == "Прайс"
    assert prev["body"] == "Текст ответа"


def test_build_compose_preview():
    prev = build_compose_approve_preview(to="x@y.com", subject="Hi", body="Hello")
    assert prev["kind"] == "compose"
    assert prev["to"] == "x@y.com"
