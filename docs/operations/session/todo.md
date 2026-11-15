# todo — микро-чеклист: баг голосового выбора лида по порядковому номеру

## Заказ (дословно)

> Когда пользователь говорит голосовую команду вида «открой второй лид», «открой третий», «лид № 3», система открывает не тот лид, который указан, либо открывает общий список лидов вместо карточки конкретного лида.
>
> 1. При получении команды «открой N-й лид» система должна проверять голосовую память последнего поиска и брать лид по реальному индексу из этого списка.
> 2. Если в памяти нет кандидатов (пользователь не делал поиск перед командой) — система должна дать понятную обратную связь («сначала найдите лидов»), а не открывать пустой список.
> 3. При успешном выборе по номеру должна открываться карточка конкретного лида (`/leads/{lead_id}`), а не общий список.
> 4. Индекс должен быть 1-based для пользователя («первый» = 1, «второй» = 2) и корректно маппиться на внутренний 0-based индекс списка кандидатов.

## Как понял (1–2 строки)

`fastpath_route` возвращает `open_lead` с `selected_index`, но не подставляет `lead_id` из памяти. `normalize_parsed_intent` подставляет `lead_id` из `get_last_search_candidates()` (единая память), а `voice/pipeline.py` при `selected_index` смотрел в `get_last_lead(session_id)` (per-session таблица) — разные источники памяти. Исправлено: pipeline при `selected_index` использует `get_last_search_candidates()` (единый источник), при отсутствии кандидатов — понятный ответ «сначала найдите лидов».

## Чеклист микро-шагов

- [x] **backend/voice/pipeline.py** — при `open_lead` с `selected_index`: подставляет `lead_id` из `get_last_search_candidates()` (единый источник с `slot_normalize`); без кандидатов — ответ «сначала найдите лидов»
- [x] **backend/core/hermes/slot_normalize.py** — уже подставляет `lead_id` из `get_last_search_candidates()` для `open_lead` с `selected_index` (проверено, без изменений)
- [x] **backend/tests/voice/test_voice_open_lead_by_number.py** — RED тесты (7 шт), все PASS после фикса
- [x] Регрессия зоны voice: `python -m pytest tests/voice/ -q` — 86 PASS
- [x] `test_voice_pipeline.py` — hangs на сетевых вызовах (известно, в ISSUES, не регрессия)
- [ ] `git commit` — код + ops одним коммитом

## Файлы (ожидаемо)

1. `backend/voice/pipeline.py` — обработка `open_lead` с `selected_index` (исправлено)
2. `backend/core/hermes/slot_normalize.py` — подстановка `lead_id` из памяти (без изменений, уже верно)
3. `backend/tests/voice/test_voice_open_lead_by_number.py` — новые тесты (7 PASS)

## Не ломать

- `backend/voice/pipeline.py` — hot-path voice (WS / process_text), регрессия зоны voice обязательна
- `backend/core/hermes/slot_normalize.py` — контракт интентов не менять
- `get_last_search_candidates` / `set_last_search_candidates` — сигнатуры не менять

## Проверка (после GREEN)

```bash
cd backend
python -m pytest tests/voice/test_voice_open_lead_by_number.py -q   # 7 PASS
python -m pytest tests/voice/ -q   # зона voice, 86 PASS
# tests/test_voice_pipeline.py — hangs на сетевых вызовах (окружение, не регрессия)
```

## SBR Scope

Обязателен (2+ файла backend + hot-path voice). PHASE 0 INTAKE → PHASE 1 SPEC → `go` → RED → GREEN → REVIEW.
