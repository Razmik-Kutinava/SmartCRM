"""Маппинг секции ОКВЭД (01–99) → укрупнённая отрасль CRM."""
from __future__ import annotations

# Синхрон с services.industry_catalog.FIXED_INDUSTRIES
INDUSTRY_BUCKETS: tuple[str, ...] = (
    "IT и телеком",
    "Финансы и страхование",
    "Ритейл и e-commerce",
    "Производство",
    "Строительство",
    "Транспорт и логистика",
    "Государственный сектор",
    "Образование",
    "Медицина и фарма",
    "Энергетика",
    "Нефть и газ",
    "HoReCa",
    "Агропром",
    "Медиа и реклама",
    "Другое",
)

_AGRO = "Агропром"
_PROD = "Производство"
_RETAIL = "Ритейл и e-commerce"
_BUILD = "Строительство"
_TRANS = "Транспорт и логистика"
_HORECA = "HoReCa"
_MEDIA = "Медиа и реклама"
_IT = "IT и телеком"
_FIN = "Финансы и страхование"
_GOV = "Государственный сектор"
_EDU = "Образование"
_MED = "Медицина и фарма"
_ENERGY = "Энергетика"
_OIL = "Нефть и газ"
_OTHER = "Другое"

# ОКВЭД 2, разделы 01–99 → bucket (Росстат / укрупнение под CRM)
OKVED_SECTION_TO_INDUSTRY: dict[str, str] = {
    "01": _AGRO,
    "02": _AGRO,
    "03": _AGRO,
    "05": _ENERGY,
    "06": _OIL,
    "07": _PROD,
    "08": _PROD,
    "09": _OIL,
    "10": _PROD,
    "11": _PROD,
    "12": _PROD,
    "13": _PROD,
    "14": _PROD,
    "15": _PROD,
    "16": _PROD,
    "17": _PROD,
    "18": _MEDIA,
    "19": _OIL,
    "20": _PROD,
    "21": _MED,
    "22": _PROD,
    "23": _BUILD,
    "24": _PROD,
    "25": _PROD,
    "26": _IT,
    "27": _PROD,
    "28": _PROD,
    "29": _PROD,
    "30": _PROD,
    "31": _PROD,
    "32": _PROD,
    "33": _PROD,
    "35": _ENERGY,
    "36": _OTHER,
    "37": _OTHER,
    "38": _OTHER,
    "39": _OTHER,
    "41": _BUILD,
    "42": _BUILD,
    "43": _BUILD,
    "45": _RETAIL,
    "46": _RETAIL,
    "47": _RETAIL,
    "49": _TRANS,
    "50": _TRANS,
    "51": _TRANS,
    "52": _TRANS,
    "53": _TRANS,
    "55": _HORECA,
    "56": _HORECA,
    "58": _MEDIA,
    "59": _MEDIA,
    "60": _MEDIA,
    "61": _IT,
    "62": _IT,
    "63": _IT,
    "64": _FIN,
    "65": _FIN,
    "66": _FIN,
    "68": _OTHER,
    "69": _FIN,
    "70": _OTHER,
    "71": _BUILD,
    "72": _OTHER,
    "73": _MEDIA,
    "74": _OTHER,
    "75": _MED,
    "77": _OTHER,
    "78": _OTHER,
    "79": _OTHER,
    "80": _OTHER,
    "81": _OTHER,
    "82": _OTHER,
    "84": _GOV,
    "85": _EDU,
    "86": _MED,
    "87": _MED,
    "88": _OTHER,
    "90": _MEDIA,
    "91": _EDU,
    "92": _OTHER,
    "93": _OTHER,
    "94": _OTHER,
    "95": _IT,
    "96": _OTHER,
    "97": _OTHER,
    "98": _OTHER,
    "99": _OTHER,
}

_EMPTY = frozenset({"", "—", "-", "null", "none"})


def _norm_section(section: str) -> str:
    s = str(section or "").strip()
    if not s or s.lower() in _EMPTY:
        return ""
    if s.isdigit():
        return s.zfill(2)[:2]
    return s[:2] if len(s) >= 2 and s[:2].isdigit() else ""


def industry_bucket_from_okved_section(section: str | None) -> str:
    """Отрасль по первым двум цифрам ОКВЭД."""
    code = _norm_section(section or "")
    if not code:
        return ""
    return OKVED_SECTION_TO_INDUSTRY.get(code, _OTHER)


def match_industry_text_to_bucket(text: str | None) -> str:
    """Сопоставить свободный текст industry с bucket (для ручных значений)."""
    raw = str(text or "").strip()
    if not raw or raw in _EMPTY:
        return ""
    low = raw.casefold()
    for bucket in INDUSTRY_BUCKETS:
        if bucket.casefold() == low:
            return bucket
    aliases = {
        "it": _IT,
        "телеком": _IT,
        "софт": _IT,
        "разработка": _IT,
        "финанс": _FIN,
        "банк": _FIN,
        "страх": _FIN,
        "ритейл": _RETAIL,
        "e-commerce": _RETAIL,
        "магазин": _RETAIL,
        "производ": _PROD,
        "завод": _PROD,
        "строит": _BUILD,
        "логист": _TRANS,
        "транспорт": _TRANS,
        "гос": _GOV,
        "образован": _EDU,
        "медиц": _MED,
        "фарм": _MED,
        "энерг": _ENERGY,
        "нефт": _OIL,
        "газ": _OIL,
        "horeca": _HORECA,
        "ресторан": _HORECA,
        "отель": _HORECA,
        "агро": _AGRO,
        "сельхоз": _AGRO,
        "реклам": _MEDIA,
        "медиа": _MEDIA,
    }
    for key, bucket in aliases.items():
        if key in low:
            return bucket
    return ""


def resolve_industry_bucket(
    *,
    okved_section: str | None = None,
    industry: str | None = None,
) -> str:
    """Итоговый bucket: ОКВЭД → приоритет, иначе текст industry."""
    from_okved = industry_bucket_from_okved_section(okved_section)
    if from_okved:
        return from_okved
    return match_industry_text_to_bucket(industry)
