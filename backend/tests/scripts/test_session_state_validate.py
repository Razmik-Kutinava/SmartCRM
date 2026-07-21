"""Тесты валидаторов шага: session_state_validate + check_rules_commit_conflict."""
from scripts.check_rules_commit_conflict import scan_file
from scripts.session_state_validate import validate_journal_line, validate_latest_entry


def _entry(tail: str) -> str:
    return f"2026-07-21 | Действие: тестовый шаг | {tail}"


class TestJournalLine:
    def test_done_with_hash_ok(self):
        line = _entry("Коммит: `abc1234` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done")
        assert validate_journal_line(line) == []

    def test_done_with_self_marker_ok(self):
        """«Коммит: `этот`» — один коммит на шаг, запись едет вместе с кодом."""
        line = _entry("Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done")
        assert validate_journal_line(line) == []

    def test_done_without_commit_fails(self):
        line = _entry("Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done")
        errors = validate_journal_line(line)
        assert any("Статус done" in e for e in errors)

    def test_commit_dash_fails(self):
        line = _entry("Коммит: — | Статус: done")
        assert validate_journal_line(line)

    def test_tail_incomplete_fails(self):
        line = _entry("Коммит: `этот` | Хвост A: нет | Статус: done")
        errors = validate_journal_line(line)
        assert any("Хвост B" in e for e in errors)
        assert any("Хвост C" in e for e in errors)

    def test_latest_entry_self_marker_ok(self):
        text = "# SESSION_STATE\n\nшапка\n\n" + _entry(
            "Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done"
        )
        assert validate_latest_entry(text) == []


class TestCommitConflictPatterns:
    def _scan(self, tmp_path, text: str) -> list[str]:
        f = tmp_path / "sample.md"
        f.write_text(text, encoding="utf-8")
        return scan_file(f)

    def test_deferred_commit_detected(self, tmp_path):
        assert self._scan(tmp_path, "жду коммит от пользователя")

    def test_wait_for_go_not_flagged(self, tmp_path):
        """«жду явного go» — легитимная формулировка про push, не про коммит."""
        assert self._scan(tmp_path, "push — только по явному go, жду явного go пользователя") == []

    def test_bounded_distance_not_flagged(self, tmp_path):
        far = "скажи как у нас дела по фазе четыре и какие планы на этот коммит"
        assert self._scan(tmp_path, far) == []

    def test_self_marker_not_flagged(self, tmp_path):
        assert self._scan(tmp_path, "в журнале писать Коммит: `этот`") == []
