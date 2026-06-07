"""Tenders API — фильтры и релевантность."""
from datetime import datetime

def _parse_any_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _to_number(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(" ", "").replace(",", "."))
    except Exception:
        return None


def _region_matches(item_region, region_filter: str | None) -> bool:
    if not region_filter:
        return True
    rf = str(region_filter).strip().lower()
    if not rf:
        return True
    ir = str(item_region or "").strip().lower()
    if not ir:
        return False
    return ir == rf or rf in ir


# Стоп-слова: предлоги/союзы, которые не должны считаться значимыми токенами.
_STOPWORDS = {
    "для", "или", "при", "его", "как", "что", "это", "все", "без",
    "the", "and", "for", "with", "from",
}


def _tokenize_query(q: str) -> list[str]:
    """Разбить запрос на значимые токены (len>=3, без стоп-слов, lowercased)."""
    if not q:
        return []
    raw = q.replace(",", " ").replace(";", " ").split()
    return [
        t.lower() for t in raw
        if len(t.strip()) >= 3 and t.lower() not in _STOPWORDS
    ]


def _query_hits(q: str, text: str) -> int:
    hay = (text or "").lower()
    return sum(1 for t in _tokenize_query(q) if t in hay)


def _estimate_relevance(q: str, text: str, has_budget: bool, has_deadline: bool) -> int:
    tokens = _tokenize_query(q)
    hay = (text or "").lower()
    hits = sum(1 for t in tokens if t in hay)
    if not tokens:
        # Запрос пустой/из одних стоп-слов — нечего ранжировать, даём нейтрал.
        score = 50
    elif hits == 0:
        # Ни одного совпадения — позиция в хвосте, но не ноль (для источников,
        # где кодировка может исказить текст).
        score = 10
    else:
        # Базовый скор + бонус за долю покрытия запроса
        coverage = hits / len(tokens)
        score = 35 + int(coverage * 55)
    if has_budget:
        score += 5
    if has_deadline:
        score += 5
    return max(1, min(99, score))


def _passes_local_filters(
    item: dict,
    region: str | None,
    price_min: int | None,
    price_max: int | None,
    date_start: str | None,
    date_end: str | None,
) -> bool:
    if not _region_matches(item.get("region"), region):
        return False

    budget = _to_number(item.get("budget"))
    if price_min is not None and budget is not None and budget < price_min:
        return False
    if price_max is not None and budget is not None and budget > price_max:
        return False

    dl = _parse_any_date(item.get("deadline"))
    ds = _parse_any_date(date_start)
    de = _parse_any_date(date_end)
    if ds and dl and dl < ds:
        return False
    if de and dl and dl > de:
        return False

    return True


def _normalize_item_for_ui(item: dict) -> dict:
    """
    Унифицирует поля результата под текущий frontend.
    """
    out = dict(item or {})
    out["title"] = out.get("title") or out.get("name") or ""
    out["url"] = out.get("url") or out.get("external_url") or out.get("inner_url") or ""
    if not out.get("deadline"):
        out["deadline"] = out.get("date_end") or out.get("DateEnd")
    if not out.get("published"):
        out["published"] = out.get("published_date") or out.get("Date")
    if not out.get("okpd"):
        out["okpd"] = out.get("okpd2") or out.get("Okpd2")
    return out


