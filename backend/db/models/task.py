"""
ORM модель задачи (CRM task — напоминания, звонки, встречи).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")   # open | done | cancelled
    due: Mapped[str] = mapped_column(String(100), default="—")         # свободный текст: "завтра", "2024-05-01"
    assignee: Mapped[str] = mapped_column(String(255), default="Я")
    related_lead: Mapped[str] = mapped_column(String(255), default="")  # название компании-лида
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # опциональная связь с leads.id
    note: Mapped[str] = mapped_column(Text, default="")
    # SLA: срок обязательства по задаче (текст или ISO), эскалация при просрочке
    sla_due: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, default=None)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "due": self.due,
            "assignee": self.assignee,
            "relatedLead": self.related_lead,
            "leadId": self.lead_id,
            "note": self.note,
            "slaDue": self.sla_due,
            "escalated": self.escalated,
            "created": self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
        }
