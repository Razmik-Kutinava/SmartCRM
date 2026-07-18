# HANDOFF

`Спринт:[Наведение порядка] | Задача:[.claude → gitignore] | Статус: ✅ done | 👤 продукт / PRD_MAP`

**2026-07-18:** `.claude/` в .gitignore, untrack (файлы на диске). Коммит `3e69864`. **👤:** следующая задача — PRD_MAP или чистка доков.

---

`Спринт:[CoffeeOS workflow] | Задача:[миграция rules] | Статус: ✅ done | 👤 продукт / PRD_MAP`

**2026-07-18:** CoffeeOS workflow **закрыт** (1–6). SBR scope зафиксирован. Коммит `4a77384`. **👤:** PRD_MAP или `go` на долг из BACKLOG § post-migration.

---

`Спринт:[CoffeeOS workflow] | Задача:[шаг 5 — doc links + scratch] | Статус: ✅ done (код) | 👤 go / апрув шаг 6`

**2026-07-18:** SBR — `spec-build-review.mdc`, `todo.md`, RED/GREEN в commit-ops. Коммит `a5f72b3`. Scope: PRD_MAP + фичи; one-liner без SBR. **👤:** `go` на шаг 3 (project-rules) или правки scope SBR (BACKLOG §6).

---

`Спринт:[CoffeeOS workflow] | Задача:[шаг 1 — каркас rules] | Статус: ✅ done (код) | 👤 go на шаг 2`

**2026-07-18:** Правила Cursor реорганизованы: `.cursor/rules/workflow/` (6 файлов), `smartcrm-index.mdc`, `project/` placeholder. Коммиты `c4318aa` + `4861e9e`. **👤:** `go` на шаг 2 (SBR) или правки по BACKLOG § CoffeeOS migration.

---

`Спринт:[B24 backfill] | Задача:[фокусный backfill + task scope] | Статус: 🔄 in_progress | 👤 мониторинг`

**2026-07-01:** `spawn_bitrix_backfill_focused.py` — поля, задачи (scope task OK), продукты, import; таймлайн/watch **не** запускаются. Почта: FAQ=0, IMAP=0, uvicorn перезапущен. **👤:** `bitrix_fields_resync_state.json`, `check_lead_coverage.py`.

---

`Спринт:[B24 backfill] | Задача:[mass догрузка B24 → CRM] | Статус: 🔄 in_progress | 👤 мониторинг`

**2026-06-29:** B24 API снова OK (3649 лидов в портале). Запущены: `spawn_bitrix_backfill_all` (поля, таймлайн, задачи, продукты) + `POST /api/leads/import-bitrix` (новые лиды). Почта: `EMAIL_FAQ_AUTOREPLY=0`, `EMAIL_AUTO_SYNC_MINUTES=0` в `.env` — **перезапустить uvicorn** чтобы IMAP не крутился. Монитор: `backend/data/bitrix_fields_resync_state.json`, `check_lead_coverage.py`.

---

`Спринт:[Ф4 Email] | Задача:[backfill всей истории] | Статус: ✅ done (код) | 👤 credentials + browser`

**2026-06-27:** Фоновая догрузка почты — `backfill.py`, API `/api/email/backfill/*`, кнопка «Догрузить всю историю», скрипт `run_email_backfill.py`; батчи по 90 дней назад до 10 лет. **👤:** проверить пароль ib@ (AUTHENTICATIONFAILED); на `/email` нажать «Догрузить» или `python scripts/run_email_backfill.py`.

---

`Спринт:[Ф4 Email UI] | Задача:[тред как Яндекс] | Статус: ✅ done (код) | 👤 browser`

**2026-06-25:** Тред — одно письмо + «Письма на тему» справа; цитаты обрезаются. **👤:** открыть длинный тред (Ruslan/ADSelfService), переключить письма в сайдбаре.

---

`Спринт:[Ф4 Email UI] | Задача:[Yandex Mail /email] | Статус: ✅ done (код) | 👤 browser апрув`

**2026-06-25:** `/email` — сайдбар и фильтры как Яндекс.Почта; чеклист `F4_EMAIL_YANDEX_UI.md`. **👤:** открыть `/email`, пройти чеклист §приёмка.

---

`Спринт:[Ф4 лиды] | Задача:[кнопка «Сбросить» всегда в списке] | Статус: ✅ done | 👤 проверка`

**2026-06-27:** Кнопка «Сбросить» в `/leads/list` — всегда видна справа от поиска, не прячется при дефолтных фильтрах. **👤:** обновить страницу — кнопка рядом с полем поиска.

---

`Спринт:[Ф4 лиды] | Задача:[сохранение фильтров списка] | Статус: ✅ done | 👤 проверка`

**2026-06-27:** Фильтры `/leads/list` сохраняются в `sessionStorage` — менеджер, стадия, сортировка, поиск и др. Возврат с карточки лида не сбрасывает выбор. Кнопка «Сбросить» очищает сохранение. **👤:** выставить фильтр менеджера → открыть лид → «К списку» — фильтры на месте.

---

`Спринт:[Ф4 лиды] | Задача:[баннер «Что сделать» на карточке] | Статус: ✅ done | 👤 проверка`

**2026-06-27:** На хабе `/leads/{id}` — баннер с просрочками, документами, паспортом, подсказкой скоринга; клик → нужная плитка; `!` на плитках с проблемами. **👤:** открыть лид со скриншота — баннер над плитками.

---

`Спринт:[Ф4 лиды] | Задача:[listStageSummary — этап и даты в списке] | Статус: ✅ done | 👤 проверка`

**2026-06-27:** Колонка **Этап** в `/leads/list`: прогресс пути сделки (N/M), дни на этапе, срок дела, без касания. API `listStageSummary`. **👤:** обновить список, смотреть колонку Этап у просроченных.

---

`Спринт:[Ф4 лиды] | Задача:[суфлёр listCoach в списке] | Статус: ✅ done | 👤 проверка`

**2026-06-27:** Под каждой компанией в `/leads/list` — до 4 строк «что сделать»: просрочка/дело, дозаполнить, путь сделки, балл. API `listCoach` в `GET /api/leads`. **👤:** фильтр «Просрочено» — у каждой строки видны подсказки.

---

`Спринт:[Ф4 лиды] | Задача:[фильтр дел «На дату» в списке] | Статус: ✅ done | 👤 проверка`

**2026-06-27:** `/leads/list` — фильтр дел «На дату» + date picker; API `openTaskDueDates` на каждом лиде. **👤:** выбрать «На дату», сменить дату, убедиться что список сужается.

---

`Спринт:[Ф4 лиды] | Задача:[«Мой день» — task_intent + Ops веса] | Статус: ✅ done (код) | 👤 приёмка`

