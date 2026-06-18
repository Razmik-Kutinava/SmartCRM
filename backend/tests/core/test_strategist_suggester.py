"""Тесты авто-суфлёра Стратега."""
from __future__ import annotations

import pytest

from core import traces
from core.strategist_suggester import (
    collect_gate_failures,
    collect_hermes_bad_traces,
    gather_weak_signals,
    suggest_prompt_fixes,
)


def test_collect_hermes_bad_traces(monkeypatch):
    monkeypatch.setattr(traces, "get_traces", lambda limit=500: [
        {"text": "создай лид", "feedback": "bad", "intent": "noop"},
        {"text": "ок", "feedback": "good", "intent": "noop"},
    ])
    items = collect_hermes_bad_traces(5)
    assert len(items) == 1
    assert items[0]["source"] == "hermes_trace"


def test_collect_gate_failures_empty(monkeypatch):
    monkeypatch.setattr("core.strategist_suggester.load_latest_gate", lambda: (None, None))
    assert collect_gate_failures() == []


def test_collect_gate_failures_parses(monkeypatch):
    report = {
        "agents": {
            "marketer": {
                "results": [
                    {"id": "m-1", "passed": False, "reason": "must_contain fail"},
                    {"id": "m-2", "passed": True},
                ]
            }
        }
    }
    monkeypatch.setattr("core.strategist_suggester.load_latest_gate", lambda: ("x.json", report))
    items = collect_gate_failures(5)
    assert len(items) == 1
    assert items[0]["agent"] == "marketer"


@pytest.mark.asyncio
async def test_gather_weak_signals(monkeypatch):
    monkeypatch.setattr(traces, "get_traces", lambda limit=500: [
        {"text": "x", "feedback": "bad", "intent": "noop"},
    ])
    monkeypatch.setattr("core.strategist_suggester.load_latest_gate", lambda: (None, None))

    async def fake_runs(max_items=12):
        return [{"source": "agent_run", "agent": "marketer", "task": "t", "note": "", "summary": ""}]

    monkeypatch.setattr("core.strategist_suggester.collect_bad_agent_runs", fake_runs)
    sig = await gather_weak_signals()
    assert sig["total"] == 2


@pytest.mark.asyncio
async def test_suggest_no_signals():
    out = await suggest_prompt_fixes({"total": 0, "hermes_bad_traces": [], "gate_failures": [], "agent_bad_runs": []})
    assert out["has_suggestions"] is False


@pytest.mark.asyncio
async def test_suggest_with_mock_groq(monkeypatch):
    signals = {
        "total": 1,
        "hermes_bad_traces": [],
        "gate_failures": [{"agent": "marketer", "case_id": "m1", "reason": "bad tone"}],
        "agent_bad_runs": [],
    }
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    class FakeMsg:
        content = '{"summary":"ok","suggestions":[{"agent_id":"marketer","pattern":"p","explanation":"e","prompt_append":"Добавь примеры B2B писем для производства.","priority":"high"}]}'

    class FakeChoice:
        message = FakeMsg()

    class FakeResp:
        choices = [FakeChoice()]

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        class chat:
            class completions:
                @staticmethod
                async def create(**kwargs):
                    return FakeResp()

        async def close(self):
            pass

    monkeypatch.setattr("groq.AsyncGroq", lambda api_key: FakeClient())
    out = await suggest_prompt_fixes(signals)
    assert out["has_suggestions"] is True
    assert out["suggestions"][0]["agent_id"] == "marketer"
