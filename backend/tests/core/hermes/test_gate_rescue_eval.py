"""Hermes eval-кейсы: rescue для типовых провалов gate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent

_REPO = Path(__file__).resolve().parents[4]
CASES = _REPO / "eval" / "cases.jsonl"
RESCUE_IDS = None  # all cases


def load_cases():
    cases = []
    with open(CASES, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    if RESCUE_IDS is None:
        return cases
    return [c for c in cases if c["id"] in RESCUE_IDS]


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
def test_rescue_matches_eval_intent(case):
    raw = rescue_route(case["text"])
    assert raw is not None, case["text"]
    got = normalize_parsed_intent(case["text"], raw).get("intent")
    assert got == case["expected_intent"], f"'{case['text']}' → {got}"
