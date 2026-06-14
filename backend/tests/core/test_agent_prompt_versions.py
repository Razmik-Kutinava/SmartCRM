"""Тесты версионирования промптов агентов."""
from __future__ import annotations

import pytest


@pytest.fixture
def versions_data(monkeypatch, tmp_path):
    monkeypatch.setattr("core.agent_prompt_versions._DATA", tmp_path)
    return tmp_path


def test_save_version_dedup(versions_data):
    from core.agent_prompt_versions import list_versions, save_version

    text = "x" * 50 + "\n# v1"
    v1 = save_version("analyst", text, note="save")
    v2 = save_version("analyst", text, note="save")
    assert v1 == v2
    assert len(list_versions("analyst")) == 1


def test_save_multiple_and_list(versions_data):
    from core.agent_prompt_versions import get_version_text, list_versions, save_version

    save_version("marketer", "a" * 50, note="save")
    save_version("marketer", "b" * 50, note="save")
    versions = list_versions("marketer")
    assert len(versions) == 2
    assert versions[0]["id"].startswith("v")
    assert get_version_text("marketer", versions[0]["id"]).startswith("b")


def test_compare_texts_diff():
    from core.agent_prompt_versions import compare_texts

    out = compare_texts("line1\nline2", "line1\nline3")
    assert out["added_lines"] >= 1
    assert out["removed_lines"] >= 1
    assert out["diff"]


@pytest.mark.asyncio
async def test_ops_prompt_versions_api(client, monkeypatch, tmp_path):
    monkeypatch.setattr("core.agent_prompt_versions._DATA", tmp_path / "pv")
    base = "/api/ops/agents/marketer/prompt"
    v1 = "x" * 50 + "\n# version one"
    v2 = "y" * 50 + "\n# version two"

    r1 = await client.put(base, json={"prompt": v1})
    assert r1.status_code == 200
    assert r1.json().get("version_id")

    r2 = await client.put(base, json={"prompt": v2})
    assert r2.status_code == 200

    listed = (await client.get(f"{base}/versions")).json()["versions"]
    assert len(listed) >= 2

    old_id = listed[1]["id"]
    restore = await client.post(f"{base}/versions/{old_id}/restore")
    assert restore.status_code == 200
    assert (await client.get(base)).json()["prompt"].startswith("x")

    cmp_r = await client.get(f"{base}/versions/compare", params={"left": "builtin", "right": "current"})
    assert cmp_r.status_code == 200
    assert "diff" in cmp_r.json()

    await client.delete(base)


@pytest.mark.asyncio
async def test_hermes_prompt_versions_api(client, monkeypatch, tmp_path):
    monkeypatch.setattr("core.agent_prompt_versions._DATA", tmp_path / "pv")
    base = "/api/ops/hermes/prompt"
    from core.hermes import SYSTEM_PROMPT

    v1 = SYSTEM_PROMPT[:200] + "\n# hermes test v1 " + "x" * 20
    v2 = SYSTEM_PROMPT[:200] + "\n# hermes test v2 " + "y" * 20

    r1 = await client.post(base, json={"prompt": v1})
    assert r1.status_code == 200
    assert r1.json().get("version_id")

    r2 = await client.post(base, json={"prompt": v2})
    assert r2.status_code == 200

    listed = (await client.get(f"{base}/versions")).json()["versions"]
    assert len(listed) >= 2

    old_id = listed[1]["id"]
    restore = await client.post(f"{base}/versions/{old_id}/restore")
    assert restore.status_code == 200

    cmp_r = await client.get(f"{base}/versions/compare", params={"left": "builtin", "right": "current"})
    assert cmp_r.status_code == 200
    assert "diff" in cmp_r.json()

    await client.delete(base)
