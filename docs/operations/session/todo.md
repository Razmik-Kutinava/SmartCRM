# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> ебашь

**Задача для следующего агента: F4 — «Агенты по синтезу» (зависит от «Агенты на карточке работают»)**

Собирает контекст лида (этап, задачи, паспорт, 🔍, переписка) → вызывает 5 агентов → выдаёт **единый совет: 1–3 следующих шага простым языком** + суфлёр `missing_data` на карточке + задача из `next_action`.

### Входные артефакты (уже в коде / доке)
- `backend/agents/СИНТЕЗ_АГЕНТЫ_ВОРКФЛОУ_И_ПРОМПТЫ.md` — канон воркфлоу + промпты 5 агентов
- `F4_LEADS_ACCEPTANCE.md` § «Агенты по синтезу (контекст+промпты+суфлёр)»
- `F4_LEADS_DIRECTION.md` — модель «Кто / Что делать»
- `backend/core/hermes_prompt_profiles.py` — профили промптов агентов
- `backend/agents/orchestrator.py` — точка входа для запуска агентов

### Что реализовать (SBR)

**PHASE 0 INTAKE (в `todo.md`):** дословный заказ из этого сообщения + пункт чеклиста Ф4.

**PHASE 1 SPEC:**
- Тест: `tests/agents/test_agent_synthesis.py` (новый) — проверяет: контекст собирается → 5 агентов отвечают → есть `next_action` + `missing_data` на карточке
- Файлы: `orchestrator.py`, `hermes_prompt_profiles.py`, возможно `agent_synthesis.py` (новый модуль)
- Читать: `СИНТЕЗ_АГЕНТЫ_ВОРКФЛОУ_И_ПРОМПТЫ.md` § «Синтез в код», `F4_LEADS_ACCEPTANCE.md`

**PHASE 2 BUILD (RED→GREEN):**
1. RED: тест падает (нет синтеза)
2. GREEN: код синтеза — собирает слоты (паспорт, 🔍, этап, задачи, email) → прогоняет агентов → возвращает структурированный ответ для UI

**PHASE 3 REVIEW:**
- Регрессия: `crm_leads` + `analyst` (из `smartcrm-dev-gates.mdc`)
- UI smoke: открыть карточку → плитка «Агенты» → кнопка «Синтез» → совет отображается

### Зависимость
**Требует:** «Агенты на карточке работают» — `POST /api/agents/email/run` без ошибок, аналитик с `lead_id`, дайджест переписки урезан. Без этого синтез не запустится.

### Приёмка (acceptance)
- [ ] Тест зелёный
- [ ] Регрессия `crm_leads` + `analyst` PASS
- [ ] На карточке лида в плитке «Агенты» нажал «Синтез» → получил 1–3 шага + `missing_data` блок
- [ ] `go` пользователя → `[x]` в чеклисте Ф4

### Куда писать результат
- `docs/operations/phase4/leads/F4_AGENT_SYNTHESIS.md` (создать по образу `F4_LEAD_SEARCH_FUZZY.md`)
- `SESSION_STATE.md` / `CHANGELOG.md` / `HANDOFF.md` — в том же коммите

**Старт:** `/spec` → напиши `todo.md` + SPEC → стоп до моего `go` на RED.

## Как понял

Нужно реализовать узел синтеза на карточке лида: собирать контекст (этап, задачи, паспорт, веб-исследование 🔍, переписка) через существующие слоты (`build_agent_slots`), вызывать 5 агентов (аналитик, экономист, маркетолог, тех.спец, стратег) через `POST /api/agents/email/run` или `orchestrator.run_agents`, возвращать единый ответ: 1–3 шага простым языком + блок `missing_data` для суфлёра + задачу из `next_action`. Тест в `tests/agents/test_agent_synthesis.py`, модуль `agent_synthesis.py`, правки в `orchestrator.py`/`hermes_prompt_profiles.py`, док `F4_AGENT_SYNTHESIS.md`. Зависит от готового `POST /api/agents/email/run`.

## Чеклист фазы (пункт)

`CHECKLIST_F4.md` — «Агенты по синтезу (контекст+промпты+суфлёр): 🔍/паспорт в слотах, missing_data на карточке, задача из next_action» — `[ ]` до «ок».

## Файлы (ожидаемо)

- `todo.md` — этот файл (заказ + микро-чеклист)
- `docs/operations/phase4/leads/F4_AGENT_SYNTHESIS.md` — новый док по образу `F4_LEAD_SEARCH_FUZZY.md`
- `backend/agents/agent_synthesis.py` — новый модуль синтеза
- `backend/agents/orchestrator.py` — запуск синтеза (точка входа)
- `backend/core/hermes_prompt_profiles.py` — профили промптов агентов
- `tests/agents/test_agent_synthesis.py` — новый тест
- `SESSION_STATE.md` / `CHANGELOG.md` / `HANDOFF.md` — в том же коммите

## Читать (узко)
- `backend/agents/СИНТЕЗ_АГЕНТЫ_ВОРКФЛОУ_И_ПРОМПТЫ.md` § «Синтез в код»
- `F4_LEADS_ACCEPTANCE.md`
- `backend/core/agent_email_context.py` — слоты + gaps
- `backend/core/agent_gaps.py` — суфлёр missing_data
- `backend/api/routes/agent_email.py` — `POST /api/agents/email/run`

## Не ломать
- `POST /api/agents/email/run` — горячий путь, регрессия analyst + crm_leads
- Слоты `build_agent_slots` — не менять сигнатуру без нужды

## Проверка
- `cd backend && python -m pytest tests/agents/test_agent_synthesis.py -q` — RED → GREEN
- `cd backend && python scripts/run_zone_regression.py crm_leads`
- `cd backend && python scripts/run_zone_regression.py analyst`
- `cmd /c scripts\check_step.cmd`

## Чеклист микро
- [x] PHASE 0 INTAKE: заказ дословно + пункт чеклиста Ф4 в todo.md
- [x] PHASE 1 SPEC: файлы, читать, не ломать
- [x] PHASE 2 RED: тест падает (нет синтеза) — commit `65cb401`
- [x] PHASE 2 GREEN: код синтеза + зелёный тест — `agent_synthesis.py`, endpoint `/api/agents/synthesis`, правки в `agent_email.py`
- [ ] PHASE 3 REVIEW: регрессия crm_leads + analyst, UI smoke
- [ ] `[x]` в чеклисте Ф4 — только после «ок»
