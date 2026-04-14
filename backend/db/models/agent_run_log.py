"""
Лог каждого запуска агента — для истории, обратной связи и few-shot обучения.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, Integer, Boolean, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class AgentRunLog(Base):
    __tablename__ = "agent_run_logs"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int]     = mapped_column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name: Mapped[str]  = mapped_column(String(100), nullable=False)
    task: Mapped[str]        = mapped_column(Text, default="")
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[str]    = mapped_column(String(20), default="")   # "" | "good" | "bad"
    feedback_note: Mapped[str] = mapped_column(Text, default="")       # комментарий к плохому ответу
    threads_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    intents_applied: Mapped[int]  = mapped_column(Integer, default=0)
    is_few_shot: Mapped[bool]     = mapped_column(Boolean, default=False)  # добавлен как пример
    created_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        r = self.result_json or {}
        return {
            "id":               self.id,
            "leadId":           self.lead_id,
            "agentName":        self.agent_name,
            "task":             self.task,
            "result":           r,
            "feedback":         self.feedback,
            "feedbackNote":     self.feedback_note,
            "threadsAnalyzed":  self.threads_analyzed,
            "intentsApplied":   self.intents_applied,
            "isFewShot":        self.is_few_shot,
            "created":          self.created_at.strftime("%d.%m.%Y %H:%M") if self.created_at else "—",
            # удобные поля для UI
            "emailSubject":     r.get("first_email", {}).get("subject", "") if isinstance(r, dict) else "",
            "emailBody":        r.get("first_email", {}).get("body", "")    if isinstance(r, dict) else "",
            "summary":          r.get("summary", "")                         if isinstance(r, dict) else "",
        }
