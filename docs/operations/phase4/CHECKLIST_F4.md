# Чеклист: Фаза 4 — Тюнинг и MVP

**Статус фазы:** 🔄 **текущая фаза**

> **Легенда:** ✅ готово (код + смоук + acceptance) · ⚠️ код ✅, хвост в `BACKLOG.md` · 🔲 не начато · `[x]` = ✅ по коду/автомату · `[ ]` = 🔲 или хвост.
> **Закрытие пункта:** pytest + acceptance → `[x]`; финальный `[x]` — только после «ок» оператора. DoD пункта → [`dev-gates`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).
> Результаты (acceptance) — в папках областей рядом: `./{область}/*.md`. Хвосты → [`../session/BACKLOG.md`](../session/BACKLOG.md).

---

## Фаза 4 — Тюнинг и MVP

> Polish и доводка после базового Ф3. **Старт Ф4:** обход с дашборда — см. [`F4_DASHBOARD_ACCEPTANCE.md`](../phase4/dashboard/F4_DASHBOARD_ACCEPTANCE.md).

### Дашборд (обход Ф4)

Детали: [`F4_DASHBOARD_ACCEPTANCE.md`](../phase4/dashboard/F4_DASHBOARD_ACCEPTANCE.md)

- [x] Модалка «Новый лид» — дашборд + `/leads/list`, POST в БД · [`F4_DASHBOARD_ACCEPTANCE.md`](../phase4/dashboard/F4_DASHBOARD_ACCEPTANCE.md) · апрув 2026-06-19

### Интеграции CRM (Ф4, перед обходом лидов)

Детали: [`F4_CRM_INTEGRATIONS_ACCEPTANCE.md`](../phase4/platform/F4_CRM_INTEGRATIONS_ACCEPTANCE.md) · тюнинг [`F4_PLATFORM_TUNING.md`](../phase4/platform/F4_PLATFORM_TUNING.md)

- [ ] Экран **`/ops/integrations`** — Битрикс, Amo, HubSpot; статусы подключения · шаг 1, **создаём**
- [ ] **OAuth / credentials топ-3:** Битрикс24 (№1) → AmoCRM (№2) → HubSpot (№3)
- [ ] **Security:** шифрование токенов (AES), middleware вебхуков (подпись), валидация входа
- [ ] **Импорт/экспорт в 1 клик** — API + CSV-шаблон; кнопки на `/leads/list` из UI credentials
- [ ] **Маппинг стадий/полей** в Ops (ручной, без LLM на MVP)
- [ ] Битрикс исходящий вебхук + расписание синка · после подключения
- [x] **Битрикс расширенный маппинг** — ИНН/реквизиты/контакт/домен/продукты + таймлайн в «Действия»; poll DATE_MODIFY + local batch · код 2026-06-22 · апрув ждём
- [x] **Битрикс история + дела:** mass-resync `resync_bitrix_lead_engagement.py`; `crm.activity`+comments→история; встречи/задачи→`tasks`; upsert+poll · код 2026-06-22
- [ ] Smoke + acceptance закрыт · `tests/integrations/`

### Лиды (обход Ф4)

Детали: [`F4_LEADS_ACCEPTANCE.md`](../phase4/leads/F4_LEADS_ACCEPTANCE.md)