**2026-06-27:** Dropdown `task_intent` при создании задачи (`/leads/tasks`, карточка лида, панель активности); API `taskIntent` + `GET /api/tasks/intent-catalog`; веса `day_priority` в `/ops/crm`. pytest: crm_leads + tasks + day_priority. **👤:** создать задачу с типом, сохранить веса в Ops, проверить порядок в `/leads/list`.

---

`Спринт:[Ф4 лиды] | Задача:[«Мой день» — dayRank] | Статус: ✅ done (код) | 👤 приёмка`

**2026-06-27:** `lead_day_priority.py` + intents + API `dayRank`/`needsEnrich`; сортировка «Мой день» list/deals; суфлеры `wait_stale`. pytest 51 crm_leads PASS. **👤:** `/leads/list` + `/leads/deals` + фильтр менеджера.

---

`Спринт:[Ф4 лиды] | Задача:[спека «Мой день»] | Статус: ✅ done (док)`

**2026-06-27:** Согласована логика умной очереди: этап+`dealPath` первичны, тип задачи вторичен, затухание «жду ответ». Канон: `docs/operations/phase4/leads/F4_DAY_PRIORITY.md`; пункты в PRD_MAP §«Мой день». Код **не начат** — ждём `go` на шаг 1 (`lead_day_priority.py`). Backfill B24 — отдельно (🔴 портал).

---

`Спринт:[Ф4 docs] | Задача:[чеклист Email в MAP] | Статус: ✅ done`

**2026-06-25:** `F4_EMAIL_TUNING.md` + 17 пунктов в PRD_MAP §Ф4 Email; `phase4/README`. Все `[ ]` — ждём ручной обход владельца. Следующий: **go** на пункт A (ящики в UI) или обход по порядку.

---

`Спринт:[Ф4 лиды] | Задача:[обход Ф4 без голоса] | Статус: ✅ done (кроме голоса)`

**2026-06-25:** Апрув: список, карточка, воронка, `/leads/deals`, tasks/calendar/focus, analytics. Голос (554/560) — отложен до приёмки проекта. Backfill B24 — в фоне.

---

`Спринт:[Ф4 лиды] | Задача:[апрув обход карточки] | Статус: ✅ done`

**2026-06-25:** Карточка end-to-end + UX — апрув владельца. PRD_MAP 550/552/555 `[x]`; F4_LEADS_ACCEPTANCE §П.3. Дальше: воронка, задачи/календарь/фокус, аналитика.

---

`Спринт:[Ф4 лиды] | Задача:[апрув обход /leads/list] | Статус: ✅ done`

**2026-06-25:** Владелец апрувнул обход списка лидов (фильтры, KPI, 3k+, create, карточка). PRD_MAP 551/553/557 `[x]`; F4_LEADS_ACCEPTANCE §П.5. Дальше: карточка, воронка, задачи/аналитика.

---

`Спринт:[Ф4 / DevOps] | Задача:[исходящий вебхук B24 + ngrok — инструкция] | Статус: ✅ done (док)`

**2026-06-25:** Пошаговый how-to: `docs/start/BITRIX_OUTBOUND_WEBHOOK.md` (туннель :8000, URL в портале, `BITRIX_OUTBOUND_TOKEN`, чеклист). Настройка в портале — **вместе позже**, пока опрос 5 мин.

---

`Спринт:[Ф4 UI] | Задача:[убрать Аналитика из сайдбара] | Статус: ✅ done`

**2026-06-25:** Дубль «Аналитика» убран из корневого сайдбара; осталась только вкладка **Лиды → Аналитика** (`/leads/analytics`). Редирект `/analytics` → без изменений. pytest 8 PASS. Коммит: `c23b32a`.

---

`Спринт:[Ф4 лиды] | Задача:[resume mass backfill B24] | Статус: 🔄 in_progress`

**2026-06-25:** Перезапущены фоновые прогоны: поля (3228), таймлайн `--resume` с 270, дела, продукты, watch `--only-missing`. `--resume` для engagement; `spawn_bitrix_backfill_all.py`. Коммит: `042b5bd`.

---

`Спринт:[Ф4 UI] | Задача:[/leads/deals — дела как B24] | Статус: ✅ done`

**2026-06-24:** Вкладка **Дела** `/leads/deals` — список лидов с ближайшим делом, сортировка по сроку; фильтры Запланированные/Сегодня/Завтра/Просрочено/Входящие; менеджер; API `GET /api/leads/activities`; время в due из B24; «Дело завтра» в `/leads/list` и `/leads/tasks`. pytest 17+ PASS. Коммит: `29d1380`.

---

`Спринт:[Ф4 лиды] | Задача:[B24 таймлайн → Действия и история] | Статус: ✅ done (код) | 🔄 mass --timeline-only`

**2026-06-24:** Было: панель «Действия и история» пустая/бедная — mass-resync гонял только tasks, не timeline. Стало: `bitrix24_timeline_extra` (создание лида, logmessage/бизнес-процессы, имена авторов); расширен `bitrix24_timeline`; UI — единая лента комментов + встреч без дублей `[b24:act:*]`; CLI `check_bitrix_engagement_backfill.py`; `--timeline-only` + state. До backfill: 392/3228 лидов с историей, 3582 comm rows. Smoke 5 лидов +6 записей. Mass `--timeline-only` в фоне. pytest 5 PASS. Коммит: `fb20f91`.

---

`Спринт:[Ф4 UI] | Задача:[fix 404 coverage/managers] | Статус: ✅ done`

**2026-06-24:** Двойной путь `/api/leads/leads/*` в `leadsStorage.js` → 404. Исправлено на `/coverage` и `/managers`. Fallback списка менеджеров из `GET /api/leads`. Activity resync: **3228/3228**, 359 задач, 0 ошибок. Коммит: `05446af`.

---

`Спринт:[Ф4 UI] | Задача:[/leads/list фильтр менеджера] | Статус: ✅ done`

**2026-06-24:** Выпадающий фильтр «Менеджер» из БД (ответственный B24 + `bitrix_extra.manager`). API `GET /api/leads/managers`, колонка в таблице, бейдж в карточке. Дефолт через `CRM_OPERATOR_NAME` в `.env`. Коммит: `a5079a1`.

---

`Спринт:[Ф4 UI] | Задача:[/leads/list coverage-счётчики] | Статус: ✅ done`

**2026-06-24:** Сегменты полноты карточки (B24 полный/частичный/пустой, паспорт, карточка готова, пустые, проигран, без дел). API `GET /api/leads/coverage` + флаги в `GET /api/leads`. UI: кликабельные чипы на `/leads/list` с фильтрацией. CLI `check_lead_coverage.py`. Коммит: `f9123bf`.

---

