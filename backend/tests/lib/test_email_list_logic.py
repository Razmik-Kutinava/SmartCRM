"""Зеркало frontend/src/lib/email/emailListLogic.js."""

from __future__ import annotations

HIDDEN_IN_INBOX = frozenset({"outbound", "campaign", "archive"})


def thread_has_attachments(thread: dict) -> bool:
    if thread.get("hasAttachments") is True:
        return True
    text = f"{thread.get('subject', '')} {thread.get('snippet', '')}".lower()
    return any(
        x in text
        for x in ("вложен", "attachment", ".pdf", ".doc", ".docx", ".xlsx", ".zip", "📎")
    )


def is_notification_thread(thread: dict) -> bool:
    from_ = str(thread.get("previewFrom") or thread.get("from") or "").lower()
    return any(
        x in from_
        for x in ("noreply", "no-reply", "notification", "mailer-daemon", "уведомлен", "donotreply")
    )


def is_template_thread(thread: dict) -> bool:
    text = f"{thread.get('subject', '')} {thread.get('snippet', '')}".lower()
    return "template" in text or "шаблон" in text


def match_folder(thread: dict, folder: str, starred_ids: set[str] | None = None) -> bool:
    stars = starred_ids or set()
    if folder == "inbox":
        return thread.get("category") not in HIDDEN_IN_INBOX and not thread.get("isArchived")
    if folder == "important":
        return str(thread.get("id")) in stars
    if folder == "with_attachments":
        return thread_has_attachments(thread) and not thread.get("isArchived")
    if folder == "sent":
        return thread.get("category") == "outbound"
    if folder == "zoho":
        return "zoho" in f"{thread.get('subject', '')} {thread.get('snippet', '')}".lower()
    if folder == "templates":
        return is_template_thread(thread)
    if folder in ("mailing", "campaign"):
        return thread.get("category") == "campaign"
    if folder == "notifications":
        return is_notification_thread(thread)
    if folder == "archive":
        return bool(thread.get("isArchived"))
    if folder in ("trash", "drafts", "spam"):
        return False
    return True


def match_search_filters(thread: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    if filters.get("attachments") and not thread_has_attachments(thread):
        return False
    if filters.get("from"):
        q = str(filters["from"]).strip().lower()
        from_ = str(thread.get("previewFrom") or thread.get("from") or "").lower()
        if q not in from_:
            return False
    if filters.get("to"):
        q = str(filters["to"]).strip().lower()
        to = str(thread.get("previewTo") or thread.get("to") or thread.get("recipients") or "").lower()
        if q not in to:
            return False
    if filters.get("folderKey") and not match_folder(thread, filters["folderKey"]):
        return False
    return True


def filter_email_threads(
    threads,
    *,
    folder="inbox",
    search="",
    account_id=None,
    search_filters=None,
    starred_ids=None,
):
    list_ = list(threads)
    stars = {str(x) for x in (starred_ids or [])}
    if account_id is not None and account_id != "":
        list_ = [t for t in list_ if t.get("accountId") == account_id]
    if folder and folder not in ("campaign_mass", "campaigns_manage", "nurture_touch"):
        list_ = [t for t in list_ if match_folder(t, folder, stars)]
    q = (search or "").strip().lower()
    if q:
        list_ = [
            t
            for t in list_
            if q in str(t.get("subject") or "").lower()
            or q in str(t.get("snippet") or "").lower()
            or q in str(t.get("previewFrom") or "").lower()
        ]
    if search_filters:
        list_ = [t for t in list_ if match_search_filters(t, search_filters)]
    return list_


def count_email_folder(threads, folder, starred_ids=None):
    return len(filter_email_threads(threads, folder=folder, search="", starred_ids=starred_ids))


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


def test_important_starred_only():
    threads = [
        {"id": 1, "category": "inbound", "isArchived": False},
        {"id": 2, "category": "inbound", "isArchived": False},
    ]
    out = filter_email_threads(threads, folder="important", starred_ids={"1"})
    assert [t["id"] for t in out] == [1]


def test_with_attachments_heuristic():
    threads = [
        {"id": 1, "category": "inbound", "snippet": "см. вложение pdf"},
        {"id": 2, "category": "inbound", "snippet": "привет"},
    ]
    out = filter_email_threads(threads, folder="with_attachments")
    assert [t["id"] for t in out] == [1]


def test_notifications_folder():
    threads = [
        {"id": 1, "category": "inbound", "previewFrom": "noreply@service.com"},
        {"id": 2, "category": "inbound", "previewFrom": "client@corp.ru"},
    ]
    out = filter_email_threads(threads, folder="notifications")
    assert [t["id"] for t in out] == [1]


def test_search_filter_attachments_chip():
    threads = [
        {"id": 1, "category": "inbound", "snippet": "file.pdf"},
        {"id": 2, "category": "inbound", "snippet": "ok"},
    ]
    out = filter_email_threads(threads, folder="inbox", search_filters={"attachments": True})
    assert [t["id"] for t in out] == [1]
