"""
Инструменты агентов SmartCRM.
Каждая функция — async, возвращает структурированные данные.
Агенты вызывают эти функции напрямую (не через LangChain tools schema).
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def _api_headers() -> dict[str, str]:
    key = os.getenv("SMARTCRM_API_KEY", "").strip()
    return {"X-API-Key": key} if key else {}


async def _api_get(path: str) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{_BACKEND_URL}{path}", headers=_api_headers())
        r.raise_for_status()
        return r.json()


async def _api_patch(path: str, data: dict) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.patch(f"{_BACKEND_URL}{path}", json=data, headers=_api_headers())
        r.raise_for_status()
        return r.json()


async def read_leads(limit: int = 100) -> list[dict]:
    """Получить список лидов из БД."""
    try:
        leads = await _api_get("/api/leads")
        return leads[:limit]
    except Exception as e:
        logger.warning("tools.read_leads ошибка: %s", e)
        return []


# --- Транслитерация RU↔EN (простая карта частых слов) ---
_TRANSLIT_RU_EN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

_TRANSLIT_COMMON_WORDS = {
    "банк": "bank", "банка": "bank", "банку": "bank", "банком": "bank", "банке": "bank",
    "аудит": "audit", "аудита": "audit", "аудиту": "audit", "аудитом": "audit", "аудите": "audit",
    "инвест": "invest", "инвестиции": "investments", "инвестиция": "investment",
    "страхование": "insurance", "страхования": "insurance",
    "лизинг": "leasing", "лизинга": "leasing",
    "факторинг": "factoring", "факторинга": "factoring",
    "консалтинг": "consulting", "консалтинга": "consulting",
    "аутсорсинг": "outsourcing", "аутсорсинга": "outsourcing",
    "разработка": "development", "разработки": "development",
    "производство": "manufacturing", "производства": "manufacturing",
    "торговля": "trade", "торговли": "trade",
    "строительство": "construction", "строительства": "construction",
    "недвижимость": "realestate", "недвижимости": "realestate",
    "логистика": "logistics", "логистики": "logistics",
    "транспорт": "transport", "транспорта": "transport",
    "энергетика": "energy", "энергетики": "energy",
    "нефть": "oil", "нефти": "oil",
    "газ": "gas", "газа": "gas",
    "металлы": "metals", "металлов": "metals",
    "химия": "chemicals", "химии": "chemicals",
    "фарма": "pharma", "фармы": "pharma",
    "медицина": "medical", "медицины": "medical",
    "образование": "education", "образования": "education",
    "ит": "it", "ai": "ai",
    "софт": "software", "софта": "software",
    "системы": "systems", "систем": "systems",
    "технологии": "technologies", "технологий": "technologies",
    "сервис": "service", "сервиса": "service",
    "сервисы": "services",
    "платформа": "platform", "платформы": "platform",
    "решение": "solution", "решения": "solutions",
    "продукт": "product", "продукты": "products",
    "компания": "company", "компании": "company",
    "группа": "group", "группы": "group",
    "холдинг": "holding", "холдинга": "holding",
    "корпорация": "corporation", "корпорации": "corporation",
    "центр": "center", "центра": "center",
    "институт": "institute", "института": "institute",
    "академия": "academy", "академии": "academy",
    "университет": "university", "университета": "university",
    "колледж": "college", "колледжа": "college",
    "школа": "school", "школы": "school",
    "больница": "hospital", "больницы": "hospital",
    "клиника": "clinic", "клиники": "clinic",
    "аптека": "pharmacy", "аптеки": "pharmacy",
    "магазин": "store", "магазины": "stores",
    "супермаркет": "supermarket", "супермаркеты": "supermarkets",
    "ресторан": "restaurant", "рестораны": "restaurants",
    "кафе": "cafe", "кафе": "cafe",
    "отель": "hotel", "отели": "hotels",
    "туризм": "tourism", "туризма": "tourism",
    "авиа": "avia", "аэро": "aero",
    "морской": "marine", "морская": "marine", "морское": "marine",
    "речной": "river", "речная": "river", "речное": "river",
    "жд": "rail", "жд": "railway",
    "авто": "auto", "авто": "auto",
    "мото": "moto",
    "вело": "velo", "вело": "bike",
    "электро": "electro", "электрика": "electrical",
    "газпром": "gazprom", "роснефть": "rosneft", "лукойл": "lukoil",
    "сбер": "sber", "сбербанк": "sberbank", "втб": "vtb", "альфа": "alfa",
    "тинькофф": "tinkoff", "рак뱅к": "raiffeisen", "райффайзен": "raiffeisen",
    "газпромбанк": "gazprombank", "мск": "moscow", "спб": "spb", "казань": "kazan",
    "екатеринбург": "ekaterinburg", "новосибирск": "novosibirsk",
    "красноярск": "krasnoyarsk", "челябинск": "chelyabinsk", "омск": "omsk",
    "ростов": "rostov", "уфа": "ufa", "воронеж": "voronezh", "пермь": "perm",
    "волгоград": "volgograd", "нижний": "nizhny", "новгород": "novgorod",
    "краснодар": "krasnodar", "саратов": "saratov", "тюмень": "tyumen",
    "тольятти": "tolyatti", "ижевск": "izhevsk", "барнаул": "barnaul",
    "ульяновск": "ulyanovsk", "иркутск": "irkutsk", "хабаровск": "khabarovsk",
    "владивосток": "vladivostok", "махачкала": "makhachkala", "томск": "tomsk",
    "оренбург": "orenburg", "кемерово": "kemerovo", "новокузнецк": "novokuznetsk",
    "рязань": "ryazan", "астрахань": "astrakhan", "набережные": "naberezhnye",
    "челны": "chelny", "пенза": "penza", "липецк": "lipetsk", "тула": "tula",
    "киров": "kirov", "чебоксары": "cheboksary", "калининград": "kaliningrad",
    "брянск": "bryansk", "курск": "kursk", "иваново": "ivanovo", "магнитогорск": "magnitogorsk",
    "бриansk": "bryansk", "курск": "kursk",
}


def _transliterate_ru_to_en(text: str) -> str:
    """Простая транслитерация RU→EN для поиска."""
    text = text.lower()
    # Сначала заменяем частые слова целиком
    for ru, en in _TRANSLIT_COMMON_WORDS.items():
        text = text.replace(ru, en)
    # Затем посимвольно для остального
    result = []
    for ch in text:
        result.append(_TRANSLIT_RU_EN.get(ch, ch))
    return "".join(result)


def _transliterate_en_to_ru(text: str) -> str:
    """Простая транслитерация EN→RU для поиска (обратная карта)."""
    # Обратная карта для частых слов
    en_to_ru = {v: k for k, v in _TRANSLIT_COMMON_WORDS.items()}
    text = text.lower()
    for en, ru in en_to_ru.items():
        text = text.replace(en, ru)
    return text


def _generate_search_variants(query: str) -> list[str]:
    """Сгенерировать варианты запроса с транслитерацией RU↔EN."""
    variants = [query.lower().strip()]
    # RU→EN
    variants.append(_transliterate_ru_to_en(query))
    # EN→RU
    variants.append(_transliterate_en_to_ru(query))
    # Убрать дубликаты с сохранением порядка
    seen = set()
    uniq = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def _lead_recency_score(lead: dict) -> float:
    """
    Скоринг актуальности лида:
    1) Открытая задача due≤сегодня / звонок 24ч — вес 1000
    2) Стадия: Переговоры=100, КП=50, Квалифицирован=20, Новый=10
    3) Скор 0-100 — вес 1
    4) updated_at свежесть — вес 0.01
    """
    score = 0.0
    now = datetime.now()

    # 1) Задачи/звонки
    next_call = lead.get("next_call") or lead.get("nextCall")
    if next_call and next_call != "—":
        try:
            # Попытка парсинга даты
            call_date = datetime.fromisoformat(str(next_call).replace("Z", "+00:00"))
            if call_date <= now:
                score += 1000  # просрочена или сегодня
            elif (call_date - now).total_seconds() <= 86400:  # 24 часа
                score += 500
        except Exception:
            pass

    # 2) Стадия
    stage = str(lead.get("stage") or "").strip()
    stage_weights = {
        "Переговоры": 100,
        "КП": 50,
        "КП отправлено": 50,
        "Квалифицирован": 20,
        "Новый": 10,
    }
    score += stage_weights.get(stage, 0)

    # 3) Скор
    lead_score = lead.get("score") or lead.get("scoreAdvisory", {}).get("suggestedScore")
    if lead_score is not None:
        try:
            score += float(lead_score) * 1
        except Exception:
            pass

    # 4) updated_at свежесть
    updated_at = lead.get("updated_at") or lead.get("updatedAt")
    if updated_at:
        try:
            upd = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
            days_ago = (now - upd).days
            score += max(0, 365 - days_ago) * 0.01
        except Exception:
            pass

    return score


async def read_lead_by_company(query: str, limit: int = 10) -> list[dict]:
    """
    Найти лиды по названию компании ИЛИ контакту с транслитерацией RU↔EN.
    Возвращает list[dict], отсортированный по актуальности (recency score).
    """
    try:
        leads = await read_leads(limit=500)  # берём больше для фильтрации
    except Exception as e:
        logger.warning("tools.read_lead_by_company ошибка чтения: %s", e)
        return []

    if not query or not query.strip():
        return []

    # Генерируем варианты поиска с транслитерацией
    search_variants = _generate_search_variants(query.strip())

    matched = []
    for lead in leads:
        company = str(lead.get("company") or "").lower()
        contact = str(lead.get("contact") or "").lower()
        lead_name = str(lead.get("lead_name") or lead.get("name") or "").lower()

        # Поиск по любому из вариантов
        for variant in search_variants:
            v = variant.lower()
            if v in company or v in contact or v in lead_name:
                normed = normalize_lead_for_agents(lead)
                normed["_recency_score"] = _lead_recency_score(lead)
                matched.append(normed)
                break

    # Сортировка по актуальности (убывание)
    matched.sort(key=lambda x: x.get("_recency_score", 0), reverse=True)

    # Убираем служебное поле
    for m in matched:
        m.pop("_recency_score", None)

    return matched[:limit]


def normalize_lead_for_agents(raw: dict[str, Any]) -> dict[str, Any]:
    """Приводит ответ API /api/leads к полям, которые ждут агенты (snake_case, note, lead_id)."""
    if not raw:
        return {}
    from rag.search.research_dossier import extract_web_research_brief

    out = dict(raw)
    nc = out.get("nextCall") or out.get("next_call")
    out["next_call"] = nc if nc not in (None, "") else "—"
    lid = out.get("id")
    if lid is not None:
        out["lead_id"] = lid
    desc = out.get("description") or ""
    out["note"] = desc
    # Досье из 🔍 — в note/description для агентов (без повторного веб-поиска)
    brief = extract_web_research_brief(out)
    if brief and "Веб-исследование" not in (out.get("note") or ""):
        out["note"] = f"{out['note']}\n\n{brief}".strip() if out.get("note") else brief
        out["description"] = out["note"]
    return out


async def read_lead_by_id(lead_id: int) -> Optional[dict]:
    """Получить лид по id (GET /api/leads/{id})."""
    try:
        data = await _api_get(f"/api/leads/{lead_id}")
        return normalize_lead_for_agents(data)
    except Exception as e:
        logger.warning("tools.read_lead_by_id(%s) ошибка: %s", lead_id, e)
        return None


async def update_lead_score(lead_id: int, score: int, reason: str = "") -> dict:
    """Обновить CRM-скор лида (0–100). По умолчанию отключено: балл задаёт менеджер в UI (crm_settings.agents_may_update_score)."""
    from core import crm_settings_store

    settings = crm_settings_store.load_settings()
    if settings.get("manager_sets_score", True) and not settings.get("agents_may_update_score", False):
        logger.info(
            "tools.update_lead_score пропущен (лид #%s): менеджер владеет score; agents_may_update_score=false",
            lead_id,
        )
        return {
            "ok": False,
            "skipped": True,
            "lead_id": lead_id,
            "message": "Скор в CRM меняет только менеджер; агент не перезаписывает поле score.",
            "reason": reason,
        }
    score = max(0, min(100, score))
    try:
        result = await _api_patch(f"/api/leads/{lead_id}", {"score": score})
        logger.info("Скор лида #%s обновлён → %s (%s)", lead_id, score, reason)
        return {"ok": True, "lead_id": lead_id, "score": score, "reason": reason}
    except Exception as e:
        logger.warning("tools.update_lead_score ошибка: %s", e)
        return {"ok": False, "error": str(e)}


async def update_lead_fields(lead_id: int, patch: dict) -> dict:
    """Обновить произвольные поля лида."""
    try:
        result = await _api_patch(f"/api/leads/{lead_id}", patch)
        return {"ok": True, "updated": patch, "lead": result}
    except Exception as e:
        logger.warning("tools.update_lead_fields ошибка: %s", e)
        return {"ok": False, "error": str(e)}


async def read_lead_audit(lead_id: int, limit: int = 60) -> list[dict]:
    try:
        return await _api_get(f"/api/leads/{lead_id}/audit?limit={limit}")
    except Exception as e:
        logger.warning("tools.read_lead_audit(%s) ошибка: %s", lead_id, e)
        return []


async def read_lead_comments(lead_id: int, limit: int = 40) -> list[dict]:
    try:
        return await _api_get(f"/api/leads/{lead_id}/comments?limit={limit}")
    except Exception as e:
        logger.warning("tools.read_lead_comments(%s) ошибка: %s", lead_id, e)
        return []


async def read_lead_communications(lead_id: int, limit: int = 40) -> list[dict]:
    try:
        return await _api_get(f"/api/leads/{lead_id}/communications?limit={limit}")
    except Exception as e:
        logger.warning("tools.read_lead_communications(%s) ошибка: %s", lead_id, e)
        return []


async def read_tasks(filter_status: str = "open") -> list[dict]:
    """Получить задачи по фильтру: open / done / all."""
    try:
        tasks = await _api_get("/api/tasks")
        if filter_status == "all":
            return tasks
        return [t for t in tasks if t.get("status") == filter_status]
    except Exception as e:
        logger.warning("tools.read_tasks ошибка: %s", e)
        return []


def compute_lead_score(lead: dict) -> tuple[int, str]:
    """
    Эвристический скоринг лида по доступным полям.
    Возвращает (score: int, explanation: str).
    """
    score = 30
    reasons = []

    if lead.get("contact") and lead["contact"] != "—":
        score += 10
        reasons.append("+10 есть контактное лицо")
    if lead.get("phone") and lead["phone"] != "—":
        score += 10
        reasons.append("+10 есть телефон")
    if lead.get("email") and lead["email"] != "—":
        score += 8
        reasons.append("+8 есть email")
    if lead.get("budget") and lead["budget"] != "—":
        score += 15
        reasons.append("+15 указан бюджет")
        try:
            budget_val = int("".join(c for c in str(lead["budget"]) if c.isdigit()))
            if budget_val >= 1_000_000:
                score += 10
                reasons.append("+10 бюджет ≥1 млн")
        except Exception:
            pass
    if lead.get("industry") and lead["industry"] != "—":
        score += 5
        reasons.append("+5 указана отрасль")
    if lead.get("city") and lead["city"] != "—":
        score += 3
        reasons.append("+3 указан город")
    if lead.get("website") and lead["website"] != "—":
        score += 5
        reasons.append("+5 есть сайт")
    if lead.get("description") and len(lead.get("description", "")) > 20:
        score += 5
        reasons.append("+5 есть заметки")

    stage = lead.get("stage", "Новый")
    stage_bonus = {
        "Квалифицирован": 10,
        "КП отправлено": 15,
        "Переговоры": 20,
        "Выигран": 0,
        "Проигран": -20,
    }.get(stage, 0)
    if stage_bonus:
        score += stage_bonus
        reasons.append(f"{stage_bonus:+d} этап «{stage}»")

    score = max(5, min(99, score))
    return score, "; ".join(reasons)