`Спринт:[Ф4 UI] | Задача:[/leads/tasks фильтры] | Статус: ✅ done`

**2026-06-24:** Два ряда фильтров (статус + срок) + эскалация; API `task_status`/`due`; бейджи в таблице. Коммит: `9e1d76b`.

---

`Спринт:[Ф4 UI] | Задача:[/leads/tasks layout] | Статус: ✅ done`

**2026-06-24:** Список задач сверху + фильтры; форма создания в модалке (+ / + SLA). Коммит: `3739c5b`.

---

`Спринт:[Ф4 лиды] | Задача:[crm.activity синк встреч/дел] | Статус: 🔄 in_progress`

**2026-06-24:** Preflight без scope task — только `crm.activity` (встреча/дело/звонок). Smoke 5 лидов OK; полный `resync_bitrix_lead_tasks.py` в фоне. Коммит: `511b753`.

---

`Спринт:[Ф4 лиды] | Задача:[mass-resync до 3228 + only-missing] | Статус: 🔄 in_progress`

**2026-06-24:** 👤 **апрув шагов 5 и 7**. Resync **~1205/3228** (0 новых ошибок после 141 burst). Добавлен `--only-missing` + `watch_fields_resync_then_retry.py` (фон). После done — автодожим. Коммит: `1b81d9a`.

---

`Спринт:[Ф4 лиды] | Задача:[browser апрув + resync — шаги 5/6/7] | Статус: ✅ шаги 5/7 апрув`

---

`Спринт:[Ф4 лиды] | Задача:[webhook scope task — шаг 4 X5-gap] | Статус: blocked (портал)`

**2026-06-24:** Extended probe: crm/user **ok**, task **missing** (401); feature API ok кроме `tasks.task.list`; `requisite.list` Access denied (ИНН через UF). JSON `data/bitrix_webhook_scope_report.json`. Acceptance: `F4_X5_WEBHOOK_TASK_SCOPE_ACCEPTANCE.md`. **👤:** включить scope **task** на вебхуке → `.env` → `check_bitrix_webhook_scopes.py` → `resync_bitrix_lead_tasks.py`. Коммит: `ae3fa9c`.

---

`Спринт:[Ф4 лиды] | Задача:[сумма+валюта — шаг 3 X5-gap] | Статус: 🔄 backfill + 👤 browser`

**2026-06-24:** Код/UI ✅ (`15 780 $`, lead 5227 → `/leads/289`). БД **663/3228** deal_amount. Acceptance: `F4_X5_DEAL_AMOUNT_ACCEPTANCE.md`. Resync упал @625 (Errno 22) — `_safe_print`, `--resume`. **👤:** открыть карточку, проверить `data-testid=lead-card-deal-amount`. Коммит: `f54dd36`.

---

`Спринт:[Ф4 лиды] | Задача:[mass-resync bitrix_extra — шаг 1/6 хвост] | Статус: 🔄 in_progress`

**2026-06-24:** Mass-resync **162/3225** extra, **106** multi-contacts, **200** deal_amount. Фикс: global retry/rate-limit в `bitrix_call`, auto-sync pause на resync, метрики multi в check script. Прогон перезапущен `--resume workers 2`. Коммит: `1f103f5`.

---

`Спринт:[Ф4 лиды] | Задача:[список — подписка / тип поставки — шаг 7] | Статус: ✅ done (код)`

**2026-06-19:** `/leads/list` — фильтры «Подписка» (истекает 30 дн. / просрочена / есть дата) и «Тип поставки»; колонка-бейдж «Подписка до» + подпись типа поставки; `leadBitrixExtra.js` + `leadListFilter.js`; pytest + smoke PASS. **Следующий:** browser апрув после mass-resync шага 6. Коммит: `a228e9d`.

---

`Спринт:[Ф4 лиды] | Задача:[mass-resync полей — шаг 6] | Статус: ✅ done (код) | in_progress: полный прогон 3225`

**2026-06-19:** `resync_bitrix_lead_fields.py` + `core/bitrix_lead_fields_sync.py` — backfill `bitrix_extra`, `contacts`, `deal_amount`/`deal_currency` из Битрикс API (`crm.lead.get` + enrich); offline `--no-api` → UF из `tech_json`; pytest 6 PASS; smoke `--limit 2` OK. **Команда:** `cd backend && python -u scripts/resync_bitrix_lead_fields.py --workers 4 --batch-size 40 --delay-ms 10`. Доки `leads.md`, PRD_MAP. **Следующий:** дождаться полного прогона; scope **task** на портале; browser апрув карточки. Коммит: `8c6e5e5`.

---

`Спринт:[Ф4 лиды] | Задача:[UI карточки X5-gap — шаг 5] | Статус: ✅ done (код)`

**2026-06-19:** Шапка — `formatDealAmountLabel` → `15 780 $`, бейдж «Повторный лид» (`isRepeatLead`); панель «Карточка» — `LeadBitrixExtraPanel` (лицензия/подписка + сворачиваемые сырые UF), `LeadContactsReadonlyList`; превью хаба `licensePreviewText`; pytest mirror+smoke 21 PASS. **Хвосты прогона 1–5:** mass backfill bitrix_extra/deal_amount/contacts (~3225), scope **task** на портале B24, 👤 апрув UI в браузере — см. `BACKLOG.md` § X5-gap. **Следующий шаг:** оператор — scope task + mass resync; затем обход карточки end-to-end. Коммит: `cd62bbf`.

---

`Спринт:[Ф4 лиды] | Задача:[webhook scope task + tasks.task.list] | Статус: ✅ done (код) | blocked: scope на портале`

**2026-06-19:** Probe `crm/user/task` (`check_bitrix_webhook_scopes.py`); понятный 401 для `tasks.task.list`; кэш denied + preflight resync; `resync_bitrix_lead_tasks.py`; pytest 10 PASS. **На портале:** включить scope **task** на входящем вебхуке, обновить URL в `.env`, затем `python scripts/resync_bitrix_lead_tasks.py --workers 4`. Live probe: crm/user ok, **task missing**. Коммит: `59490d3`.

---

`Спринт:[Ф4 лиды] | Задача:[сумма + валюта OPPORTUNITY] | Статус: ✅ done`

**2026-06-19:** `deal_amount`/`deal_currency` из Битрикс OPPORTUNITY+CURRENCY_ID; API `amount`+`currency`; `amount_rub` только RUB; шапка и панель карточки; pytest 35+ PASS. **Следующий шаг 4:** по плану X5-gap (бейдж «Повторный лид» / UI bitrixExtra). Коммит: `85f88ef`.

---

`Спринт:[Ф4 лиды] | Задача:[мультиконтакты Битрикс] | Статус: ✅ done`

