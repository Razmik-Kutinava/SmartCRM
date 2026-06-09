"""Fuzzy-стадии из crm_settings."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from core.hermes.stage_fuzzy import resolve_stage_fuzzy


def test_resolve_known_stage():
    assert resolve_stage_fuzzy("переговоры") == "Переговоры"


def test_resolve_typo_close():
    assert resolve_stage_fuzzy("переговор", ["Переговоры", "Новый"]) == "Переговоры"


def test_resolve_kp_alias():
    stages = ["Новый", "КП отправлено", "Переговоры"]
    assert resolve_stage_fuzzy("кп", stages) == "КП отправлено"
