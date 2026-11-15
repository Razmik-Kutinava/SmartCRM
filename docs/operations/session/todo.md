# todo — микро-чеклист текущей фичи (SBR)

## Заказ (дословно)

> «Сейчас read_lead_by_company возвращает только один лид и ищет только по полю company. Надо: вернуть список до 10 лидов с полями id, company, city, stage, score, next_call. Искать не только по company, но и по названию лида (name / title / lead_name — поле модели Lead). Поддержка транслитерации: кириллица ↔ латиница, чтобы "акбарс банк ад аудит" и "akbars bank ad audit" находили один и тот же лид. Функция transliterate_ru_en(text) + поиск по обоим вариантам (нормализованный текст / SQL ILIKE с обоими формами).»

---

## Как понял (1–2 строки)
Расширить `read_lead_by_company` до полнотекстового поиска по `company` И `lead_name` с транслитерацией RU↔EN, возвращать список кандидатов до 10 штук с полями для сортировки/отображения.

---

## Чеклист микро-шагов

- [x] **backend/agents/tools.py** — `read_lead_by_company(query: str, limit: int = 10) -> list[dict]`:
  - Принимать строку запроса (не только название компании)
  - Генерировать два варианта: исходный + транслитерированный (`transliterate_ru_en`)
  - Поиск по `company` / `contact` / `description` (эквивалент `lead_name`) — оба варианта запроса
  - Вернуть список словарей: `id, company, city, stage, score, next_call, contact_name, manager_name` (последние два — опционально, для уточнения поиска)
  - Лимит 10, сортировка в Python по `_lead_recency_score`
- [x] **backend/agents/tools.py** — добавить `transliterate_ru_en(text: str) -> str`:
  - Карта замен: а→a, б→b, в→v, г→g, д→d, е→e, ё→yo, ж→zh, з→z, и→i, й→y, к→k, л→l, м→m, н→n, о→o, п→p, р→r, с→s, т→t, у→u, ф→f, х→kh, ц→ts, ч→ch, ш→sh, щ→shch, ъ→'', ы→y, ь→'', э→e, ю→yu, я→ya (и заглавные)
  - Пробелы и дефисы сохранять
  - Если текст уже латиница — вернуть как есть (нормализованный)
  - EN→RU через `_transliterate_en_to_ru` для обратного поиска
- [x] Сортировка результатов (в Python после выборки, или в SQL через CASE):
  1. Есть открытая задача с `due <= сегодня` / последняя коммуникация типа `call` за 24ч
  2. Стадия: Переговоры > КП отправлено > Квалифицирован > Новый
  3. Скор (desc)
  4. `updated_at` desc (свежесть)
- [x] Обновить `normalize_lead_for_agents` чтобы она корректно работала со списком (сейчас ожидает один dict)

---

## Файлы (ожидаемо)
1. `backend/agents/tools.py` — основная правка
2. `backend/db/models/lead.py` — проверить точные названия полей: `company`, `contact` (имя контакта), `description` (описание лида, эквивалент lead_name), `city`, `stage`, `score`, `next_call`, `responsible` (менеджер)

---

## Читать (только нужные §)
- `backend/agents/tools.py` — `read_lead_by_company`, `normalize_lead_for_agents`, `_api_get`, `_transliterate_ru_to_en`, `_generate_search_variants`, `_lead_recency_score`
- `backend/db/models/lead.py` — поля модели Lead (уже прочитано)
- `backend/api/routes/leads/crud.py` — `list_leads` (как делают фильтрацию)
- `backend/voice/lead_context.py` — `resolve_lead` (точка входа из voice)

---

## Не ломать
- `read_lead_by_company` используется в `voice/lead_context.py` → `resolve_lead` → `voice/pipeline.py` (hot-path voice). **Регрессия зоны `voice` обязательна.**
- Не менять сигнатуру публичных API (`/api/leads`), только внутреннюю функцию tools.
- Тесты `tests/test_voice_pipeline.py` мокают `agents.tools.read_lead_by_company` — поведение мока должно остаться совместимым (возвращать list[dict] или None).

---

## Техническая спецификация (PHASE 1 SPEC)

### 1. Публичная функция `transliterate_ru_en(text: str) -> str`
- На основе существующих `_transliterate_ru_to_en` / `_transliterate_en_to_ru`
- Карта замен: а→a, б→b, в→v, г→g, д→d, е→e, ё→yo, ж→zh, з→z, и→i, й→y, к→k, л→l, м→m, н→n, о→o, п→p, р→r, с→s, т→t, у→u, ф→f, х→kh, ц→ts, ч→ch, ш→sh, щ→shch, ъ→'', ы→y, ь→'', э→e, ю→yu, я→ya (и заглавные)
- Пробелы и дефисы сохранять
- Общие слова (банк→bank, аудит→audit, ад→ad и т.д.) из `_TRANSLIT_COMMON_WORDS`
- Если текст уже латиница — возвращать нормализованный (lowercase, пробелы)