**2026-06-19:** `crm.lead.contact.items.get` → все контакты в `lead.contacts[]` (телефоны/email); primary → ЛПР + плоские поля; `merge_bitrix_contacts` — ручные CRM не затираются при upsert; pytest 10 PASS (5 контактов X5-like). Коммит: `2497736`.

---

`Спринт:[Ф4 лиды] | Задача:[UF Битрикс → bitrix_extra] | Статус: ✅ done`

**2026-06-19:** Маппинг UF лицензии/подписки/поставки → колонка `bitrix_extra` (JSONB); `core/lead_bitrix_extra.py`, `extract_bitrix_extra_from_row`, enrich+merge в upsert; API `bitrixExtra`; offline из `tech_json.bitrix24.uf`; pytest 14 PASS (X5-like). Коммит: `503914d`.

---

`Спринт:[Ф4 лиды] | Задача:[Битрикс история + задачи/встречи] | Статус: ✅ done`

**2026-06-22:** `bitrix24_tasks.py` — встречи/дела (`crm.activity`, `tasks.task`) → `tasks`; `resync_bitrix_lead_engagement.py` (история + задачи, `--timeline-only`/`--tasks-only`); upsert+poll синкают оба слоя; pytest 30+ PASS; доки `docs/modules/leads.md`, PRD_MAP. Массовый прогон: `python -u scripts/resync_bitrix_lead_engagement.py --workers 4 --batch-size 40`. Коммит: `c9e0cb8`.

---

`Спринт:[Ф4 лиды] | Задача:[массовый resync продуктов Битрикс API] | Статус: 🔄 in_progress`

**2026-06-22:** Расширен `bitrix24_products` — `crm.lead.get`, productrows, сделки, **КП** (`crm.quote.*`), `crm.product.get`, OPPORTUNITY; `resync_bitrix_lead_products.py` — `.env`, `--workers`, батчи; smoke 5/5; **полный resync ~3225 лидов в фоне** (`--workers 6`); на момент коммита ~140+ лидов с `lead_products`. Команда: `cd backend && python -u scripts/resync_bitrix_lead_products.py --workers 6 --delay-ms 8 --batch-size 80`. Коммит: `164be96`.

---

`Спринт:[Ф4 лиды] | Задача:[продукты Битрикс + плитка карточки] | Статус: ✅ done`

**2026-06-22:** `lead_products` (цена, статус sold/pipeline/owned) из Битрикс UF/productrows/сделок; плитка «Продукты» в хабе + `LeadProductsPanel`; скрипт `resync_bitrix_lead_products.py`; backfill offline 0 (нет UF в tech_json); DevTools плитка OK; pytest 23 PASS. На проде: webhook → re-import или `resync_bitrix_lead_products.py`. Коммит: `bffbf62`.

---

`Спринт:[Ф4 лиды] | Задача:[отрасли из ОКВЭД — industry_bucket] | Статус: ✅ done`

**2026-06-22:** Маппинг `okved_industry_map` (секция ОКВЭД → отрасль CRM); колонка `industry_bucket` + auto-sync; backfill 3230/158; фильтр «Отрасль» + группировка на `/leads/list`; DevTools OK (селект + group industry_bucket). Коммит: `0a58b61`. Следующий: апрув группировки по отрасли на полной базе.

---

`Спринт:[Ф4 лиды] | Задача:[дела в списке /leads/list] | Статус: ✅ done`

**2026-06-22:** Видимость задач в списке — `lead_task_list_flags` (API), сортировка «Дела срочные» по умолчанию, фильтры today/overdue/open, KPI + бейдж в строке, `/leads/tasks?filter=today`; фикс даты при создании задачи в карточке; pytest crm_leads 30 + smoke 11 PASS. Коммит: `cb3c63b`, ops `eff4cf4`. Следующий: апрув в браузере на реальных лидах с задачами.

---

`Спринт:[Ф4 лиды] | Задача:[Битрикс ОКВЭД UF + resync] | Статус: ✅ done`

**2026-06-22:** Маппинг ОКВЭД/сотрудников из UF Битрикс (`bitrix24_uf`); `resync_bitrix_lead_profiles.py` (import+backfill); `lead_profile` читает okved с лида без checko_json; pytest 12 PASS. Import на машине без `BITRIX24_WEBHOOK_URL` — skip, backfill 0. На проде: задать webhook → `python scripts/resync_bitrix_lead_profiles.py`. Коммит: `464fe88`. Следующий: re-import с webhook.

---

`Спринт:[Ф4 лиды] | Задача:[группировка + backfill портрета] | Статус: ✅ done`

**2026-06-22:** Группировка `/leads/list` (ОКВЭД/размер/этап, сворачиваемые заголовки); backfill `3230` лидов / `386` обновлено; DevTools: фильтры размер/ОКВЭД + group-by OK; pytest 13 PASS. Коммит: `d3be5c9`, ops `f747d3e`. Следующий: обход 3000+ производительность; enrich для ОКВЭД у остальных лидов.

---

`Спринт:[Ф4 лиды] | Задача:[сегментация ОКВЭД + portrait] | Статус: ✅ done`

**2026-06-22:** Нормализация ОКВЭД (`okved_main`/`okved_section`), `employees_band`, `portrait_score` в БД + sync (CRUD, enrich, CSV, B24); фильтры «Размер» и «ОКВЭД сек.» на `/leads/list`; backfill-скрипт; pytest 28+ PASS. Коммит: `28517cd` (feat), ops `36a5471`. После рестарта API: `python scripts/backfill_lead_profile.py`. Следующий: апрув фильтров в браузере; при 3000+ — обход производительности.

---

`Спринт:[Ф4 лиды] | Задача:[шапка /leads/list] | Статус: ✅ done`

**2026-06-19:** Список лидов — единая шапка: «+ Новый лид» + меню ⋯ (импорт B24/Amo/HS/CSV, экспорт, стата B24); KPI (горячие, предупрежд., ср. балл); фильтры с подписями + «Сбросить»; pytest 9 PASS. Коммит: `20edfdb`. Следующий: апрув в браузере.

---

`Спринт:[Ф4 лиды] | Задача:[единая шапка карточки] | Статус: ✅ done`

**2026-06-19:** Убран дубль: одна шапка `← Лиды` + название + мета (контакт, скор, стадия, ИНН) + toolbar; summary-карточка в хабе удалена — плитки сразу ниже. PRD_MAP UX обновлён. pytest smoke 10 PASS. Коммит: `ad1d453`. Следующий: апрув в браузере.

---

`Спринт:[Ф4 лиды] | Задача:[хаб карточки + slide-over] | Статус: ✅ done`

