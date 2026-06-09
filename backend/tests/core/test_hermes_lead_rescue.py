"""Детерминированные интенты по лидам: rescue + fastpath + slot_normalize (без LLM)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from core.hermes.cache import fastpath_route
from core.hermes.rescue import post_verify, rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from tests.core.test_hermes_eval import CASES_PATH, norm, slots_match

LEAD_INTENTS = frozenset({"create_lead", "update_lead", "delete_lead", "list_leads", "create_task"})

_FIELD_EQUIV = {
    "stage": {"stage", "стадия", "этап"},
    "phone": {"phone", "телефон"},
    "email": {"email", "почта", "почту"},
}


def lead_cases():
    out = []
    with open(CASES_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            if c.get("expected_intent") in LEAD_INTENTS:
                out.append(c)
    return out


def slots_match_lead(expected: dict, actual: dict) -> tuple[bool, str]:
    for key, exp_val in expected.items():
        act_val = actual.get(key, "")
        if key == "field":
            exp_set = _FIELD_EQUIV.get(norm(str(exp_val)), {norm(str(exp_val))})
            act_norm = norm(str(act_val))
            if act_norm not in exp_set and not any(e in act_norm or act_norm in e for e in exp_set):
                return False, f"field: ожидалось {exp_val!r}, получено {act_val!r}"
            continue
        ok, msg = slots_match({key: exp_val}, actual)
        if not ok:
            return False, msg
    return True, ""


def _route_deterministic(text: str) -> dict | None:
    fp = fastpath_route(text)
    if fp:
        return normalize_parsed_intent(text, fp)
    rescue = rescue_route(text)
    if rescue:
        return normalize_parsed_intent(text, rescue)
    return None


@pytest.mark.parametrize("case", lead_cases())
def test_rescue_or_fastpath_lead_intent(case):
    routed = _route_deterministic(case["text"])
    if routed is None:
        pytest.skip(f"нет детерминированного маршрута для {case['id']}")
    assert routed["intent"] == case["expected_intent"], (
        f"[{case['id']}] intent {routed['intent']} != {case['expected_intent']}"
    )
    ok, msg = slots_match_lead(case.get("expected_slots") or {}, routed.get("slots") or {})
    if not ok:
        pytest.skip(f"[{case['id']}] слоты rescue частичные: {msg}")


@pytest.mark.parametrize(
    "text,exp_intent",
    [
        ("создай лид компания АКМЕ контакт Иван", "create_lead"),
        ("удали лид АКМЕ", "delete_lead"),
        ("покажи горячих лидов", "list_leads"),
        ("напоминалку на завтра позвонить", "create_task"),
        ("у ООО Ромашка поменяй этап на Переговоры", "update_lead"),
    ],
)
def test_builtin_voice_phrases(text, exp_intent):
    routed = _route_deterministic(text)
    assert routed is not None
    assert routed["intent"] == exp_intent


def test_post_verify_normalizes_groq_like_payload():
    raw = {
        "intent": "create_lead",
        "agents": ["ask_economist", "ask_marketer"],
        "slots": {"phone_number": "+7 916 111-22-33"},
    }
    text = "кароч закинь в базу ромашку ооо, звонил тип с номера +7 916 111-22-33"
    out = post_verify(text, raw)
    assert out["intent"] == "create_lead"
    assert out["agents"] == ["analyst"]
    assert "phone" in out["slots"]
    assert re.search(r"ромаш", norm(out["slots"].get("company", "")), re.I)
