"""API strategist suggester."""
from unittest.mock import AsyncMock, patch

import pytest

_APPEND = "Добавь в промпт примеры писем для B2B-производства. " * 2


@pytest.mark.asyncio
async def test_strategist_suggest_api(client):
    fake = {
        "ok": True,
        "has_suggestions": True,
        "summary": "test",
        "signals": {"total": 1},
        "suggestions": [{"agent_id": "marketer", "prompt_append": _APPEND}],
    }
    with patch(
        "core.strategist_suggester.gather_weak_signals",
        new_callable=AsyncMock,
        return_value={"total": 1},
    ), patch(
        "core.strategist_suggester.suggest_prompt_fixes",
        new_callable=AsyncMock,
        return_value=fake,
    ):
        r = await client.post("/api/ops/strategist/suggest-prompts", json={})
    assert r.status_code == 200
    assert r.json()["has_suggestions"] is True


@pytest.mark.asyncio
async def test_strategist_apply_api(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "api.routes.ops.agents_routes._backend_data_dir",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "core.agent_prompt_versions._DATA",
        tmp_path / "prompt_versions",
    )
    from agents.marketer import MARKETER_SYSTEM_PROMPT

    (tmp_path / "agent_prompt_marketer.txt").write_text(MARKETER_SYSTEM_PROMPT, encoding="utf-8")

    r = await client.post(
        "/api/ops/strategist/apply-suggestion",
        json={"agent_id": "marketer", "prompt_append": _APPEND},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    text = (tmp_path / "agent_prompt_marketer.txt").read_text(encoding="utf-8")
    assert "Strategist suggester" in text
