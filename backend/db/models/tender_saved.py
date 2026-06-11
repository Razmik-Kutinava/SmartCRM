"""Сохранённые тендеры: «Мои» и «Архив»."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from db.session import Base

_JSON = JSON().with_variant(JSONB(), "postgresql")


class TenderSaved(Base):
    __tablename__ = "tender_saved"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(20), default="saved", index=True)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(_JSON, default=dict)
    tender_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        snap = self.snapshot_json or {}
        return {
            "id": self.id,
            "externalId": self.external_id,
            "source": self.source,
            "status": self.status,
            "snapshot": snap,
            "title": snap.get("title") or snap.get("name") or "",
            "customer": snap.get("customer") or "",
            "budget": snap.get("budget"),
            "deadline": snap.get("deadline"),
            "url": snap.get("url") or "#",
            "law": snap.get("law"),
            "tenderAnalysis": self.tender_analysis,
            "techAnalysis": self.tech_analysis,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "archivedAt": self.archived_at.isoformat() if self.archived_at else None,
        }
