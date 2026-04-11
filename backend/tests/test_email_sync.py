import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from backend.email_sync.sync import _fetch_imap_messages
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_fetch_imap_messages_yandex():
    # Используй реальные тестовые данные или мок
    account = SimpleNamespace(
        imap_server='imap.yandex.com',
        imap_port=993,
        use_ssl=True,
        username='test@yandex.com',
        password='app-password',
    )
    try:
        messages = _fetch_imap_messages(account)
        assert isinstance(messages, list)
        print(f"Fetched {len(messages)} messages from Yandex")
    except Exception as e:
        print(f"IMAP fetch failed: {e}")
        assert False, f"IMAP fetch failed: {e}"
