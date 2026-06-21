"""Зеркало stageBadgeClass из frontend/src/lib/crmStages.js."""
from __future__ import annotations

from pathlib import Path

_CRM_STAGES = Path(__file__).resolve().parents[3] / "frontend" / "src" / "lib" / "crmStages.js"


def test_stage_badge_class_exported():
    text = _CRM_STAGES.read_text(encoding="utf-8")
    assert "export function stageBadgeClass" in text
    assert "STAGE_BADGE_CLASSES" in text
    assert "bg-green-900 text-green-300" in text
    assert "bg-red-900 text-red-300" in text
