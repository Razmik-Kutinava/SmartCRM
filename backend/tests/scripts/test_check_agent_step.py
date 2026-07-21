"""Тесты проверки свежести CHANGELOG/HANDOFF в check_agent_step."""
from scripts.check_agent_step import ops_freshness_errors

DONE = "2026-07-21 | Действие: шаг | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done"
RED = "2026-07-21 | Действие: RED подшаг | Коммит: `этот` | Статус: in_progress"

CHANGELOG_FRESH = "# CHANGELOG\n\n## 2026-07-21 — шаг\n\nтекст\n"
CHANGELOG_STALE = "# CHANGELOG\n\n## 2026-07-18 — старый шаг\n\nтекст\n"
HANDOFF_FRESH = "# HANDOFF\n\n**2026-07-21:** запись. Коммит: `этот`.\n"
HANDOFF_STALE = "# HANDOFF\n\n**2026-07-18:** старая запись.\n"


class TestOpsFreshness:
    def test_fresh_ok(self):
        assert ops_freshness_errors(DONE, CHANGELOG_FRESH, HANDOFF_FRESH) == []

    def test_stale_changelog_fails(self):
        errors = ops_freshness_errors(DONE, CHANGELOG_STALE, HANDOFF_FRESH)
        assert len(errors) == 1
        assert "CHANGELOG.md" in errors[0]

    def test_stale_handoff_fails(self):
        errors = ops_freshness_errors(DONE, CHANGELOG_FRESH, HANDOFF_STALE)
        assert len(errors) == 1
        assert "HANDOFF.md" in errors[0]

    def test_both_stale_two_errors(self):
        assert len(ops_freshness_errors(DONE, CHANGELOG_STALE, HANDOFF_STALE)) == 2

    def test_empty_journals_fail(self):
        assert len(ops_freshness_errors(DONE, "", "")) == 2

    def test_in_progress_skipped(self):
        """RED-подшаг: CHANGELOG/HANDOFF по правилу не пишутся — не проверяем."""
        assert ops_freshness_errors(RED, CHANGELOG_STALE, HANDOFF_STALE) == []

    def test_no_entry_skipped(self):
        assert ops_freshness_errors(None, CHANGELOG_STALE, HANDOFF_STALE) == []

    def test_newer_journal_date_ok(self):
        """Запись в журнале позже done-шага — тоже свежо."""
        old_done = DONE.replace("2026-07-21", "2026-07-18")
        assert ops_freshness_errors(old_done, CHANGELOG_FRESH, HANDOFF_FRESH) == []
