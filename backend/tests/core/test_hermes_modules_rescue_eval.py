"""Rescue-eval для модулей Hermes Ф2 (без LLM)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent

_REPO = Path(__file__).resolve().parents[3]
CASES = _REPO / "eval" / "cases_modules.jsonl"


def load_module_cases():
    cases = []
    with open(CASES, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


@pytest.mark.parametrize("case", load_module_cases(), ids=lambda c: c["id"])
def test_rescue_module_contract(case):
    raw = rescue_route(case["text"])
    assert raw is not None, case["text"]
    out = normalize_parsed_intent(case["text"], raw)
    assert out["intent"] == case["expected_intent"]
    assert out["module"] == case["expected_module"]
    assert out["ui_action"] == case["expected_ui_action"]
    for key, val in (case.get("expected_slots") or {}).items():
        assert out["slots"].get(key) == val, f"{key}: {out['slots'].get(key)} != {val}"


def test_cases_modules_file_exists():
    assert CASES.is_file()
