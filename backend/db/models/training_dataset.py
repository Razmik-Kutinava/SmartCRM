"""
Датасеты для подготовки fine-tune: пары фраза → JSON Hermes, сырой текст из PDF.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class TrainingDataset(Base):
    """Набор записей для выгрузки во внешний fine-tune."""

    __tablename__ = "training_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    # draft | ready | error | processing
    meta_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # последний импорт: { "errors": [...], "imported": N, "skipped": M }

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

    records: Mapped[list["TrainingRecord"]] = relationship(
        "TrainingRecord", back_populates="dataset", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "meta_json": self.meta_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TrainingRecord(Base):
    """
    Одна строка датасета.
    record_type: pair — готовая пара для обучения; raw — фрагмент из PDF без разметки.
    """

    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sort_idx: Mapped[int] = mapped_column(Integer, default=0, index=True)
    record_type: Mapped[str] = mapped_column(String(16), default="pair")  # pair | raw
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    dataset: Mapped["TrainingDataset"] = relationship("TrainingDataset", back_populates="records")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "sort_idx": self.sort_idx,
            "record_type": self.record_type,
            "input_text": self.input_text,
            "output_json": self.output_json,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