- [x] Создание лида — модалка дашборд + `/leads/list`, POST в БД · апрув 2026-06-19
- [x] Удаление лида — confirm, list + карточка, DELETE в БД · pytest `test_lead_delete_ui.py` · апрув 2026-06-19
- [x] **Сегментация списка:** нормализация ОКВЭД (`okved_main`/`okved_section`), `employees_band`, `portrait_score`; фильтры + **группировка** (ОКВЭД/размер/этап) на `/leads/list`; CSV; backfill · код 2026-06-22 · **апрув обход**
- [x] **Дела в списке:** API-флаги `taskDueToday`/`taskOverdue`; сортировка «Дела срочные» по умолчанию; фильтры «сегодня»/«просроч.»/«есть открытые»; KPI + бейдж в строке; `/leads/tasks?filter=today`; фикс даты при создании задачи в карточке · код 2026-06-22
- [x] **Отрасли из ОКВЭД:** `okved_industry_map` → `industry_bucket`; авто-sync + backfill; фильтр «Отрасль» + группировка на `/leads/list` · код 2026-06-22
- [x] **Продукты из Битрикс:** `lead_products` (название, цена, статус sold/pipeline/owned); productrows+сделки+КП+UF+OPPORTUNITY; плитка «Продукты»; `resync_bitrix_lead_products.py` (`--workers`, webhook) · код 2026-06-22 · **массовый resync в прогоне**
- [x] **UF Битрикс → `bitrix_extra`:** подписка до, тип поставки, срок лицензии, резерв, licensing email, сублицензиат, плательщик, менеджер, участник; `lead_bitrix_extra` + enrich upsert; API `bitrixExtra` · код 2026-06-19
- [x] **Мультиконтакты Битрикс:** `crm.lead.contact.items` → `contacts[]`, merge без затирания ручных · код 2026-06-19
- [x] **Сумма + валюта:** OPPORTUNITY/CURRENCY_ID → `amount`+`currency` в API, карточка · код 2026-06-19
- [x] **Webhook scope task:** probe + fix `tasks.task.list` 401, `check_bitrix_webhook_scopes.py`, `resync_bitrix_lead_tasks.py` · код 2026-06-19
- [x] **UI карточки X5-gap:** шапка `15 780 $` + бейдж «Повторный лид»; блок «Лицензия / подписка»; список контактов; сворачиваемые сырые UF · код 2026-06-19
- [x] **Mass-resync полей:** `resync_bitrix_lead_fields.py` — `bitrix_extra`, contacts, `deal_amount` на b24-лидах (`--workers 4`) · код 2026-06-19
- [x] **Список: подписка / поставка:** фильтры «истекает» / «тип поставки»; колонка-бейдж «подписка до» · код 2026-06-19
- [x] **Критично:** карточка end-to-end — сохранение, этап, комментарии, касания, задачи · **апрув обход 2026-06-25**
- [x] **Критично:** UX фильтров `/leads/list` — подписи тир/подсказка, меню импорта, KPI · верстка 2026-06-19 · **апрув обход 2026-06-25**
- [x] **Критично:** UX карточки — хаб плиток + slide-over ~65%; единая шапка (назад + мета + действия), без дубля summary · верстка 2026-06-19 · **апрув обход 2026-06-25**
- [ ] **DnD порядка плиток хаба** на `/leads/[id]` — хватаешь плитку, ставишь раньше/позже; порядок в `localStorage` · [`F4_LEADS_ACCEPTANCE.md`](../phase4/leads/F4_LEADS_ACCEPTANCE.md)
- [ ] **Редизайн хаба карточки:** 5 плиток (Клиент / Работа / Письма / Продукты / Агенты); этап+путь сделки в шапке; без ✉️/🔗 в тулбаре · [`F4_LEADS_ACCEPTANCE.md`](../phase4/leads/F4_LEADS_ACCEPTANCE.md)
- [ ] **Тех. спец на карточке** — кнопка в плитке «Агенты» + `POST /api/agents/email/run` для `tech_specialist` · [`F4_LEADS_ACCEPTANCE.md`](../phase4/leads/F4_LEADS_ACCEPTANCE.md)
- [x] **Критично:** производительность списка при 3000+ лидах — не тормозит · **апрув обход 2026-06-25**
- [ ] **Критично:** голос — update лида + смена этапа (не только create/filter/delete) · **отложен** (после приёмки проекта)
- [x] Карточка — редактирование, этап, комментарии, касания, задачи, enrich, рассылка · **апрув обход 2026-06-25**
- [x] Воронка — Kanban DnD, гейты стадий · **апрув обход 2026-06-25**
- [x] Список — фильтры, сортировка · **апрув обход 2026-06-25** (голосовой фильтр — отложен)
- [x] **Дела** `/leads/deals` — фильтры, сортировка, переход в карточку · **апрув обход 2026-06-25**
- [x] Задачи / календарь / фокус — smoke после Ф4 · **апрув обход 2026-06-25**
- [x] Аналитика `/leads/analytics` — smoke · **апрув обход 2026-06-25**
- [ ] Голос на лидах — create, filter, delete approve (S04) · **отложен** (после приёмки проекта)

