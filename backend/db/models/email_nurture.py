"""Ф3: цепочки 20 касаний — ORM."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class EmailNurtureChain(Base):
    __tablename__ = "email_nurture_chains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="20 касаний")
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|paused|done
    steps_total: Mapped[int] = mapped_column(Integer, default=20)
    steps_sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "leadId": self.lead_id,
            "accountId": self.account_id,
            "name": self.name,
            "status": self.status,
            "stepsTotal": self.steps_total,
            "stepsSent": self.steps_sent,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "pausedAt": self.paused_at.isoformat() if self.paused_at else None,
        }


class EmailNurtureStep(Base):
    __tablename__ = "email_nurture_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_nurture_chains.id"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    day_offset: Mapped[int] = mapped_column(Integer, default=0)
    channel: Mapped[str] = mapped_column(String(32), default="email")
    action: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|sent|skipped|task

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "chainId": self.chain_id,
            "stepIndex": self.step_index,
            "dayOffset": self.day_offset,
            "channel": self.channel,
            "action": self.action,
            "subject": self.subject,
            "body": self.body,
            "scheduledAt": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sentAt": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
        }
