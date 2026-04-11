"""
Сценарии для eval / обучения: фраза, ожидаемый интент, человекочитаемые критерии успеха.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class EvalScenario(Base):
    """
    Запись сценария проверки Hermes.
    status: draft | pending_review | approved | archived
    """

    __tablename__ = "eval_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    phrase: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[str] = mapped_column(String(128), nullable=False)
    expected_slots: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    success_criteria: Mapped[str] = mapped_column(
        Text,
        default="",
        comment="Критерий успеха для людей (что считаем правильным распознаванием)",
    )
    desired_outcome: Mapped[str] = mapped_column(
        Text,
        default="",
        comment="Чего хотим добиться сценарием в продукте",
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "phrase": self.phrase,
            "expected_intent": self.expected_intent,
            "expected_slots": self.expected_slots or {},
            "success_criteria": self.success_criteria,
            "desired_outcome": self.desired_outcome,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
