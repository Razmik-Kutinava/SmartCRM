"""Импорт failed gate-кейса в training-датасет."""
from __future__ import annotations

import json
from typing import Any

from core.agent_eval.cases import load_agent_cases, load_hermes_cases
from core.agent_eval.gate_artifacts import load_latest_gate


def case_source(agent: str, case_id: str) -> dict[str, Any] | None:
    if agent == "hermes":
        for c in load_hermes_cases():
            if c.get("id") == case_id:
                return c
    elif agent in ("analyst", "economist", "marketer", "strategist", "tech_specialist"):
        for c in load_agent_cases(agent):
            if c.get("id") == case_id:
                return c
    return None


def build_record_payload(agent: str, case_id: str) -> dict[str, Any]:
    src = case_source(agent, case_id)
    if not src:
        raise ValueError(f"кейс {case_id} не найден для {agent}")
    _, report = load_latest_gate()
    fail_reason = ""
    if report:
        row = next(
            (r for r in (report.get("agents", {}).get(agent, {}).get("results") or []) if r.get("id") == case_id),
            None,
        )
        if row:
            fail_reason = row.get("reason") or row.get("error") or ""
    if agent == "hermes":
        inp = src["text"]
        notes = f"gate-fail hermes | expected {src.get('expected_intent')} | {fail_reason}"
        out = {"expected_intent": src.get("expected_intent"), "expected_slots": src.get("expected_slots")}
    else:
        inp = json.dumps({"intent": src["intent"], "slots": src.get("slots") or {}}, ensure_ascii=False)
        notes = f"gate-fail {agent} | {fail_reason}"
        out = {
            "must_contain": src.get("must_contain"),
            "must_not_contain": src.get("must_not_contain"),
        }
    return {"input_text": inp, "output_json": out, "notes": notes.strip(), "record_type": "pair"}
