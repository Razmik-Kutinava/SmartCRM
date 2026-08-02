"""Нормализация названия компании для ЕГРЮЛ: EN→RU алиасы, срез суффиксов."""
from __future__ import annotations

import re

# Известные бренды (латиница / короткий ключ → русское юр. имя для поиска)
_BRAND_RU: dict[str, str] = {
    "otp": "ОТП Банк",
    "otp bank": "ОТП Банк",
    "otpbank": "ОТП Банк",
    "sber": "Сбербанк",
    "sberbank": "Сбербанк",
    "yandex": "Яндекс",
    "vk": "ВК",
    "mail.ru": "Мэйл.Ру",
    "mailru": "Мэйл.Ру",
    "gazprom": "Газпром",
    "lukoil": "Лукойл",
    "rosneft": "Роснефть",
    "mts": "МТС",
    "megafon": "Мегафон",
    "beeline": "Вымпелком",
    "tinkoff": "Тинькофф",
    "t-bank": "ТБанк",
    "tbank": "ТБанк",
    "alfa": "Альфа-Банк",
    "alfabank": "Альфа-Банк",
    "alfa-bank": "Альфа-Банк",
    "vtb": "ВТБ",
    "raiffeisen": "Райффайзенбанк",
    "unicredit": "ЮниКредит Банк",
    "citibank": "Ситибанк",
    "hsbc": "Эйч-эс-би-си",
    "microsoft": "Майкрософт",
    "google": "Гугл",
    "apple": "Эппл",
    "samsung": "Самсунг",
    "huawei": "Хуавей",
    "xiaomi": "Сяоми",
    "nestle": "Нестле",
    "pepsico": "Пепсико",
    "coca-cola": "Кока-Кола",
    "philip morris": "Филип Моррис",
    "hochland": "Хохланд",
}


def _strip_noise(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\s*[\(\[\{][^\)\]\}]{0,40}[\)\]\}]\s*", " ", s)
    s = re.sub(r"\b(russia|russian federation|llc|ltd|inc|gmbh|jsc|pjsc|ooo)\b", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ,.-")
    return s


def _brand_key(name: str) -> str:
    s = _strip_noise(name).lower().replace("ё", "е")
    s = re.sub(r"[\"«»']", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def company_search_variants(company: str) -> list[str]:
    """Варианты запросов: оригинал → очищенный → RU-алиас → бренд+Банк."""
    raw = (company or "").strip()
    if not raw:
        return []

    out: list[str] = []
    seen: set[str] = set()

    def add(q: str) -> None:
        q = (q or "").strip()
        if not q:
            return
        key = q.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(q)

    add(raw)
    cleaned = _strip_noise(raw)
    add(cleaned)

    key = _brand_key(raw)
    if key in _BRAND_RU:
        add(_BRAND_RU[key])
    # частичный ключ (первое слово / без bank)
    first = key.split()[0] if key else ""
    if first in _BRAND_RU:
        add(_BRAND_RU[first])
    no_bank = re.sub(r"\bbank\b", "", key).strip()
    if no_bank in _BRAND_RU:
        add(_BRAND_RU[no_bank])

    # латиница → попробовать «бренд Банк» если слово bank было
    if re.search(r"\bbank\b", key) and first and first.isascii():
        add(f"{first.upper()} Банк" if len(first) <= 4 else f"{first.title()} Банк")

    return out[:6]
