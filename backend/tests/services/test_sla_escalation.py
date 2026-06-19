"""Эскалация SLA."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.models.task import Task
from services.sla_escalation import run_sla_escalation_pass


@pytest.mark.asyncio
async def test_run_sla_escalation_pass():
    task = Task(
        id=1,
        title="Overdue",
        status="open",
        sla_due="01.01.2020",
        escalated=False,
        lead_id=5,
        assignee="Я",
        due="—",
        related_lead="Co",
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [task]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    with patch("services.sla_escalation.load_queue", return_value=[]), patch(
        "services.sla_escalation.save_queue"
    ):
        stats = await run_sla_escalation_pass(db)
    assert stats["escalated"] == 1
    assert task.escalated is True
