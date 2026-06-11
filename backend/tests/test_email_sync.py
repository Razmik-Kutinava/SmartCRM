"""Legacy live IMAP — только с EMAIL_SYNC_LIVE=1 и реальными кредами в .env."""
import os
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("EMAIL_SYNC_LIVE", "").strip().lower() not in ("1", "true", "yes"),
    reason="live IMAP: задайте EMAIL_SYNC_LIVE=1 и EMAIL_APP_PASSWORD",
)


@pytest.mark.asyncio
async def test_fetch_imap_messages_live():
    from email_sync.sync import _fetch_imap_messages

    user = os.getenv("EMAIL_ACCOUNT_2_USER") or os.getenv("EMAIL_LIVE_USER", "")
    pwd = os.getenv("EMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD", "")
    host = os.getenv("EMAIL_IMAP_HOST", "imap.yandex.com")
    if not user or not pwd:
        pytest.skip("нет EMAIL_ACCOUNT_2_USER / EMAIL_APP_PASSWORD")

    account = SimpleNamespace(
        use_ssl=True,
        imap_server=host,
        imap_port=993,
        username=user,
        password=pwd,
    )
    # password в sync расшифровывается — для live подставим plain через patch decrypt
    from unittest.mock import patch

    with patch("email_sync.sync.decrypt", side_effect=lambda x: x):
        messages = _fetch_imap_messages(account)
    assert isinstance(messages, list)
