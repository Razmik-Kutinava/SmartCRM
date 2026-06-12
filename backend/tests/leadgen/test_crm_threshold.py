"""leadgen.crm_threshold — порог автосохранения в CRM."""
import json

from leadgen.crm_threshold import (
    DEFAULT_CRM_SCORE_THRESHOLD,
    get_crm_score_threshold,
    should_autosave_to_crm,
)


def test_should_autosave_respects_threshold():
    assert should_autosave_to_crm(True, 50, threshold=30) is True
    assert should_autosave_to_crm(True, 20, threshold=30) is False
    assert should_autosave_to_crm(False, 100, threshold=0) is False


def test_get_crm_score_threshold_from_config(tmp_path, monkeypatch):
    cfg = tmp_path / "leadgen_config.json"
    cfg.write_text(json.dumps({"score_threshold_crm": 45}), encoding="utf-8")
    monkeypatch.setattr("leadgen.crm_threshold._CONFIG_PATH", str(cfg))
    assert get_crm_score_threshold() == 45


def test_get_crm_score_threshold_invalid_json_fallback(monkeypatch):
    monkeypatch.setattr("leadgen.crm_threshold._CONFIG_PATH", "/nonexistent/path.json")
    assert get_crm_score_threshold() == DEFAULT_CRM_SCORE_THRESHOLD
