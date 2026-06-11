"""IMAP fetch без live-ящика (мок MailBox)."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from imap_tools import AND

from email_sync.sync import _fetch_imap_messages, _imap_since_date, _parse_msg_date


def test_fetch_imap_messages_mocked():
    fake_msg = SimpleNamespace(
        subject="Test",
        text="hello",
        html="",
        date="Mon, 01 Jan 2024 12:00:00 +0000",
        from_="a@example.com",
        to="b@example.com",
        cc="",
        uid="1",
        message_id="<1@test>",
        in_reply_to="",
        obj=None,
    )
    account = SimpleNamespace(
        use_ssl=True,
        imap_server="imap.test",
        imap_port=993,
        username="u@test.com",
        password="enc",
    )

    with patch("imap_tools.MailBox") as mb_cls, patch(
        "email_sync.sync.decrypt", return_value="secret"
    ):
        mailbox = MagicMock()
        mailbox.__enter__.return_value = mailbox
        mailbox.fetch.return_value = [fake_msg]
        mb_cls.return_value = mailbox
        rows = _fetch_imap_messages(account)

    assert len(rows) == 1
    assert rows[0]["subject"] == "Test"
    mailbox.fetch.assert_called_once()
    mailbox.folder.set.assert_called_with("INBOX")


def test_parse_msg_date_from_datetime():
    dt = datetime(2026, 6, 11, 10, 53, 15, tzinfo=timezone.utc)
    assert _parse_msg_date(dt) == dt


def test_parse_msg_date_from_rfc_string():
    dt = _parse_msg_date("Thu, 11 Jun 2026 10:53:15 +0000")
    assert dt.year == 2026 and dt.month == 6 and dt.day == 11


def test_imap_since_date_window():
    account = SimpleNamespace(last_synced_at=datetime(2026, 6, 11, 15, 0, tzinfo=timezone.utc))
    since = _imap_since_date(account)
    assert (datetime.now(timezone.utc).date() - since).days >= 29


def test_fetch_imap_uses_since_criteria():
    fake_msg = SimpleNamespace(
        subject="New",
        text="hi",
        html="",
        date="Mon, 11 Jun 2026 12:00:00 +0000",
        from_="a@example.com",
        to="b@example.com",
        cc="",
        uid="2",
        message_id="<2@test>",
        in_reply_to="",
        obj=None,
    )
    account = SimpleNamespace(
        use_ssl=True,
        imap_server="imap.test",
        imap_port=993,
        username="u@test.com",
        password="enc",
        last_synced_at=datetime(2026, 6, 11, 10, 0, tzinfo=timezone.utc),
    )

    with patch("imap_tools.MailBox") as mb_cls, patch(
        "email_sync.sync.decrypt", return_value="secret"
    ):
        mailbox = MagicMock()
        mailbox.__enter__.return_value = mailbox
        mailbox.fetch.return_value = [fake_msg]
        mb_cls.return_value = mailbox
        rows = _fetch_imap_messages(account)

    assert len(rows) == 1
    kw = mailbox.fetch.call_args.kwargs
    assert kw["criteria"] == AND(date_gte=_imap_since_date(account))
