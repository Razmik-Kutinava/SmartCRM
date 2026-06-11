"""
ORM модель лида (как в Битрикс: компания, контакт, статус, источник, сумма и т.д.)
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base

from core.lead_approvals import merge_approvals_payload


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
    # Суммы сделки в ₽ (менеджер); для отчётов и подсказок воронки
    amount_rub: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True, default=None)
    paid_amount_rub: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True, default=None)
    position: Mapped[str] = mapped_column(String(255), default="—")
    website: Mapped[str] = mapped_column(String(255), default="—")
    employees: Mapped[str] = mapped_column(String(100), default="—")
    industry: Mapped[str] = mapped_column(String(255), default="—")
    city: Mapped[str] = mapped_column(String(255), default="—")
    responsible: Mapped[str] = mapped_column(String(255), default="Я")
    next_call: Mapped[str] = mapped_column(String(100), default="—")
    description: Mapped[str] = mapped_column(Text, default="")

    # Чеклист апрувов/документов (JSON camelCase), референс — CRM points system
    approvals: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True, default=None)

    # ── Bitrix24 (дедуп при повторном импорте) ───────────────────────────────
    bitrix_lead_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # ── Идентификаторы (из Checko/DaData) ─────────────────────────────────────
    inn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    ogrn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)

    # ── Полные данные в JSON (из Checko) ──────────────────────────────────────
    checko_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    tech_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    financials_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

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
        import json
        checko = {}
        tech = {}
        financials = {}
        try:
            if self.checko_json:
                checko = json.loads(self.checko_json)
        except Exception:
            pass
        try:
            if self.tech_json:
                tech = json.loads(self.tech_json)
        except Exception:
            pass
        try:
            if self.financials_json:
                financials = json.loads(self.financials_json)
        except Exception:
            pass

        def _money(v: Optional[Decimal]) -> Optional[float]:
            if v is None:
                return None
            return float(v)

        approvals_out = merge_approvals_payload(getattr(self, "approvals", None), {})

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
            "amountRub": _money(self.amount_rub),
            "paidAmountRub": _money(self.paid_amount_rub),
            "position": self.position,
            "website": self.website,
            "employees": self.employees,
            "industry": self.industry,
            "city": self.city,
            "responsible": self.responsible,
            "nextCall": self.next_call,
            "description": self.description,
            "created": self.created_at.strftime("%d.%m.%Y") if self.created_at else "—",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            # Новые поля
            "bitrixLeadId": self.bitrix_lead_id,
            "inn": self.inn or "",
            "ogrn": self.ogrn or "",
            "checko": checko,
            "tech": tech,
            "financials": financials,
            "approvals": approvals_out,
        }
