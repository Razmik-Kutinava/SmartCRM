"""Pydantic-схемы REST API лидов."""
from datetime import datetime
from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, Field


class LeadCreate(BaseModel):
    company: str
    contact: str = "—"
    email: str = "—"
    phone: str = "—"
    stage: str = "Новый"
    score: int = 50
    source: str = "—"
    budget: str = "—"
    amount_rub: float | None = Field(None, validation_alias=AliasChoices("amount_rub", "amountRub"))
    paid_amount_rub: float | None = Field(None, validation_alias=AliasChoices("paid_amount_rub", "paidAmountRub"))
    position: str = "—"
    website: str = "—"
    employees: str = "—"
    industry: str = "—"
    city: str = "—"
    responsible: str = "Я"
    next_call: str = "—"
    description: str = ""
    approvals: Optional[dict[str, Any]] = None


class BitrixImportBody(BaseModel):
    """Импорт лидов из Битрикс24 (входящий вебхук, переменная BITRIX24_WEBHOOK_URL)."""

    date_from: str = "2023-01-01"
    max_items: int = Field(
        default=0,
        ge=0,
        description="0 = без верхнего лимита (идём по next пока не кончится); иначе макс. число обработанных лидов",
    )


class LeadCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)
    author: str = Field(default="Менеджер", max_length=255)


class LeadCommunicationCreate(BaseModel):
    communication_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        validation_alias=AliasChoices("communicationType", "communication_type"),
    )
    content: str = ""
    actor: str = Field(default="Менеджер", max_length=255)
    occurred_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("occurredAt", "occurred_at"),
    )


class LeadPatch(BaseModel):
    company: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    stage: Optional[str] = None
    score: Optional[int] = None
    source: Optional[str] = None
    budget: Optional[str] = None
    amount_rub: float | None = Field(None, validation_alias=AliasChoices("amount_rub", "amountRub"))
    paid_amount_rub: float | None = Field(None, validation_alias=AliasChoices("paid_amount_rub", "paidAmountRub"))
    position: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    responsible: Optional[str] = None
    next_call: Optional[str] = None
    description: Optional[str] = None
    approvals: Optional[dict[str, Any]] = None