### 2. `read_lead_by_company(query: str, limit: int = 10) -> list[dict]`
**Новая логика (SQL-first, не Python-фильтр 500):**
- Генерировать 2 варианта: `q1 = query.lower().strip()`, `q2 = transliterate_ru_en(query).lower().strip()`
- Убрать дубликаты вариантов
- SQL запрос через `_api_get` или прямую сессию (если есть доступ к БД):
  ```sql
  SELECT id, company, city, stage, score, next_call, contact, responsible, description, updated_at
  FROM leads
  WHERE (
    company ILIKE %s OR contact ILIKE %s OR description ILIKE %s
  ) AND (
    %s = '' OR company ILIKE %s OR contact ILIKE %s OR description ILIKE %s
  )
  ORDER BY 
    CASE WHEN next_call IS NOT NULL AND next_call != '—' AND next_call <= NOW() THEN 1000
         WHEN next_call IS NOT NULL AND next_call != '—' AND next_call <= NOW() + INTERVAL '24 hours' THEN 500
         ELSE 0 END DESC,
    CASE stage WHEN 'Переговоры' THEN 100 WHEN 'КП отправлено' THEN 50 WHEN 'Квалифицирован' THEN 20 WHEN 'Новый' THEN 10 ELSE 0 END DESC,
    score DESC,
    updated_at DESC
  LIMIT %s
  ```
  Параметры: `f"%{q1}%", f"%{q1}%", f"%{q1}%", q2, f"%{q2}%", f"%{q2}%", f"%{q2}%", limit`
  (если q2 == q1 — один набор параметров)

**Альтернатива (через API /api/leads):**
- Если прямой SQL недоступен — использовать `read_leads(limit=200)` + фильтр/сортировка в Python (как сейчас), но с поиском по `company` И `contact` И `description` + оба варианта транслитерации.
- **Важно:** оставить fallback на Python-фильтр, если API не поддерживает сложный поиск.

### 3. Возвращаемые поля (snake_case для агентов):
```python
{
  "id": lead["id"],
  "company": lead["company"],
  "city": lead["city"],
  "stage": lead["stage"],
  "score": lead["score"] if lead["score_manual"] is None else lead["score_manual"],
  "next_call": lead["next_call"] or "—",
  "contact_name": lead["contact"],
  "manager_name": lead["responsible"],
  "lead_id": lead["id"],  # для совместимости
}
```

### 4. `normalize_lead_for_agents(raw: dict | list) -> dict | list`
- Если вход `list[dict]` — вернуть `list[normalize_lead_for_agents(item)]`
- Если `dict` — текущая логика + добавить `contact_name`, `manager_name`

### 5. Регрессия зоны voice
```bash
cd backend
python -m pytest tests/test_voice_pipeline.py -q
python scripts/run_zone_regression.py voice
```

---

## Проверка (после GREEN)
```bash
cd backend
python -c "
import asyncio
from agents.tools import read_lead_by_company, transliterate_ru_en
async def test():
    print('translit:', transliterate_ru_en('акбарс банк ад аудит'))
    print('translit:', transliterate_ru_en('akbars bank ad audit'))
    r1 = await read_lead_by_company('акбарс банк ад аудит')
    print('RU:', [(x['id'], x['company'], x.get('contact_name')) for x in r1])
    r2 = await read_lead_by_company('akbars bank ad audit')
    print('EN:', [(x['id'], x['company'], x.get('contact_name')) for x in r2])
    r3 = await read_lead_by_company('аудит')
    print('PART:', [(x['id'], x['company']) for x in r3])
asyncio.run(test())
"
python -m pytest tests/test_voice_pipeline.py -q
python scripts/run_zone_regression.py voice
```
Ожидается: оба запроса возвращают одинаковый лид (или список с ним на первом месте), список до 10 элементов, поля `id, company, city, stage, score, next_call, contact_name, manager_name` присутствуют.

---

## Проверка (после GREEN)
```bash
cd backend
python -c "
import asyncio
from agents.tools import read_lead_by_company
async def test():
    # кириллица
    r1 = await read_lead_by_company('акбарс банк ад аудит')
    print('RU:', [(x['id'], x['company']) for x in r1])
    # латиница
    r2 = await read_lead_by_company('akbars bank ad audit')
    print('EN:', [(x['id'], x['company']) for x in r2])
    # частичное совпадение по названию лида
    r3 = await read_lead_by_company('аудит')
    print('PART:', [(x['id'], x['company']) for x in r3])
asyncio.run(test())
"
python -m pytest tests/test_voice_pipeline.py -q
python scripts/run_zone_regression.py voice
```
Ожидается: оба запроса возвращают одинаковый лид (или список с ним на первом месте), список до 10 элементов, поля `id, company, city, stage, score, next_call` присутствуют.

---

## BACKLOG / ISSUES (если появятся)
- Если транслитерация слишком «грязная» — отложить в BACKLOG, сделать упрощённую карту частых слов (банк→bank, аудит→audit, ад→ad и т.д.)
- Если поиск по `lead_name` не нужен (поле пустое у большинства) — убрать, оставить только `company` + `name`

---

## SBR Scope
**Обязателен** (1 файл backend `tools.py` + hot-path voice через `lead_context.py` + поиск — пограничный случай, но затрагивает voice-пайплайн).  
PHASE 0 INTAKE ✅ → PHASE 1 SPEC → `go` → RED → GREEN → REVIEW.