"""Rescue/add_communication и eval-кейсы CPU."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent

_REPO = Path(__file__).resolve().parents[4]
CASES = _REPO / "eval" / "cases.jsonl"


def _load(ids: list[str]):
    rows = []
    with open(CASES, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return [r for r in rows if r["id"] in ids]


def _norm(s: str) -> str:
    return str(s).lower().replace("ё", "е")


def _digits(s: str) -> str:
    d = re.sub(r"\D", "", str(s))
    if d.startswith("8") and len(d) == 11:
        d = "7" + d[1:]
    return d


_FIELD_EQUIV = {
    "stage": {"stage", "стадия", "этап"},
    "phone": {"phone", "телефон"},
    "email": {"email", "почта"},
}


def _slots_ok(expected: dict, actual: dict) -> bool:
    for k, v in expected.items():
        av = actual.get(k, "")
        if k == "field":
            exp = _norm(str(v))
            act = _norm(str(av))
            matched = exp == act
            for equiv in _FIELD_EQUIV.values():
                if exp in equiv and act in equiv:
                    matched = True
                    break
            if not matched:
                return False
            continue
        if k == "value":
            fld = _norm(str(expected.get("field", actual.get("field", ""))))
            if fld in {"phone", "телефон"} and _digits(v) == _digits(av):
                continue
        if _norm(str(v)) not in _norm(str(av)) and _norm(str(av)) not in _norm(str(v)):
            return False
    return True


def test_add_communication_rescue():
    text = "запиши касание звонок по лиду АКМЕ «обсудили бюджет»"
    raw = rescue_route(text)
    assert raw is not None
    out = normalize_parsed_intent(text, raw)
    assert out["intent"] == "add_communication"
    assert out["slots"]["company"].lower().startswith("акме")
    assert "бюджет" in out["slots"]["content"].lower()


def test_eval_cpu_cases():
    for case in _load(["eval-003", "eval-020", "eval-034", "eval-035", "eval-036"]):
        raw = rescue_route(case["text"])
        assert raw is not None, case["id"]
        out = normalize_parsed_intent(case["text"], raw)
        assert out["intent"] == case["expected_intent"], case["id"]
        assert _slots_ok(case["expected_slots"], out.get("slots") or {}), case["id"]