**2026-06-19:** Карточка лида — без вкладок: компактная шапка + 7 плиток (превью: стадия 3/12, ИНН, просрочки…); по клику — большая панель справа ~65% (`LeadSlideOver`); deep link `?panel=passport`; pytest smoke 9 PASS. Коммит: `2f6b55c`. Следующий: апрув в браузере на десктопе и мобилке.

---

`Спринт:[Ф4 интеграции] | Задача:[Битрикс полный маппинг + таймлайн] | Статус: ✅ done`

**2026-06-22:** Битрикс → SmartCRM для всех лидов: ИНН/ОГРН из реквизитов, company/contact, домен/продукты UF, контакты ЛПР; таймлайн (комменты/активности) → «Действия и история»; poll: DATE_MODIFY 30д + local batch 25; pytest 19 PASS. Коммит: `765c88b`. Следующий: re-import или дождаться batch/webhook; ✨ обогатить для паспорта после появления ИНН.

---

`Спринт:[Ф4 лиды] | Задача:[enrich → полный паспорт] | Статус: ✅ done`

**2026-06-22:** ✨ Обогатить по ИНН заполняет `checko_json` (связи, финансы, арбитраж, госзакупки, tech…) + PATCH `inn`/`ogrn`/`financialsJson`/`techJson`; фильтр ложных телефонов; pytest 14+ PASS. Коммит: `5c17439`. Следующий: апрув Hochland в браузере; вакансии/налоги/история — когда появятся эндпоинты Checko.

---

`Спринт:[Ф4 лиды] | Задача:[задачи в действиях] | Статус: ✅ done`

**2026-06-21:** В «Действия» — чекбокс «Поставить задачу в календарь», дата срока, список задач лида сверху (сегодня/просрочка, «Ещё N»); pytest 11 PASS. Коммит: `89b22d6`.

---

**2026-06-21:** Обзор — шапка + 3 блока в ряд: стадии/доки (indigo) | карточка клиента (emerald) | действия (violet); pytest 9 PASS. Коммит: `5bcdbb8`. Ждём апрув в браузере.

---

**2026-06-21:** Вкладка **Checko** → **Паспорт** (после Обзора): 20 разделов из `checko_json` + связи с ИНН/ОГРН; пустые секции с подсказкой ✨; pytest 9 PASS. Коммит: `7e58d47`. Следующий шаг: enrich сохраняет полный паспорт.

---

**2026-06-21:** Касания+комменты+лента → `LeadActivityPanel`: тип (звонок/письмо/ВКС/встреча/коммент/заметка), дата авто или вручную, лента в accordion; техаудит свёрнут; pytest 20 PASS. Коммит: `08e748d`.

---

`Спринт:[Ф4 лиды] | Задача:[спрятать scoreAdvisory с обзора] | Статус: ✅ done`

**2026-06-21:** Подсказка скоринга убрана с левой колонки обзора; свёрнутый блок под «Системные поля» справа (`LeadScoreAdvisoryPanel`); pytest 6 PASS. Коммит: `3fa4302`. Как открыть: Обзор → правая колонка → Системные поля → «Подсказка скоринга (система)».

---

`Спринт:[Ф4 лиды] | Задача:[компактный путь сделки] | Статус: ✅ done`

**2026-06-21:** «Путь сделки» — чипы прогресса + «Следующий шаг» + accordion «Все документы»; ЛПР убран из дубля «До КП»; `dealPath.nextStep` в API; pytest 28 PASS. Коммит: `bae1dbf`. Ждём апрув в браузере.

---

`Спринт:[Ф4 лиды] | Задача:[блок контактов + авто ЛПР] | Статус: ✅ done`

**2026-06-19:** Справа в карточке — блок «Контакты» (мульти, роли, тел/email/мессенджеры); `contacts` JSON в БД; ЛПР с именем+должностью+каналом → шаг «ЛПР установлен» зелёный (derived); pytest 16+ PASS. Коммит: `4de81c1`. Ждём апрув в браузере.

---

`Спринт:[Ф4 лиды] | Задача:[split колонок обзора] | Статус: ✅ done`

**2026-06-19:** Обзор: слева шапка/этап/путь/активность; справа только форма редактирования+₽+системные; убран ошибочный swap; pytest 6 PASS. Коммит: `89e2a97`. Ждём апрув в браузере → go дальше.

---

`Спринт:[Ф4 лиды] | Задача:[swap колонок обзора] | Статус: ⚠️ откат логики`

`Спринт:[Ф4 лиды] | Задача:[путь сделки + stageHints] | Статус: ✅ done`

**2026-06-19:** API `dealPath` + `stageHints`; UI «Путь сделки» + «Что сделать» под этапами; цепочка доков (ЛПР→…→КП→счёт/договор/преза); лимиты 3/8/5 дн; старый чеклист апрувов убран. pytest 14 PASS. Коммит: `f4053ce`. **Ждём апрув** в браузере → go на гейты этапа.

---

`Спринт:[Ф4 лиды] | Задача:[этапы под шапкой] | Статус: ✅ done`

**2026-06-19:** Этапы перенесены под название компании; цветные pill-кнопки (`stageBadgeClass`); дубль бейджа убран; pytest 6 PASS. Коммиты: `0795b14`, `3b5d5fa`. Следующий: **апрув** обход карточки → ждём go что дальше.

---

`Спринт:[Ф4 лиды] | Задача:[UX обзор — 2 колонки] | Статус: ✅ done`

**2026-06-19:** Вкладка «Обзор» — grid 2 колонки на всю ширину (left: карточка/этап; right: касания/комменты/лента); убран max-w-5xl mx-auto; pytest 4 PASS. Коммит: `bd4b1e1`. Следующий: апрув обход в браузере.

---

`Спринт:[Ф4 лиды] | Задача:[UX — иконки шапка + сайдбар] | Статус: ✅ done`

**2026-06-19:** Тулбар карточки — иконки + title, одна строка; глобальный сайдбар сворачивается (w-14), на `/leads/{id}` скрыт + ☰; `appSidebar.js`; pytest 8 PASS. Коммиты: `20d9490`, `e09d367`. Следующий: апрув обход карточки в браузере.

---

`Спринт:[Ф4 лиды] | Задача:[фикс 500 карточки] | Статус: ✅ done`

**2026-06-19:** `/leads/{id}` — 500 из-за лишнего `</div>` во вкладке «Обзор» (Svelte `element_invalid_closing_tag`); убран; smoke 3 PASS. Коммиты: `463ba98`, `abb2282`. Следующий: перезагрузить карточку в браузере → апрув обход.

---

`Спринт:[Ф4 лиды] | Задача:[UX карточка — обзор на всю ширину] | Статус: ✅ done`