### Мой день (приоритет очереди)

Детали: [`F4_DAY_PRIORITY.md`](../phase4/leads/F4_DAY_PRIORITY.md) · спека согласована 2026-06-27

- [x] **Спека и формула** — этап+`dealPath` первичны, тип задачи вторичен, затухание «жду ответ» · док готов
- [x] **`lead_day_priority.py`** — `dayRank`, `stageBoost`, `urgencyBucket`, `waitStalePenalty` · 2026-06-27
- [x] **Классификатор дел** — `classify_task_intent(title)` + словарь intent→tier · `lead_task_intents.py`
- [x] **API** — поля `dayRank`, `taskIntent`, `needsEnrich` в `GET /api/leads` и `/api/leads/activities`
- [x] **UI list + deals** — сортировка «Мой день», `listCoach` + `listStageSummary` (этап, путь, даты) в строке · 2026-06-27
- [x] **Суфлеры** — `lead_stage_hints`: `wait_stale`, `repeat_wait_task`
- [x] **Типы задач в CRM** — dropdown `task_intent` при создании (tasks, карточка, activity panel) · 2026-06-27
- [x] **Ops** — веса `day_priority` в `/ops/crm` (опционально) · 2026-06-27
- [ ] Приёмка по §11 `F4_DAY_PRIORITY.md` · `[x]` только после «ок» оператора

### Email (тюнинг Ф4)

Детали: [`F4_EMAIL_TUNING.md`](../phase4/email/F4_EMAIL_TUNING.md)

- [ ] Ящики в UI (`/email` Настройки или `/ops/integrations`) — без единственной зависимости от `.env`
- [ ] Тест IMAP/SMTP из формы; статусы подключения; шифрование пароля at rest
- [ ] Счётчик исходящих/день; warn/block перед массовой отправкой и `send_now`
- [ ] Лимит FAQ auto-reply в `/ops/email-agents` (не только env)
- [ ] LLM-nurture на все **20** касаний (сейчас пилот 3)
- [ ] Апрув превью цепочки перед стартом nurture по сегменту
- [ ] Пауза nurture при ответе клиента — smoke на живом ящике
- [ ] История кампаний и цепочек — фильтры, статус шагов
- [ ] Вкладка «Почта» на карточке — паритет с `/email` (ответ, апрув, анализ+черновик)
- [ ] Кнопка «Рассылка» на карточке — превью сегмента + лимит перед отправкой
- [ ] Relink сирот с карточки лида
- [ ] Маскировка email в логах и `/ops/traces`
- [ ] Аудит: кто отправил письмо / запустил кампанию / nurture
- [ ] Фильтр PII перед LLM (черновики, nurture)
- [ ] Голос: `write_email`, `send_email`, рассылка по сегменту · **после** снятия отложенности голоса на лидах
- [ ] «Переделай короче» для черновика письма (F3 Voice §2)
- [ ] Acceptance: pytest `tests/email/` + live smoke + DevTools `/email`, `/ops/email`, карточка

**UI Яндекс.Почта:** [`F4_EMAIL_YANDEX_UI.md`](../phase4/email/F4_EMAIL_YANDEX_UI.md)

