"""Политика «тест на фичу» зафиксирована в репо (не gate, но обязательна для PR)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_pr_checklist_documents_feature_test_rule():
    text = (REPO / "docs/dev/PR_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Тест на фичу" in text
    assert "pytest" in text.lower()


def test_contributing_documents_feature_test_rule():
    text = (REPO / "docs/dev/CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "минимум 1 pytest" in text.lower() or "минимум 1 pytest" in text