**2026-06-19:** Карточка `/leads/{id}` — убран левый сайдбар w-80; вкладки на всю ширину; «Обзор» = балл, поля, апрувы, этап, касания, комменты, история + лента. pytest smoke 3 PASS. Коммит: `22347dd`. Следующий: апрув обход карточки.

---

`Спринт:[Ф4 лиды] | Задача:[критичные пункты в MAP] | Статус: ✅ done`

**2026-06-19:** В MAP §Лиды + `F4_LEADS_ACCEPTANCE` — 4 критичных: карточка, UX фильтров, 3000+ perf, голос update/этап. Коммит: `dc4f08a`. Следующий: обход по критичным.

---

`Спринт:[Ф4 интеграции CRM] | Задача:[отдельный блок MAP + acceptance] | Статус: ✅ done`

**2026-06-19:** Блок «Интеграции CRM» в MAP (после Дашборд, перед Лиды); `F4_CRM_INTEGRATIONS_ACCEPTANCE.md` — MVP OAuth топ-3, security, импорт, маппинг; §П.0 вынесен из leads. Код шаг 1 `/ops/integrations` — **создаём**. Коммит: `16328d9`. Следующий: **go** на код `/ops/integrations`.

---

`Спринт:[Ф4 лиды] | Задача:[§П.0 интеграции CRM — план] | Статус: ✅ done`

**2026-06-19:** В начало Ф4 лидов — §П.0 поэтапные интеграции с внешними CRM (REST, webhooks, CSV, адаптеры); MAP первым пунктом. Коммит: `8029025`. Следующий: **go** на шаг 1 (`/ops/integrations`) или обход п.3 карточка.

---

`Спринт:[Ф4 лиды] | Задача:[чеклист обхода п.3–9] | Статус: ✅ done`

**2026-06-19:** Записан полный план Ф4 лидов: приоритеты (сейчас / ближайшее / когда-нибудь), п.3–9 в `F4_LEADS_ACCEPTANCE.md`, MAP §Лиды. Только доки. Коммит: `c0e68d9`. Следующий: **обход п.3** (карточка) по владельцу.

---

`Спринт:[Ф4 лиды] | Задача:[апрув удаление] | Статус: ✅ done`

**2026-06-19:** Ручной тест list + карточка OK; MAP `[x]` удаление лида. Коммит: `263a111`. Следующий: обход лидов дальше по владельцу.

---

`Спринт:[Ф4 лиды] | Задача:[удаление list + карточка] | Статус: ✅ done`

**2026-06-19:** DELETE через `apiDelete`; кнопки list/карточка + confirm; backend purge nurture/email; `F4_LEADS_ACCEPTANCE.md`, MAP §Лиды после Дашборд; pytest **20 PASS**. Коммит: `16ac2da`.

---

`Спринт:[Ф4 дашборд] | Задача:[модалка «Новый лид» — дашборд + list] | Статус: ✅ done`

**2026-06-19:** `LeadCreateModal` + host в layout; дашборд «Быстрые действия» и `/leads/list` → модалка, POST в БД; `F4_DASHBOARD_ACCEPTANCE.md`, MAP §Дашборд; pytest **19 PASS** (5 UI + 14 API). Коммит: `f5e4274`. Следующий: **«ок»** → `[x]` MAP дашборд п.1 · обход дашборда дальше.

---

`Спринт:[Ф4 баллы] | Задача:[хвост C industryOptions — регресс + smoke] | Статус: ✅ done`

**2026-06-17:** `test_lead_card_page.py`, smoke `/leads/{id}`; DevTools `/leads/3191` — карточка и breakdown OK, без `industryOptions` в консоли. Коммит: `31242ec`. Следующий: **go** Ф4 D–F или Ф4-A.

---

`Спринт:[Ф4 баллы] | Задача:[сортировка + DevTools smoke] | Статус: ✅ done`

**2026-06-17:** Сортировка «Предупреждения ↓» / «Расхождение ↓»; `scoreDelta` в API; `smoke_scoring_f4_ui.py`; DevTools: list фильтры, /ops/crm веса, карточка breakdown (лид 3191); фикс `industryOptions` на карточке. Коммит: `0d66a41`. Следующий: **go** Ф4 D–F (прогноз, пороги, Ops badge) или Ф4-A интеграции.

---

`Спринт:[Ф4 баллы] | Задача:[A–C Ops UI + breakdown + list filters] | Статус: ✅ done`

**2026-06-17:** `/ops/crm` — редактор `scoring_advisory`; карточка — раскрываемый breakdown; `/leads/list` — флаги API + фильтры warnings/divergent; pytest **17 PASS**. Коммит: `618bffe`. Следующий: **«ок»** → `[x]` MAP Ф4 баллы A–C или go D–F.

---

`Спринт:[Ф4 docs] | Задача:[план тюнинга баллов F4_SCORING_TUNING] | Статус: ✅ done`

**2026-06-19:** `F4_SCORING_TUNING.md`, секция «Баллы (тюнинг Ф4)» в PRD_MAP; F4_PLATFORM_TUNING §D обновлён (P3 [x]). Коммит: `11abbf1`. Следующий: **go** Ф4-A интеграции или go Ф4 баллы-A (UI весов Ops).

---

`Спринт:[Ф3 P3] | Задача:[smoke экспорт баллов DevTools] | Статус: ✅ done`

**2026-06-19:** DevTools `/leads/analytics` → Excel → «Баллы» → HTTP 200; `smoke_scoring_export.py` pytest 13 + live xlsx 245KB. Коммит: `f6459af`. Следующий: **Ф4** экран интеграций.

---

`Спринт:[Ф3 P3] | Задача:[SLA [x] + экспорт баллов] | Статус: ✅ done`

**2026-06-17:** MAP `[x]` SLA + экспорт баллов/воронки; `GET /api/leads/scoring/export` (csv/xlsx/pdf), кнопка «Баллы» на `/leads/analytics`; pytest **19 PASS** (scoring export suite). Коммит: `39f452e`. Следующий: **Ф4** экран интеграций или живой smoke.

---

`Спринт:[Ф3 P3] | Задача:[SLA-протоколы шаги 1–5] | Статус: ✅ done`

---

`Спринт:[Ф4] | Задача:[Платформа — план тюнинга в docs] | Статус: ✅ done`

**2026-06-17:** `F4_PLATFORM_TUNING.md`, секция «Платформа» в PRD_MAP Ф4; что не сделали в Ф3 + чеклист A–E. Коммит: `9797d84`. Следующий: **go** Ф4-A экран интеграций.

---

`Спринт:[Ф3] | Задача:[Платформа — CRM sync Amo/HubSpot + Telegram хвост] | Статус: ✅ done`

