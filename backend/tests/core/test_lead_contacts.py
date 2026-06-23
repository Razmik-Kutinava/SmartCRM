"""Контакты лида и автоматический ЛПР."""
from __future__ import annotations

from core.lead_contacts import (
    apply_contacts_patch,
    contacts_for_api,
    has_established_lpr,
    is_lpr_contact_complete,
    merge_bitrix_contacts,
    normalize_contacts,
)


def test_lpr_complete_requires_name_position_channel():
    ok = {
        "name": "Иван",
        "role": "lpr",
        "position": "ГД",
        "phones": ["+7999"],
        "emails": [],
        "messengers": [],
    }
    assert is_lpr_contact_complete(ok)
    assert has_established_lpr([ok])

    bad = {**ok, "position": ""}
    assert not is_lpr_contact_complete(bad)


def test_normalize_contacts_drops_empty_rows():
    rows = normalize_contacts([{"name": "A", "role": "other"}, {"name": "", "role": "lpr"}])
    assert len(rows) == 1
    assert rows[0]["name"] == "A"


def test_legacy_to_contacts_from_flat_lead():
    lead = {"contact": "Петр", "phone": "+7", "email": "—", "position": "Директор", "contacts": None}
    out = contacts_for_api(lead)
    assert len(out) == 1
    assert out[0]["role"] == "lpr"
    assert out[0]["phones"] == ["+7"]


def test_apply_contacts_patch_sets_lpr_approval():
    patch = apply_contacts_patch(
        None,
        [
            {
                "name": "Алексей",
                "role": "lpr",
                "position": "Собственник",
                "phones": ["+7900"],
                "emails": ["a@b.ru"],
            }
        ],
    )
    assert patch["approvals"]["lprEstablished"] is True
    assert patch["contact"] == "Алексей"
    assert patch["email"] == "a@b.ru"


def test_merge_bitrix_contacts_keeps_manual():
    existing = [
        {"id": "b24-contact-1", "name": "Старый", "role": "lpr", "phones": [], "emails": [], "messengers": []},
        {"id": "crm-uuid", "name": "Ручной", "role": "it", "phones": ["+7111"], "emails": [], "messengers": []},
    ]
    incoming = [
        {
            "id": "b24-contact-2",
            "name": "Новый ЛПР",
            "role": "lpr",
            "position": "ГД",
            "phones": ["+7222"],
            "emails": ["new@co.ru"],
            "messengers": [],
        },
        {
            "id": "b24-contact-3",
            "name": "Коллега",
            "role": "other",
            "position": "",
            "phones": [],
            "emails": ["c@co.ru"],
            "messengers": [],
        },
    ]
    merged = merge_bitrix_contacts(existing, incoming)
    assert len(merged) == 3
    assert merged[0]["id"] == "b24-contact-2"
    assert merged[-1]["id"] == "crm-uuid"
    assert merged[-1]["name"] == "Ручной"
