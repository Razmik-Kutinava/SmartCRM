"""tools.py — X-API-Key для CLI gate при SMARTCRM_API_KEY."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_api_get_sends_api_key_header():
    os.environ["SMARTCRM_API_KEY"] = "test-gate-key"
    try:
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("agents.tools.httpx.AsyncClient", return_value=mock_client):
            from agents.tools import read_leads

            await read_leads(limit=1)

        mock_client.get.assert_called_once()
        _, kwargs = mock_client.get.call_args
        assert kwargs["headers"]["X-API-Key"] == "test-gate-key"
    finally:
        os.environ.pop("SMARTCRM_API_KEY", None)