**2026-06-17:** AmoCRM + HubSpot import/push, Telegram inline approve/reject, Ops critical notify; PRD_MAP CRM `[x]`; pytest **22+ PASS**. Коммит: `c2949ce`. Следующий: баллы P3 (SLA) или Ф4.

---

`Спринт:[Ф3] | Задача:[Платформа — MAP [x] + Битрикс push] | Статус: ✅ done`

**2026-06-17:** PRD_MAP `[x]` lead hunt + Telegram; `push-bitrix`, `lead_to_bitrix_fields`, кнопка на карточке; pytest **5 PASS**. Коммит: _pending_. Следующий: **AmoCRM** import/export.

---

`Спринт:[Ф3] | Задача:[Платформа — Telegram-бот MVP] | Статус: ✅ done`

**2026-06-17:** `integrations/telegram/` — poll loop, уведомления lead hunt, команды `/start` `/status` `/queue`; pytest **5 PASS** (telegram). Коммит: `01ae21b`. Следующий: **«ок»** → `[x]` PRD_MAP Telegram · Ops critical wiring → BACKLOG.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt шаги 6–7 UI+закрытие] | Статус: ✅ done (MAP ждёт «ок»)`

**2026-06-19:** `LeadHuntOperatorPanel`, `/leadgen` → «Авто-охота», `approve-above ≥70`, DevTools smoke OK; pytest **35 PASS**. Коммит: `7045476`. Следующий: **«ок»** → `[x]` в PRD_MAP автопоиск.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt шаг 5 фон+уведомления] | Статус: ✅ done`

**2026-06-19:** trace + agent_run_log, баннер/badge Ops, loop в main.py; pytest **33 PASS**. Коммит: `a6e670f` (ops `d706ca5`). Следующий: **«ок» MAP автопоиск**.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt шаг 4 очередь+апрув] | Статус: ✅ done`

**2026-06-19:** `lead_hunt_queue.py`, `GET/POST .../queue`, approve → CRM + nurture опц., UI «Найдено агентами» на `/ops/queue` и `/leadgen`; pytest **27 PASS**. Коммит: `4d1cf33` (ops `222a288`). Следующий: **«ок» MAP автопоиск**.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt цикл поиска агентами] | Статус: ✅ done`

**2026-06-19:** `lead_hunt_search_cycle.py` — portrait+prospect → pipeline light → fanout analyst/marketer/economist, dedup БД; pytest **19 PASS** (incl. integration). Коммит: `c22ade8`. Следующий: **«ок» MAP автопоиск**.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt шаги 3–6] | Статус: ✅ done`

**2026-06-19:** поиск `search_by_portrait`, очередь approve/reject → CRM, уведомления, UI `/ops/lead-hunt`; pytest **15 PASS**; DevTools: страница + nav OK. Коммит: `85acdee`. Следующий: **«ок» MAP автопоиск** · Битрикс push / другой блок.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt шаг 2 ICP] | Статус: ✅ done`

**2026-06-18:** `lead_hunt_icp.py`, funnelBySource + Стратег, версии ICP, `GET/POST .../icp`; pytest **13 PASS**. Коммит: `080a2cf`. Следующий: **шаг 3 поиск кандидатов**.

---

`Спринт:[Ф3] | Задача:[Платформа — lead hunt шаг 1] | Статус: ✅ done`

**2026-06-18:** `lead_hunt_config/background`, API `/api/ops/lead-hunt/*`, poll в `main.py`; ICP-превью из won; pytest **9 PASS**. Коммит: `d24fcba`. Следующий: **шаг 2 ICP + шаг 3 поиск**.

---

`Спринт:[Ф3] | Задача:[Платформа — CSV импорт/экспорт лидов] | Статус: ✅ done`

**2026-06-17:** `crm_sync/csv_adapter`, `POST /import-csv`, `GET /export?format=csv`, UI `/leads/list`; pytest **8 PASS**. Коммит: `0c49729`. Следующий шаг MAP: **Битрикс push (шаг 2)**.

---

`Спринт:[Ф3] | Задача:[Платформа — экспорт Excel/PDF] | Статус: ✅ done`

**2026-06-17:** `export_reports.py` (openpyxl + fpdf2); API analytics `format=csv|xlsx|pdf`, `GET /api/leads/{id}/export`, `GET /api/tenders/saved/export`; UI analytics/карточка/тендеры; pytest **16 PASS**; Telegram → BACKLOG. Коммит: `2bf1adf`.

**Следующий шаг:** «ок» MAP экспорт · Платформа (импорт CRM) / Ф4 по go.

---

`Спринт:[Ф4 docs] | Задача:[Аналитика v2 — план тюнинга] | Статус: ✅ done`

**2026-06-17:** `F4_ANALYTICS_V2_TUNING.md` + пункты в PRD_MAP §Ф4 (прогноз на лиде, калибровка, агенты, квартал).

**Следующий шаг:** реализация Ф4 analytics по go · или **Платформа** / другой блок MAP.

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — прогноз закрытия] | Статус: ✅ done`

**2026-06-17:** `lead_close_forecast`, `closureForecast` в analytics, UI таблица; **Аналитика v2 закрыта 4/4**; pytest **19 PASS**.

**Следующий шаг:** «ок» MAP аналитика · Платформа / Ф4 по go.

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — воронка по источнику] | Статус: ✅ done`

**2026-06-17:** `funnelBySource`, UI чипы на `/leads/analytics`, CSV; pytest **17 PASS**.

