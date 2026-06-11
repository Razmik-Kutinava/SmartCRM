"""IMAP fetch без live-ящика (мок MailBox)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from email_sync.sync import _fetch_imap_messages


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
