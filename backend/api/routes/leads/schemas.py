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
    deal_amount: float | None = Field(
        None, validation_alias=AliasChoices("deal_amount", "dealAmount", "amount")
    )
    deal_currency: str | None = Field(
        None, validation_alias=AliasChoices("deal_currency", "dealCurrency", "currency")
    )
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
    deal_amount: float | None = Field(
        None, validation_alias=AliasChoices("deal_amount", "dealAmount", "amount")
    )
    deal_currency: str | None = Field(
        None, validation_alias=AliasChoices("deal_currency", "dealCurrency", "currency")
    )
    position: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[str] = None
    industry: Optional[str] = None
    industry_verified: Optional[bool] = Field(
        None, validation_alias=AliasChoices("industryVerified", "industry_verified")
    )
    products_owned: Optional[list[str]] = Field(
        None, validation_alias=AliasChoices("productsOwned", "products_owned")
    )
    lead_products: Optional[list[dict[str, Any]]] = Field(
        None, validation_alias=AliasChoices("leadProducts", "lead_products")
    )
    city: Optional[str] = None
    responsible: Optional[str] = None
    next_call: Optional[str] = None
    description: Optional[str] = None
    contacts: Optional[list[dict[str, Any]]] = None
    approvals: Optional[dict[str, Any]] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    checko_json: Optional[Any] = Field(
        None, validation_alias=AliasChoices("checkoJson", "checko_json")
    )
    tech_json: Optional[Any] = Field(
        None, validation_alias=AliasChoices("techJson", "tech_json")
    )
    financials_json: Optional[Any] = Field(
        None, validation_alias=AliasChoices("financialsJson", "financials_json")
    )
    okved_main: Optional[str] = Field(None, validation_alias=AliasChoices("okvedMain", "okved_main"))
    okved_name: Optional[str] = Field(None, validation_alias=AliasChoices("okvedName", "okved_name"))
    okved_section: Optional[str] = Field(None, validation_alias=AliasChoices("okvedSection", "okved_section"))
    employees_band: Optional[str] = Field(None, validation_alias=AliasChoices("employeesBand", "employees_band"))
    portrait_score: Optional[int] = Field(None, validation_alias=AliasChoices("portraitScore", "portrait_score"))
    industry_bucket: Optional[str] = Field(None, validation_alias=AliasChoices("industryBucket", "industry_bucket"))


class LookalikeCandidate(BaseModel):
    company: str = Field(..., min_length=1, max_length=500)
    inn: str | None = None
    city: str = "—"
    industry: str = "—"
    score: int = Field(default=50, ge=0, le=100)
    matched_by: list[str] = Field(default_factory=list)


class LookalikeImportBody(BaseModel):
    leads: list[LookalikeCandidate] = Field(..., min_length=1, max_length=20)
