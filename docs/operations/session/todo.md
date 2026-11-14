# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> ебашь

**Задача для агента: F4 — «Автоскор в шапке»**

Пункт чеклиста Ф4: **Автоскор в шапке** — видимый `score`/приоритет от формулы (+ полнота), не ручное поле как источник истины.

## Входные артефакты
- `docs/operations/phase4/leads/F4_LEADS_DIRECTION.md` — § «Скор»: `scoreAdvisory` формула есть, не пишет в `score`, нужна автосинхронизация
- `backend/core/lead_score_advisory.py` — формула advisory score (этап + сумма + путь сделки − просрочки)
- `backend/db/models/lead.py` — поле `score` (int, ручное сейчас)
- `frontend/src/routes/leads/[id]/+page.svelte` — шапка карточки, показывает `score`
- `backend/api/routes/leads/crud.py` — `GET /api/leads/{id}`, `PATCH` (обновление скора)

## Что реализовать (SBR)

**PHASE 0 INTAKE (в `todo.md`):** дословный заказ из этого сообщения + пункт чеклиста Ф4.

**PHASE 1 SPEC:**
- Тест: `tests/api/test_lead_auto_score.py` (новый) — проверяет:
  - `GET /api/leads/{id}` возвращает `score` = `scoreAdvisory.suggestedScore` (если advisory есть)
  - `score` обновляется при смене этапа/пути/суммы/просрочек
  - Ручное поле `score_manual` (новое, опционально) — для переопределения
- Файлы: `lead_score_advisory.py`, `crud.py`, `lead.py` (модель), `+page.svelte` (UI)
- Читать: `F4_LEADS_DIRECTION.md` § «Скор», `F4_SCORING_TUNING.md`

**PHASE 2 BUILD (RED→GREEN):**
1. RED: тест падает (нет автоскора в ответе API)
2. GREEN:
   - Добавить в модель `score_manual` (nullable) — миграция через `init_db()`
   - В `GET /api/leads` / `{id}`: `score = score_manual if score_manual is not None else scoreAdvisory.suggestedScore`
   - В `PATCH`: если приходит `score` — пишем в `score_manual`, иначе не трогаем
   - UI: шапка показывает автоскор, иконка «ручное переопределение» если `score_manual`

**PHASE 3 REVIEW:**
- Регрессия: `crm_leads` (из `smartcrm-dev-gates.mdc`)
- UI smoke: открыть карточку → смена этапа → скор пересчитался без ручного ввода

## Зависимость
**Независимая** — можно параллелить с «Путь сделки: не 0/0» (каждая свой `go` + свой коммит).

## Приёмка
- [ ] Тест зелёный
- [ ] Регрессия `crm_leads` PASS
- [ ] Карточка: скор обновляется при смене этапа/пути/просрочки
- [ ] `go` пользователя → `[x]` в чеклисте Ф4

## Куда писать результат
- `docs/operations/phase4/leads/F4_SCORING_TUNING.md` (обновить статус)
- `SESSION_STATE.md` / `CHANGELOG.md` / `HANDOFF.md` — в том же коммите

## Чеклист фазы (пункт)
`CHECKLIST_F4.md` — «Автоскор в шапке — видимый score/приоритет от формулы (+ полнота), не ручное поле как источник истины» — `[ ]` до «ок».

## Файлы (ожидаемо)
- `todo.md` — этот файл (заказ + микро-чеклист)
- `backend/db/models/lead.py` — поле `score_manual`
- `backend/db/session.py` — миграция колонки `score_manual`
- `backend/api/routes/leads/crud.py` — PATCH `score` → `score_manual`; GET через presenter
- `backend/api/routes/leads/presenter.py` — GET `score = score_manual или scoreAdvisory.suggestedScore`
- `backend/core/lead_score_advisory.py` — без изменений (формула есть)
- `frontend/src/routes/leads/[id]/+page.svelte` — иконка «ручное переопределение» если `score_manual`
- `tests/api/test_lead_auto_score.py` — новый тест
- `docs/operations/phase4/leads/F4_SCORING_TUNING.md` — обновить статус
- `SESSION_STATE.md` / `CHANGELOG.md` / `HANDOFF.md` — в том же коммите

## Читать (узко)
- `F4_LEADS_DIRECTION.md` § «Скор»
- `F4_SCORING_TUNING.md`
- `backend/core/lead_score_advisory.py`
- `backend/db/models/lead.py`
- `backend/api/routes/leads/crud.py`
- `backend/api/routes/leads/presenter.py`

## Не ломать
- `compute_lead_score_advisory` — горячий, не менять сигнатуру
- `POST /api/agents/email/run` — не в зоне этой задачи

## Проверка
- `cd backend && python -m pytest tests/api/test_lead_auto_score.py -q` — RED → GREEN
- `cd backend && python scripts/run_zone_regression.py crm_leads`
- `cmd /c scripts\check_step.cmd`

## Чеклист микро
- [x] PHASE 0 INTAKE: заказ дословно + пункт чеклиста Ф4 в todo.md
- [x] PHASE 1 SPEC: файлы, читать, не ломать
- [x] PHASE 2 RED: тест падает (нет автоскора в ответе API) — commit `этот`
- [x] PHASE 2 GREEN: код + зелёный тест (3 passed)
- [x] PHASE 3 REVIEW: регрессия crm_leads PASS (118 passed); UI — иконка score_manual добавлена, браузер-smoke не гоняли (нет go на запуск фронта)
- [ ] `[x]` в чеклисте Ф4 — только после «ок»
