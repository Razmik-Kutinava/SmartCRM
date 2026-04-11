"""
ORM модель лида (как в Битрикс: компания, контакт, статус, источник, сумма и т.д.)
"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), default="—")
    email: Mapped[str] = mapped_column(String(255), default="—")
    phone: Mapped[str] = mapped_column(String(100), default="—")
    stage: Mapped[str] = mapped_column(String(100), default="Новый")
    score: Mapped[int] = mapped_column(Integer, default=50)
    source: Mapped[str] = mapped_column(String(100), default="—")
    budget: Mapped[str] = mapped_column(String(100), default="—")
    position: Mapped[str] = mapped_column(String(255), default="—")
    website: Mapped[str] = mapped_column(String(255), default="—")
    employees: Mapped[str] = mapped_column(String(100), default="—")
    industry: Mapped[str] = mapped_column(String(255), default="—")
    city: Mapped[str] = mapped_column(String(255), default="—")
    responsible: Mapped[str] = mapped_column(String(255), default="Я")
    next_call: Mapped[str] = mapped_column(String(100), default="—")
    description: Mapped[str] = mapped_column(Text, default="")
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
            "company": self.company,
            "contact": self.contact,
            "email": self.email,
            "phone": self.phone,
            "stage": self.stage,
            "score": self.score,
            "source": self.source,
            "budget": self.budget,
            "position": self.position,
            "website": self.website,
            "employees": self.employees,
            "industry": self.industry,
            "city": self.city,
            "responsible": self.responsible,
            "nextCall": self.next_call,
            "description": self.description,
            "created": self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
        }
