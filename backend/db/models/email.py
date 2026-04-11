"""
ORM модели для почтовой подсистемы.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), default="generic")
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    imap_server: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    smtp_server: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, default=465)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
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
            "name": self.name,
            "provider": self.provider,
            "username": self.username,
            "imap_server": self.imap_server,
            "imap_port": self.imap_port,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "use_ssl": self.use_ssl,
            "lastSyncedAt": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "created": self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
        }


class EmailThread(Base):
    __tablename__ = "email_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), default="Без темы")
    thread_key: Mapped[str] = mapped_column(String(500), nullable=False)
    snippet: Mapped[str] = mapped_column(String(500), default="")
    category: Mapped[str] = mapped_column(String(100), default="general")
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "accountId": self.account_id,
            "leadId": self.lead_id,
            "subject": self.subject,
            "threadKey": self.thread_key,
            "snippet": self.snippet,
            "category": self.category,
            "lastMessageAt": self.last_message_at.isoformat() if self.last_message_at else None,
            "created": self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
        }


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    thread_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_threads.id"), nullable=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), nullable=True)
    message_id: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    in_reply_to: Mapped[str] = mapped_column(String(500), default="")
    subject: Mapped[str] = mapped_column(String(500), default="Без темы")
    sender: Mapped[str] = mapped_column(String(255), default="")
    recipients: Mapped[str] = mapped_column(String(1000), default="")
    cc: Mapped[str] = mapped_column(String(1000), default="")
    direction: Mapped[str] = mapped_column(String(50), default="inbound")
    category: Mapped[str] = mapped_column(String(100), default="general")
    snippet: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    raw_headers: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "accountId": self.account_id,
            "threadId": self.thread_id,
            "leadId": self.lead_id,
            "messageId": self.message_id,
            "inReplyTo": self.in_reply_to,
            "subject": self.subject,
            "sender": self.sender,
            "recipients": self.recipients,
            "cc": self.cc,
            "direction": self.direction,
            "category": self.category,
            "snippet": self.snippet,
            "body": self.body,
            "sentAt": self.sent_at.isoformat() if self.sent_at else None,
            "created": self.created_at.strftime("%d.%m.%Y %H:%M") if self.created_at else "—",
        }


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    lead_ids: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
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
            "accountId": self.account_id,
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "leadIds": [int(x) for x in self.lead_ids.split(",") if x.strip().isdigit()],
            "status": self.status,
            "sentCount": self.sent_count,
            "notes": self.notes,
            "created": self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
