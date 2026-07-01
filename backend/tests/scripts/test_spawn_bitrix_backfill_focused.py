"""spawn_bitrix_backfill_focused — без timeline/watch."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "backend" / "scripts" / "spawn_bitrix_backfill_focused.py"


def test_focused_spawn_excludes_timeline_and_watch():
    text = _SCRIPT.read_text(encoding="utf-8")
    assert "timeline-only" not in text
    assert "watch_fields_resync" not in text
    assert "resync_bitrix_lead_tasks.py" in text
    assert "require-task-scope" in text


def test_mark_timeline_done_logic(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("spawn_focused", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    state_path = tmp_path / "bitrix_timeline_resync_state.json"
    state_path.write_text(
        json.dumps({"status": "running", "processed": 3230, "total_b24": 3230}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "TIMELINE_STATE", state_path)
    mod._mark_timeline_done_if_complete()
    out = json.loads(state_path.read_text(encoding="utf-8"))
    assert out["status"] == "done"
