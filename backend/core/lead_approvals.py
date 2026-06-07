"""
Чеклист апрувов/документов по лиду (слой A — референс CRM points system: boolean + веса в scoring_advisory).
Ключи в API и в JSON колонке — camelCase.
"""
from __future__ import annotations

from typing import Any

# Согласовано с Rails ScoreCalculator + флаги «документов» из schema leads
APPROVAL_CAMEL_KEYS: tuple[str, ...] = (
    "lprEstablished",
    "assortmentAgreed",
    "priceAgreed",
    "termsAgreed",
    "paymentTermsAgreed",
    "securityPassed",
    "rebateAgreed",
    "contractSigned",
    "invoiceIssued",
    "contractSent",
    "contractSignedDoc",
    "kpSent",
    "presentationSent",
    "licenseShipped",
)

APPROVAL_LABELS_RU: dict[str, str] = {
    "lprEstablished": "ЛПР установлен",
    "assortmentAgreed": "Ассортимент согласован",
    "priceAgreed": "Цена согласована",
    "termsAgreed": "Условия согласованы",
    "paymentTermsAgreed": "Условия оплаты согласованы",
    "securityPassed": "Пройден security",
    "rebateAgreed": "Скидка согласована",
    "contractSigned": "Договор подписан (факт)",
    "invoiceIssued": "Счёт выставлен",
    "contractSent": "Договор отправлен",
    "contractSignedDoc": "Подписанный договор (документ)",
    "kpSent": "КП отправлено",
    "presentationSent": "Презентация отправлена",
    "licenseShipped": "Лицензия отгружена",
}


def default_approvals_dict() -> dict[str, bool]:
    return {k: False for k in APPROVAL_CAMEL_KEYS}


def merge_approvals_payload(existing: Any, patch: Any) -> dict[str, bool]:
    """Слияние текущего JSON из БД и PATCH (частичный объект)."""
    base = default_approvals_dict()
    if isinstance(existing, dict):
        for k in APPROVAL_CAMEL_KEYS:
            if k in existing:
                base[k] = bool(existing[k])
    if not isinstance(patch, dict):
        return base
    for k, v in patch.items():
        if k in APPROVAL_CAMEL_KEYS:
            base[k] = bool(v)
    return base
