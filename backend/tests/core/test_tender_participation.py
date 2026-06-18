"""Вердикт участия в тендере."""
from __future__ import annotations

import pytest

from core.tender_participation import (
    VERDICT_CAUTION,
    VERDICT_NO,
    VERDICT_PARTICIPATE,
    extract_participation,
)


def test_extract_from_participation_verdict_field():
    out = extract_participation(
        {
            "strategist_output": {
                "participation_verdict": "no",
                "decision": "Не участвовать — нет маржи",
                "rationale": "Маржа 5%",
            },
            "tech_output": {"summary": "ТЗ ок"},
            "economist_output": {"summary": "Дорого"},
        }
    )
    assert out["verdict"] == VERDICT_NO
    assert out["label"] == "Не участвовать"


def test_extract_classify_participate():
    out = extract_participation(
        {
            "strategist_output": {"decision": "Участвовать — проходим по ТЗ"},
            "final_reply": "Рекомендую подачу заявки",
        }
    )
    assert out["verdict"] == VERDICT_PARTICIPATE


def test_extract_classify_caution():
    out = extract_participation(
        {
            "strategist_output": {
                "decision": "Участвовать осторожно",
                "final_reply": "Нужны разъяснения по SLA",
            },
        }
    )
    assert out["verdict"] == VERDICT_CAUTION
