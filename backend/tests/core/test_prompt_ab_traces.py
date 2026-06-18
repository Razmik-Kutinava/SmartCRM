"""Тесты A/B промптов по плохим трейсам."""
from __future__ import annotations

import pytest

from core import traces
from core.prompt_ab_traces import collect_bad_trace_cases, run_prompt_ab_on_traces


def test_collect_bad_trace_cases_dedup(monkeypatch):
    monkeypatch.setattr(traces, "get_traces", lambda limit=500: [
        {"id": "a1", "text": "создай лид", "feedback": "bad", "intent": "noop"},
        {"id": "a2", "text": "создай лид", "feedback": "bad", "intent": "noop"},
        {"id": "a3", "text": "найди лид", "error": "timeout", "intent": None},
        {"id": "a4", "text": "ок", "feedback": "good", "intent": "noop"},
    ])
    cases = collect_bad_trace_cases(10)
    assert len(cases) == 2
    assert cases[0]["text"] == "создай лид"
    assert cases[1]["trace_id"] == "a3"


@pytest.mark.asyncio
async def test_run_prompt_ab_on_traces_no_bad(monkeypatch):
    monkeypatch.setattr(traces, "get_traces", lambda limit=500: [])
    out = await run_prompt_ab_on_traces("x" * 80, max_bad_traces=5)
    assert out["ok"] is False
    assert out["error"] == "no_bad_traces"


@pytest.mark.asyncio
async def test_run_prompt_ab_on_traces_compare(monkeypatch):
    monkeypatch.setattr(traces, "get_traces", lambda limit=500: [
        {"id": "b1", "text": "удали лид 5", "feedback": "bad", "intent": "noop"},
    ])

    async def fake_enrich(cases):
        for c in cases:
            c["expected"] = "delete_lead"

    monkeypatch.setattr("core.prompt_ab_traces.enrich_expected_from_eval_db", fake_enrich)

    async def fake_pipeline(cases, models, *, system_prompt=None):
        is_var = system_prompt and "VARIANT" in system_prompt
        intent = "delete_lead" if is_var else "noop"
        correct = intent == cases[0].get("expected")
        return {
            "cases_count": len(cases),
            "summary": {
                models[0]: {
                    "correct": 1 if correct else 0,
                    "total": 1,
                    "accuracy_pct": 100 if correct else 0,
                    "avg_ms": 10,
                }
            },
            "results": [{
                "text": cases[0]["text"],
                "expected": cases[0].get("expected"),
                "models": {
                    models[0]: {
                        "intent": intent,
                        "correct": correct,
                        "duration_ms": 10,
                    }
                },
            }],
        }

    monkeypatch.setattr("core.prompt_ab_traces.run_eval_pipeline", fake_pipeline)

    out = await run_prompt_ab_on_traces(
        "VARIANT " + "y" * 80,
        max_bad_traces=5,
        models=["hermes3"],
        baseline_prompt="BASE " + "x" * 80,
    )
    assert out["ok"] is True
    assert out["delta"]["fixes"] == 1
    assert out["delta"]["accuracy_pp"] == 100.0
    assert out["per_case"][0]["variant_intent"] == "delete_lead"
