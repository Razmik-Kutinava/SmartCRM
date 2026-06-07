"""
Аудит изменений полей лида (P2), append-only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class LeadFieldAudit(Base):
    __tablename__ = "lead_field_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(80), nullable=False)
    old_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(255), default="Менеджер")
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    event_type: Mapped[str] = mapped_column(String(64), default="field_change")
    audit_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True, default=None
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "leadId": self.lead_id,
            "field": self.field_name,
            "oldValue": self.old_value,
            "newValue": self.new_value,
            "actor": self.actor,
            "changedAt": self.changed_at.isoformat() if self.changed_at else None,
            "eventType": self.event_type,
            "metadata": self.audit_metadata if self.audit_metadata is not None else {},
        }
