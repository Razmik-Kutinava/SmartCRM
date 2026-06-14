"""Зеркало frontend/src/lib/email/emailListLogic.js."""

from __future__ import annotations

HIDDEN_IN_INBOX = frozenset({"outbound", "campaign", "archive"})


def filter_email_threads(threads, *, folder="inbox", search="", account_id=None):
    list_ = list(threads)
    if account_id is not None and account_id != "":
        list_ = [t for t in list_ if t.get("accountId") == account_id]
    if folder == "inbox":
        list_ = [t for t in list_ if t.get("category") not in HIDDEN_IN_INBOX and not t.get("isArchived")]
    elif folder == "sent":
        list_ = [t for t in list_ if t.get("category") == "outbound"]
    elif folder == "zoho":
        list_ = [t for t in list_ if "zoho" in f"{t.get('subject', '')} {t.get('snippet', '')}".lower()]
    elif folder == "campaign":
        list_ = [t for t in list_ if t.get("category") == "campaign"]
    elif folder == "archive":
        list_ = [t for t in list_ if t.get("isArchived")]
    q = (search or "").strip().lower()
    if q:
        list_ = [
            t
            for t in list_
            if q in str(t.get("subject") or "").lower()
            or q in str(t.get("snippet") or "").lower()
            or q in str(t.get("previewFrom") or "").lower()
        ]
    return list_


def count_email_folder(threads, folder):
    return len(filter_email_threads(threads, folder=folder, search=""))


def test_inbox_hides_outbound_and_archived():
    threads = [
        {"id": 1, "category": "inbound", "isArchived": False, "subject": "A"},
        {"id": 2, "category": "outbound", "isArchived": False, "subject": "B"},
        {"id": 3, "category": "general", "isArchived": True, "subject": "C"},
    ]
    out = filter_email_threads(threads, folder="inbox")
    assert [t["id"] for t in out] == [1]


def test_search_by_preview_from():
    threads = [
        {"id": 1, "category": "inbound", "previewFrom": "client@example.com", "subject": "Hi"},
    ]
    out = filter_email_threads(threads, folder="inbox", search="example")
    assert len(out) == 1


def test_account_filter():
    threads = [
        {"id": 1, "accountId": 1, "category": "inbound", "isArchived": False},
        {"id": 2, "accountId": 2, "category": "inbound", "isArchived": False},
    ]
    out = filter_email_threads(threads, folder="inbox", account_id=2)
    assert [t["id"] for t in out] == [2]


def test_folder_counts():
    threads = [
        {"id": 1, "category": "outbound", "isArchived": False},
        {"id": 2, "category": "inbound", "isArchived": False},
        {"id": 3, "category": "inbound", "isArchived": True},
    ]
    assert count_email_folder(threads, "sent") == 1
    assert count_email_folder(threads, "archive") == 1
