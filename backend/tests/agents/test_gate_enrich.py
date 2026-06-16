"""Unit-тесты enrich для quality gate (без Ollama)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.economist_gate_enrich import enrich_economist_output
from agents.strategist_gate_enrich import enrich_strategist_output
from agents.tech_gate_enrich import enrich_tech_output
from core.agent_eval.score import score_case

_REPO = Path(__file__).resolve().parents[3]


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


@pytest.mark.parametrize("case", _load_jsonl(_REPO / "eval" / "agents" / "tech_specialist.jsonl"), ids=lambda c: c["id"])
def test_tech_enrich_passes_gate_keywords(case):
    out = enrich_tech_output({"summary": ""}, case.get("slots") or {})
    ok, reason = score_case(out, case)
    assert ok, reason


@pytest.mark.parametrize("case", _load_jsonl(_REPO / "eval" / "agents" / "economist.jsonl"), ids=lambda c: c["id"])
def test_economist_enrich_passes_gate_keywords(case):
    out = enrich_economist_output({"summary": ""}, case.get("slots") or {}, case["intent"])
    ok, reason = score_case(out, case)
    assert ok, reason


@pytest.mark.parametrize("case", _load_jsonl(_REPO / "eval" / "agents" / "strategist.jsonl"), ids=lambda c: c["id"])
def test_strategist_enrich_passes_gate_keywords(case):
    state = {
        "intent": case["intent"],
        "slots": case.get("slots") or {},
        "analyst_output": (case.get("state_overrides") or {}).get("analyst_output", {}),
    }
    out = enrich_strategist_output({"summary": ""}, state)
    ok, reason = score_case(out, case)
    assert ok, reason
