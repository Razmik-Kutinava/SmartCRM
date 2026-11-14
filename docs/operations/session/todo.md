# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> ебашь spec
> **Задача для агента: F4 — «Путь сделки: не 0/0» (мелкий фикс)**
>
> ---
>
> ### Что закрываем
> Пункт чеклиста Ф4: **Путь сделки — не показывать «всё пройдено» при пустом dealPath (0/0)**.
>
> Проблема: в UI карточки лида отображается «Все шаги пройдены» + индикатор 0/0, когда `dealPath` пустой или не пришёл с бэкенда. Это вводит в заблуждение — как будто всё закрыто, а на деле путь не задан.
>
> ---
>
> ### Входные артефакты
> - `docs/operations/phase4/leads/F4_LEADS_DIRECTION.md` — § «Путь сделки»: «Часто в UI: «Все шаги пройдены» + 0/0 → dealPath пустой/не пришёл, не «всё закрыто». Разобрать и починить»
> - `CHECKLIST_F4.md` — § Лиды: пункт «Путь сделки: не показывать «всё пройдено» при пустом dealPath (0/0)»
> - `backend/db/models/lead.py` — модель лида, поле `deal_path` / `dealPath`
> - `frontend/src/routes/leads/[id]/+page.svelte` — карточка лида, отображение пути сделки
> - `frontend/src/lib/leadsStorage.js` или аналог — где рендерится индикатор прогресса пути
>
> ### Что реализовать (SBR)
>
> **PHASE 0 INTAKE (в `todo.md`):** дословный заказ + пункт чеклиста Ф4.
>
> **PHASE 1 SPEC:**
> - Тест: `tests/api/test_lead_deal_path_empty.py` (новый) — проверяет:
>   - GET /api/leads/{id} возвращает `dealPath: null` или `[]` (не отсутствует ключ)
>   - UI не рендерит «всё пройдено» / 100% при пустом пути
> - Файлы: `crud.py` (или где возвращается лид), `+page.svelte` карточки
> - Читать: `F4_LEADS_DIRECTION.md` § «Путь сделки»
>
> **PHASE 2 BUILD (RED→GREEN):**
> 1. RED: тест падает (UI показывает «всё пройдено» при пустом dealPath)
> 2. GREEN:
>    - Бэкенд: при пустом/отсутствующем `dealPath` возвращать `null` или `[]` (не опускать поле)
>    - Фронт: условие — если `dealPath` пуст/отсутствует → не показывать «всё пройдено», показать «путь не задан» или пустой индикатор
>
> **PHASE 3 REVIEW:**
> - Регрессия: `crm_leads` (из `smartcrm-dev-gates.mdc`)
> - UI smoke: открыть карточку лида без пути сделки → не показывается «всё пройдено»
>
> ---
>
> ### Команды
> ```bash
> cd backend
> python -m pytest tests/api/test_lead_deal_path_empty.py -q   # RED → GREEN
> python scripts/run_zone_regression.py crm_leads                # регрессия лидов
> ```
>
> ---
>
> ### Зависимость
> **Независимая** — можно параллелить с «Автоскор в шапке» (каждый свой `go` + свой коммит).
>
> ---
>
> ### Приёмка
> - [ ] Тест зелёный
> - [ ] Регрессия `crm_leads` PASS
> - [ ] Карточка: при пустом dealPath не показывается «всё пройдено» / 0/0
> - [ ] `go` пользователя → `[x]` в чеклисте Ф4
>
> ---
>
> ### Куда писать
> - `SESSION_STATE.md` / `CHANGELOG.md` / `HANDOFF.md` — в том же коммите
>
> ---
>
> **Старт:** `/spec` → `todo.md` + SPEC → стоп до `go` на RED.

## Как понял

`LeadDealPathPanel` рендерит «Все шаги пройдены ✓» когда `dealPath.nextStep` = null (в т.ч. при пустых группах). Бэкенд через `presenter.py` всегда вызывает `build_deal_path(payload)` → `dealPath` с 3 группами (qualification/pre_kp/won), так что ключ есть, но UI не различает «путь задан» и «путь пуст/не пришёл». Нужно: бэкенд возвращает `dealPath: null` (или `[]`) когда путь не задан, а фронт показывает «путь не задан» вместо «всё пройдено».

## Файлы (ожидаемо)

- `backend/api/routes/leads/presenter.py` — смена `dealPath` на `null` при пустом/отсутствующем пути
- `frontend/src/lib/leads/enrichLeadForCard` / `+page.svelte` — дефолт `dealPath` и условие показа
- `frontend/src/components/LeadDealPathPanel.svelte` — условие «путь не задан»
- `backend/tests/api/test_lead_deal_path_empty.py` — новый тест

## Читать (узко)

- `F4_LEADS_DIRECTION.md` § «Путь сделки» (уже прочитан)
- `backend/core/lead_deal_path.py` — `build_deal_path`
- `backend/api/routes/leads/presenter.py` — `lead_api_payload`
- `frontend/src/components/LeadDealPathPanel.svelte` — рендер «всё пройдено»
- `frontend/src/lib/leadsStorage.js` — `enrichLeadForCard`

## Не ломать

- Существующие тесты `test_lead_deal_path.py`, `test_lead_engagement.py` (dealPath с группами)
- `lead_deal_path.build_deal_path` сигнатура

## Чеклист микро

- [x] PHASE 0 INTAKE: заказ дословно в todo.md
- [x] PHASE 1 SPEC: файлы, читать, не ломать
- [x] PHASE 2 RED: `test_lead_deal_path_empty.py` падает (нет фикса dealPath empty) — коммит `659a95f [RED]`
- [x] PHASE 2 GREEN: бэкенд presenter.py (dealPath=null при пустом) + фронт enrichLeadForCard (dealPath=null) + LeadDealPathPanel («путь не задан»), тест зелёный, регрессия crm_leads 118 PASS
- [ ] PHASE 3 REVIEW: UI smoke + check_step + `[x]` в чеклисте Ф4 после «ок» пользователя

---

**PHASE 3 REVIEW — жду `go` / `ебашь` для финиша шага**
