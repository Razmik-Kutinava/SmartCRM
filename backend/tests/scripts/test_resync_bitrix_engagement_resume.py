"""--offset в backfill_engagement (срез лидов)."""
from __future__ import annotations

from unittest.mock import MagicMock


def test_work_rows_slice_from_offset():
    rows = [MagicMock(id=i) for i in range(1, 6)]
    offset = 2
    work_rows = rows[offset:]
    assert len(work_rows) == 3
    assert work_rows[0].id == 3
