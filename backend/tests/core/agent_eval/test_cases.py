"""Smoke: eval-кейсы Hermes и 5 агентов — количество и схема."""
from __future__ import annotations

import pytest

from core.agent_eval import (
    AGENT_IDS,
    AGENT_MIN_CASES,
    HERMES_MIN_CASES,
    load_agent_cases,
    load_hermes_cases,
    validate_agent_case,
)
from core.agent_eval.score import score_case


def test_hermes_cases_count():
    cases = load_hermes_cases()
    assert len(cases) >= HERMES_MIN_CASES, f"Hermes: {len(cases)} < {HERMES_MIN_CASES}"


@pytest.mark.parametrize("agent_id", AGENT_IDS)
def test_agent_cases_count(agent_id: str):
    cases = load_agent_cases(agent_id)
    assert len(cases) >= AGENT_MIN_CASES, f"{agent_id}: {len(cases)} < {AGENT_MIN_CASES}"


@pytest.mark.parametrize("agent_id", AGENT_IDS)
def test_agent_cases_schema(agent_id: str):
    seen: set[str] = set()
    for case in load_agent_cases(agent_id):
        assert case["agent"] == agent_id
        assert case["id"] not in seen, f"duplicate id {case['id']}"
        seen.add(case["id"])
        errs = validate_agent_case(case)
        assert not errs, f"{case['id']}: {errs}"


def test_score_case_pass_and_fail():
    case = {"must_contain": ["бюджет"], "must_not_contain": ["галлюцина"]}
    ok, _ = score_case({"summary": "Бюджет 500к"}, case)
    assert ok
    bad, reason = score_case({"summary": "галлюцинация данных"}, case)
    assert not bad
    assert "forbidden" in reason
