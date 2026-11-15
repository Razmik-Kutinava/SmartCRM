# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> «Сейчас голосом говорю найти лид — поиск почти точен. Но следующая команда "открой лид" — если быстро не скажу, агент забывает, что нашёл. Надо: чуть задержать память, чтобы "открой лид" подхватил последний найденный. Если задача в контуре лида — агент помнит и знает, что делать. Если "найди другой лид" — переключается на поиск. Память уходит очень быстро.
>
> Ещё: иногда находит несколько одинаковых лидов. Надо голосом выбирать: "первый", "второй", "лид № 3" или сказать полное название / город / ИНН / имя контакта / фамилию менеджера — поиск сужается и находит точный.
>
> Поиск работает только на кириллице — надо транслитерацию RU↔EN, чтобы "акбарс банк ад аудит" и "akbars bank ad audit" находили один лид.
>
> Сортировка: самый актуальный (свежая задача/звонок, стадия Переговоры, высокий скор) — первый в списке.»

---

## Как понял (1–2 строки)
Добавить короткую TTL-память последнего найденного лида в голосовом пайплайне + вернуть список совпадений с сортировкой по актуальности + голосовой выбор по порядковому числителю/номеру + поиск по названию лида и контакту с транслитерацией RU↔EN.

---

## Чеклист микро-шагов (todo.md)

- [x] **agent_memory.py**: таблица `voice_last_lead(session_id, lead_id, company, candidates_json, ts)` + функции `set_last_lead(session_id, lead_id, company, candidates_list)`, `get_last_lead(session_id, max_age_sec=60)`, `clear_last_lead(session_id)` — TTL 60 сек
- [x] **voice/pipeline.py**: после `resolve_lead`/`fetch_lead_history` → `set_last_lead(session_id, ...)`; при `list_leads` с query → сохраняем топ-10 кандидатов; перед `open_lead` без `lead_id` → `get_last_lead(session_id)` → подставить `lead_id` + `ref=last`; при `list_leads` с `_clear_voice_memory` → `clear_last_lead(session_id)`
- [x] **agents/tools.py**: `read_lead_by_company(query, limit=10)` → вернуть `list[dict]` (id, company, city, stage, score, next_call, contact_name, manager_name); поиск по `company` ИЛИ `contact` ИЛИ `lead_name`/`name`; транслитерация RU↔EN простая карта — оба варианта в `ILIKE`-like; сортировка: 1) открытая задача due≤сегодня / звонок 24ч (вес 1000), 2) стадия (Переговоры=100, КП=50, Квалифицирован=20, Новый=10), 3) скор (вес 1), 4) updated_at свежесть (вес 0.01)
- [x] **core/hermes/slot_normalize.py**: извлечение порядкового числительного («первый»..«пятый»), «лид № N» / «номер N» → слот `selected_index` = n-1; в `normalize_parsed_intent` — подставляет `selected_index` для `open_lead`
- [x] **core/hermes/rescue.py**: детерминированные паттерны для выбора по номеру: `re.search(r"\b(первый|второй|третий|четвёртый|пятый|лид\s*№?\s*\d)\b", t)` → intent `open_lead` со слотом `selected_index`; паттерн «найди другой лид» → `_clear_voice_memory`

---

## Файлы (ожидаемо)
1. `backend/core/agent_memory.py`
2. `backend/voice/pipeline.py`
3. `backend/agents/tools.py`
4. `backend/core/hermes/slot_normalize.py`
5. `backend/core/hermes/rescue.py`

---

## Читать (только нужные §)
- `backend/core/agent_memory.py` — вся (структура observations, TTL-паттерн)
- `backend/voice/pipeline.py` — `_run_pipeline`, `resolve_lead`, `fetch_lead_history`
- `backend/agents/tools.py` — `read_lead_by_company`, `normalize_lead_for_agents`
- `backend/core/hermes/slot_normalize.py` — `_extract_company`, `normalize_parsed_intent`
- `backend/core/hermes/rescue.py` — `rescue_route`, секции `open_lead`, `list_leads`
- `docs/operations/phase4/ZONE_NOTES.md` — раздел `## voice`
- `backend/tests/voice/test_open_lead.py` — существующие кейсы `ref: "last"`

---

## Не ломать (hot-path)
- `backend/voice/pipeline.py` — WS / process_text (регрессия зоны `voice` обязательна)
- `backend/core/hermes/parse.py` — не трогать, логика подстановки только в пайплайне
- `backend/core/hermes/rescue.py` — добавлять паттерны аккуратно, не ломать существующие

---

## Проверка (после GREEN)
```bash
cd backend
python -m pytest tests/test_voice_pipeline.py -q
python scripts/run_zone_regression.py voice
```
Ожидается: зелёные тесты + работающий сценарий:
1. «Найди акбарс банк» → список 3 лида, первый — самый актуальный
2. «Открой первый» → открывается лид №1
3. «Открой лид» (через 20 сек) → открывается тот же последний
4. «Найди другой лид» → память сбрасывается, новый поиск
5. «akbars bank ad audit» → находит тот же лид (транслитерация)

---

## BACKLOG / ISSUES (если появятся)
- Если транслитерация тяжелая — отложить в BACKLOG, сделать простую карту частых слов (решено: простая карта)
- TTL-память: scope = session_id (решено)
- Список кандидатов: в agent_memory.py таблица voice_last_lead (решено)

---

## SBR Scope
**Обязателен** (5 файлов backend + hot-path voice + пункт чеклиста фазы voice).  
PHASE 0 INTAKE ✅ (этот текст) → PHASE 1 SPEC → `go` → RED → GREEN → REVIEW.