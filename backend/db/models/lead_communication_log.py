"""
Лог касаний по лиду (слой B): звонки, встречи, письма — аналог communication_logs в CRM points system.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class LeadCommunicationLog(Base):
    __tablename__ = "lead_communication_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    communication_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(255), default="Менеджер")
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "leadId": self.lead_id,
            "communicationType": self.communication_type,
            "content": self.content,
            "actor": self.actor,
            "occurredAt": self.occurred_at.isoformat() if self.occurred_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