**Следующий шаг:** «ок» MAP п.3 · п.4 прогноз закрытия (Экономист).

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — агенты по трейсам] | Статус: ✅ done`

**2026-06-17:** `agent_trace_analytics`, `GET /api/ops/analytics/agents`, UI `/ops/stats`, ссылки улучшения; pytest **5 PASS**.

**Следующий шаг:** «ок» MAP п.2 · п.3 воронка по источнику.

---

`Спринт:[Ф3] | Задача:[Аналитика v2 — когорты] | Статус: ✅ done`

**2026-06-17:** `compute_cohorts`, API `cohorts`, UI `/leads/analytics`, pytest **15 PASS** зона.

**Следующий шаг:** «ок» MAP когорты · п.2 эффективность агентов по трейсам.

---

`Спринт:[Ф4 docs] | Задача:[Тех. спец тендеры — план тюнинга] | Статус: ✅ done`

**2026-06-17:** `F4_TECH_TENDER_TUNING.md` + пункты в PRD_MAP §Ф4 (автопайплайн, доки, матрица ТЗ, CRM, eval).

**Следующий шаг:** реализация Ф4 по go · или **Аналитика v2** / другой блок MAP.

---

**2026-06-17:** MAP п.3 sources `[x]` апрув; п.4 вердикт участия — `tender_participation`, API `participation`, UI вкладка «Вердикт», snapshot; pytest **29 PASS** зона.

**Следующий шаг:** «ок» MAP п.4 · Аналитика v2 / Контур Ф4 — только по go.

---

`Спринт:[Ф3] | Задача:[Тендеры: sources + MAP] | Статус: ✅ done`

**2026-06-17:** MAP п.2 `[x]`; Контур → Ф4 `F4_KONTUR_GATE`; п.3 `tender_sources` + Gosplan prod + фильтры + DataNewton UI; pytest зона тендеров.

**Следующий шаг:** «ок» MAP п.3 sources · **не трогать** п.4 участвовать/нет до go.

---

`Спринт:[Ф3] | Задача:[MAP мониторинг + уведомления/календарь] | Статус: ✅ done`

**2026-06-17:** MAP п.1 мониторинг `[x]`; п.2 — уведомления + календарь (`/tenders/notifications`, `/tenders/calendar`); pytest **16 PASS**.

**Следующий шаг:** «ок» MAP п.2 · Контур API / решение участвовать.

---

`Спринт:[Ф3] | Задача:[pytest.ini filterwarnings] | Статус: ✅ done`

**2026-06-17:** убран битый `StarletteDeprecationWarning` из `pytest.ini` (Starlette 0.46+); `tests/test_pytest_config.py` — 2 PASS; обычный `pytest` без `-c NUL`.

**Следующий шаг:** «ок» MAP мониторинг тендеров п.1 · п.2 календарь.

---

`Спринт:[Ф3] | Задача:[Тех. спец — мониторинг тендеров п.1] | Статус: ✅ done`

**2026-06-17:** переименование «тендерный агент» → **Тех. спец — тендеры**; мониторинг 24/7 — config, фон, API, UI `/ops/tender-monitor`; pytest **9 PASS**.

**Следующий шаг:** «ок» MAP п.1 · п.2 уведомления/календарь дедлайнов.

---

`Спринт:[Ф3] | Задача:[Суфлёр MAP + Ф4 рекомендации] | Статус: ✅ done`

**2026-06-17:** апрув суфлёр → `[x]` MAP; `F4_STRATEGIST_SUGGESTER_TUNING.md` (8 пунктов).

**Следующий шаг:** Ф3 **Тендерный агент** (строка 479 MAP) или Ф4 тюнинг.

---

`Спринт:[Ф3] | Задача:[Авто-суфлёр Стратега] | Статус: ✅ done`

**2026-06-17:** `strategist_suggester.py` + API suggest/apply + UI `/ops/agents`; pytest **8 PASS**. MAP A/B `[x]`.

**Следующий шаг:** «ок» MAP суфлёр · дальше по Ф3/Ф4.

---

`Спринт:[Ф3] | Задача:[A/B промптов — MAP апрув] | Статус: ✅ done`

**2026-06-17:** `[x]` MAP строка 476.

---

`Спринт:[Ф3] | Задача:[A/B промптов по трейсам] | Статус: ✅ done`

**2026-06-17:** `prompt_ab_traces.py` + API `ab-traces` + UI improve; pytest **5 PASS**. MAP crawl `[x]`.

**Следующий шаг:** «ок» MAP A/B · авто-суфлёр Стратега.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — MAP закрыт] | Статус: ✅ done`

**2026-06-17:** краулинг `[x]` MAP; тюнинг → Ф4.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 4 Playwright SPA] | Статус: ✅ done`

**2026-06-17:** `vendor_crawl_playwright.py`; `use_playwright` (PT on); fallback fetch; UI; pytest **29 PASS**. Live discover на PT seed — 0 новых PDF (уже через search); инфра готова.

**Следующий шаг:** «ок» MAP crawl → A/B промптов.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 3 live PDF+RAG] | Статус: ✅ done`

**2026-06-17:** live ME+PT — **10 PDF → RAG**, **871 чанк**; фикс `_fetch_bytes`; RAG tech_specialist видит PDF. Tavily 432 (Brave/Serper OK).

**Следующий шаг:** «ок» MAP crawl **или** шаг 4 Playwright.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 2 фильтр качества] | Статус: ✅ done`

**2026-06-17:** `vendor_crawl_quality.py`; pytest 23 PASS.

---

`Спринт:[Ф3] | Задача:[Vendor crawl — шаг 1 PDF автопоиск] | Статус: ✅ done`

**2026-06-17:** `site:домен filetype:pdf`; `max_pdf_pages`; ingest `%PDF`; pytest 18 PASS.

---

`Спринт:[Ф3] | Задача:[Vendor crawl v2] | Статус: ✅ done`

**2026-06-17:** doc_urls в конфиге/UI; фильтр мусора; приоритет ссылок; PDF ingest; sitemap; live **80/80 стр, 582 чанка** (было 51). pytest **13 PASS**. `[x]` MAP crawl — после «ок».

**Дальше по списку Ф3 Self-improvement:**
1. `[x]` MAP crawl — ваше «ок»
2. A/B промптов по трейсам
3. Авто-суфлёр Стратега
4. (опц.) Playwright для SPA; голосом добавлять doc_urls

---

`Спринт:[Ф3] | Задача:[Vendor crawl live + gate close] | Статус: ✅ done`

**2026-06-17:**
- **Quality gate tuning** — `[x]` MAP: A+B+C + апрув «ок»; Economist 93.3%, остальные 100%. Таблица: `AGENTS_QUALITY_GATE_ACCEPTANCE.md`.
- **Vendor crawl live:** ManageEngine (33 чанка) + PT Security (18) → **51** в RAG `tech_specialist`. Конфиг в `vendor_crawl_config.json`. `[x]` MAP crawl — после вашего «ок».

**Следующий шаг Ф3 Self-improvement:** A/B промптов по трейсам · авто-суфлёр Стратега.

---

`Спринт:[Ф3] | Задача:[Vendor crawl → RAG tec] | Статус: ✅ done`

**2026-06-17:** API + UI `/ops/vendor-crawl` + фон + **live** на manageengine.com/ru и ptsecurity.com.

---

`Спринт:[Ф3] | Задача:[Quality gate tuning] | Статус: ✅ done — [x] MAP`

**2026-06-17:** A+B+C зелёные; acceptance [`F3_GATE_TUNING_ACCEPTANCE.md`](../phase3/agents/F3_GATE_TUNING_ACCEPTANCE.md).

---

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 2] | Статус: ✅ done`

**2026-06-16:** Ф3 gate шаг 2 — rescue 36/36, enrich smoke 100%. **Коммит:** `dc1220c`.

---

`Спринт:[Ф3] | Задача:[Quality gate tuning — шаг 1] | Статус: ✅ done`

**2026-06-16:** шаг 1 — порог 85%, parse_intent, enrich tech/econ/strategist. **Коммит:** `6efd107`.
