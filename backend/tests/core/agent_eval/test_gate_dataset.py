import pytest

from core.agent_eval.gate_dataset import build_record_payload, case_source


def test_case_source_hermes():
    c = case_source("hermes", "eval-001")
    assert c and c["id"] == "eval-001"


def test_build_record_payload_analyst():
    p = build_record_payload("analyst", "analyst-001")
    assert "intent" in p["input_text"]
    assert p["output_json"]["must_contain"]


def test_build_record_payload_missing():
    with pytest.raises(ValueError):
        build_record_payload("analyst", "no-such-id")