- [x] Сайдбар + папки + жёлтая «Написать» · код 2026-06-25
- [x] Поиск pill + чипы фильтров · код 2026-06-25
- [x] «Главное» (звезда на треде) · код 2026-06-25
- [x] Тред: одно письмо + сайдбар «Письма на тему» + strip цитат · код 2026-06-25
- [ ] Browser-апрув по чеклисту `F4_EMAIL_YANDEX_UI.md`
- [ ] IMAP: непрочитанные, вложения, Trash/Drafts/Spam

### Vendor crawl → RAG tech_specialist (тюнинг)

Детали: [`F4_VENDOR_CRAWL_TUNING.md`](../phase4/rag/F4_VENDOR_CRAWL_TUNING.md)

- [ ] Автокраул (`auto_crawl_enabled`, интервал, фоновый poll)
- [ ] Глубже `doc_urls` — KB, datasheet, release notes
- [ ] Метаданные чанков — продукт / тип дока (datasheet, manual, …)
- [ ] Eval retrieval — 10–20 вопросов к tech_specialist, pass rate

### A/B промптов по трейсам (тюнинг)

Детали: [`F4_PROMPT_AB_TUNING.md`](../phase4/agents/F4_PROMPT_AB_TUNING.md)

- [ ] Эталон intent при 👎 на трейсе
- [ ] Больше кейсов + регрессия на 👍 / approved eval
- [ ] Выбор модели (groq / hermes3) в UI
- [ ] A/B для промптов агентов (`/ops/agents`)
- [ ] Suggest-prompt → сразу A/B
- [ ] История отчётов A/B в Ops
- [ ] Dr. QA / KPI-gate в UI

### Авто-суфлёр Стратега (тюнинг)

Детали: [`F4_STRATEGIST_SUGGESTER_TUNING.md`](../phase4/agents/F4_STRATEGIST_SUGGESTER_TUNING.md)

- [ ] Runtime агентов читает `agent_prompt_*.txt`
- [ ] 👎 с ожидаемым ответом / intent
- [ ] Больше сигналов + агрегация по агенту
- [ ] После apply → gate / A/B
- [ ] История предложений суфлёра
- [ ] Периодический запуск / очередь Ops
- [ ] Цепочка Hermes: suggest → A/B → apply
- [ ] Суфлёр по одному агенту в UI

### Контур.Закупки (после gate)

Детали: [`F4_KONTUR_GATE.md`](../phase4/tenders/F4_KONTUR_GATE.md)

- [ ] Gate: первая тендерная сделка + go оператора
- [ ] Адаптер `tender_sources/kontur.py` + `TENDER_PROVIDER=kontur`
- [ ] Smoke: search / monitor / карточка без смены UI

### Тех. спец — тендеры (тюнинг Ф4)

Детали: [`F4_TECH_TENDER_TUNING.md`](../phase4/tenders/F4_TECH_TENDER_TUNING.md)

- [ ] Автопайплайн: мониторинг → скачать доки → оценка → пуш с вердиктом
- [ ] Автозагрузка ТЗ/PDF с площадки (кэш по external_id)
- [ ] UI: матрица «ТЗ ↔ продукты» (ok / gap / risk)
- [ ] Мониторинг → задача/лид в CRM по вердикту + напоминания
- [ ] Eval/gate качества тендерного тех. разбора (15–20 кейсов)

### Аналитика v2 (тюнинг Ф4)

Детали: [`F4_ANALYTICS_V2_TUNING.md`](../phase4/analytics/F4_ANALYTICS_V2_TUNING.md)

- [ ] Прогноз на карточке лида + поле `expected_close_at`
- [ ] Срез «закрытие по кварталу/месяцу» на analytics
- [ ] Калибровка % стадий по реальным won/lost из БД
- [ ] LLM-Экономист по запросу на лид (кэш, rationale)
- [ ] 👎/👍 по агенту в трейсе + связка stats → A/B/суфлёр
- [ ] Когорты по неделе/кварталу (переключатель)

### Баллы (тюнинг Ф4)

