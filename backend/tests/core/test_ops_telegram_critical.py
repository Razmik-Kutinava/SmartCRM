"""Ops critical → Telegram."""
from unittest.mock import patch

from core.ops_store import recompute_queue_and_suggestions


def test_recompute_notifies_new_critical(monkeypatch):
    monkeypatch.setattr("core.traces._traces", [{"error": "x"}] * 10)
    with patch("core.traces.get_stats", return_value={"total": 10, "groq_pct": 50}), patch(
        "core.ops_store.get_snapshots",
        return_value=[],
    ), patch(
        "core.ops_store.load_queue",
        return_value=[],
    ), patch("core.ops_store.save_queue"), patch(
        "integrations.telegram.notify.notify_ops_critical_sync",
    ) as notify:
        recompute_queue_and_suggestions(update_queue=True)
        assert notify.called
