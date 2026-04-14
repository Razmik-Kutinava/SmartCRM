"""
Правила поведения агентов при работе с почтой.
Хранятся в БД — редактируются через Ops UI без деплоя.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class AgentEmailIntent(Base):
    __tablename__ = "agent_email_intents"

    id: Mapped[int]         = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)          # marketer | analyst | all
    intent_name: Mapped[str] = mapped_column(String(255), nullable=False)         # "клиент молчит 7 дней"
    trigger_keywords: Mapped[str] = mapped_column(String(500), default="")        # "молч,тишина,не отвеч"
    action_template: Mapped[str]  = mapped_column(Text, nullable=False)           # что делать агенту
    priority: Mapped[int]   = mapped_column(Integer, default=0)                   # выше = важнее
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "agentName":        self.agent_name,
            "intentName":       self.intent_name,
            "triggerKeywords":  self.trigger_keywords,
            "actionTemplate":   self.action_template,
            "priority":         self.priority,
            "isActive":         self.is_active,
            "created":          self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
        }