Детали: [`F4_SCORING_TUNING.md`](../phase4/leads/F4_SCORING_TUNING.md)

- [ ] UI весов `scoring_advisory` в Ops (`/ops/crm`) — сейчас только API/JSON, на карточке ссылка врёт
- [ ] Breakdown подсказки на карточке лида (этап, сумма, апрувы, штрафы)
- [ ] Список лидов: флаги `hasScoreWarnings` / `scoreDivergent` + фильтры
- [ ] Прогноз закрытия на карточке (перекрёст с Analytics v2)
- [ ] Единые пороги CRM ↔ лидоген или явная подпись в UI
- [ ] Ops-видимость расхождений балла (badge / очередь)

### Платформа

Детали: [`F4_PLATFORM_TUNING.md`](../phase4/platform/F4_PLATFORM_TUNING.md)

- [ ] Экран интеграций в UI (Битрикс, Amo, HubSpot, Telegram) — без правки `.env`
- [ ] Credentials в БД (шифрование), статусы подключения, OAuth/мастера
- [ ] Расписание синка + маппинг стадий + конфликты полей
- [ ] Битрикс: исходящий вебхук из UI + подсказка туннеля
- [ ] Telegram: привязка чата из UI, дайджест, уведомления тендеров
- [x] SLA-протоколы + эскалация — см. P3 [`F3_SLA_PROTOCOLS_ACCEPTANCE.md`](../phase3/leads/F3_SLA_PROTOCOLS_ACCEPTANCE.md)
- [x] Экспорт отчёта по баллам и воронке — см. P3 [`F3_SCORING_EXPORT_ACCEPTANCE.md`](../phase3/leads/F3_SCORING_EXPORT_ACCEPTANCE.md)
- [ ] Acceptance + smoke живых интеграций

---

## Сводка модулей

| Модуль | Фаза | Сдано | Вернуться / следующий шаг |
|--------|------|-------|---------------------------|
| Лиды | 1 | ✅ 2026-06-08 | — |
| Баллы | 1 (+P3) | ✅ P3 | Ф4: [`F4_SCORING_TUNING.md`](../phase4/leads/F4_SCORING_TUNING.md) |
| Голос лиды | 1 | ✅ (хвосты 🟡) 2026-06-11 | `VOICE_MIC_E2E_ACCEPTANCE.md`; п.3/5 spot-check → `BACKLOG` |
| Поиск/RAG | 1→2 | ✅ база | Ф2 §4: кэш enrich, авто-чанки |
| Лиды enrich | 2 | ✅ | Ф2 §9: кнопка + голос enrich — `LEADS_CARD_ENRICH_ACCEPTANCE.md`, `LEADS_ENRICH_VOICE_ACCEPTANCE.md` |
| Лидоген | 1→2 | ✅ Ф1 | **Ф2 §8:** голос ✅ · `LEADGEN_VOICE_F2_ACCEPTANCE.md` |
| Тендеры | 1→2→3 | ✅ baseline 2026-06-11 | `TENDERS_BASELINE_ACCEPTANCE.md` · Ф2 §7 голос/платный API |
| Email | 2→3→4 | 🔲 | Ф4: [`F4_EMAIL_TUNING.md`](../phase4/email/F4_EMAIL_TUNING.md) |
| Оркестрация | 2 | 🔲 | Ф2 §2: fanout |
| Агенты | 1→2 | ✅ чат | Ф2 quality gates → `/ops/eval` |
| Безопасность | 2→3 | ⚠️ dev OK | **Ф2 оч.10** перед продом · **Ф3** роли/аудит |
| Инфра прод | 2→3 | 🔲 | отдельный шаг перед деплоем |
| Качество/coverage | сквозное | ✅ smoke | ориентир 60%/75% Ф2/Ф3 · не gate · dev-gates |
| Ops | 1→2 | ✅ | Ф2 §5: версии промптов |
| Аналитика | 1→2→3 | ✅ база | Ф2 §6: голос |

---
