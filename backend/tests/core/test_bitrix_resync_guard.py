"""bitrix_resync_guard — пауза auto-sync на время mass-resync."""
from pathlib import Path

from core.bitrix_resync_guard import (
    fields_resync_state_path,
    is_fields_resync_running,
    read_fields_resync_state,
)


def test_is_fields_resync_running_false_when_missing(tmp_path, monkeypatch):
    path = tmp_path / "bitrix_fields_resync_state.json"
    monkeypatch.setattr("core.bitrix_resync_guard._STATE_PATH", path)
    assert is_fields_resync_running() is False


def test_is_fields_resync_running_true(tmp_path, monkeypatch):
    path = tmp_path / "bitrix_fields_resync_state.json"
    monkeypatch.setattr("core.bitrix_resync_guard._STATE_PATH", path)
    path.write_text('{"status": "running", "processed": 10}', encoding="utf-8")
    assert is_fields_resync_running() is True
    assert read_fields_resync_state()["processed"] == 10
    assert fields_resync_state_path() == path
