# CHANGELOG (операционный)

**Роль:** источник правды по истории — что сделано, когда, почему и при каким `go`.

## 2026-06-25 — Resume: mass backfill Битрикс → CRM

Перезапуск поля/таймлайн (resume 270)/дела/продукты + watch only-missing. CLI `spawn_bitrix_backfill_all.py`, `--resume` на engagement.

## 2026-06-24 — UI /leads/deals: дела по лидам как в B24

Вкладка «Дела»: лид + ближайшее открытое дело, срок с временем, фильтры scheduled/today/tomorrow/overdue/incoming, менеджер. API `GET /api/leads/activities`. Фильтр «завтра» в списке лидов и задачах.

## 2026-06-24 — B24 таймлайн: комменты + хронология в «Действия и история»

**Было:** в карточке лида панель истории почти пустая — синкали только дела/встречи (`crm.activity` → tasks), комментарии и системные события B24 не подтягивались массово.

**Стало:** полный fetch таймлайна (`crm.timeline.comment.list`, `crm.timeline.logmessage.list`, «Создан лид» из `crm.lead.get`); единая UI-лента (коммуникации + задачи/встречи без дублей); `check_bitrix_engagement_backfill.py`; mass `resync_bitrix_lead_engagement.py --timeline-only`.

## 2026-06-24 — Fix: 404 coverage/managers на списке лидов

`leadsStorage.js` дублировал `/leads` в URL (`/api/leads/leads/coverage`). Activity resync завершён: 3228 лидов, 359 задач.

## 2026-06-24 — UI /leads/list: фильтр по менеджеру

Справочник из БД (ответственный + UF manager). Dropdown, колонка в таблице, бейдж в карточке. `CRM_OPERATOR_NAME` — фильтр по умолчанию.

## 2026-06-24 — UI /leads/list: счётчики и фильтры полноты карточки

Сегменты B24 (полный/частичный/пустой), паспорт, карточка готова, пустые, проигран, без дел. `core/lead_coverage.py`, `GET /api/leads/coverage`, чипы на списке лидов.

## 2026-06-24 — UI /leads/tasks: фильтры статус + срок + эскалация

Два ряда чипов; API task_status/due/escalated; бейджи Просрочено/Сегодня/Выполнено.

## 2026-06-24 — UI /leads/tasks: список сверху, создание в модалке

Таблица задач на всю высоту; фильтры в шапке; «+ Создать задачу» и «+ SLA» → модалка.

## 2026-06-24 — Ф4: crm.activity синк без scope task

Встречи/дела/звонки из Битрикса → tasks в CRM без галочки «Задачи» на вебхуке. `tasks.task` опционально. Mass resync activity в фоне.

## 2026-06-24 — Ф4 X5-gap: апрув 5/7 + only-missing дожим resync

**👤:** апрув карточки и списка. Resync ~1205/3228; `--only-missing` + watcher для дожима после done.

## 2026-06-24 — Ф4 X5-gap: browser-апрув чеклист + fix календаря

**Прогон:** resync 985/3228; DevTools шаги 5/7 + календарь OK. Док: `F4_X5_BROWSER_APPROVAL.md`. Fix: закрывающие `</div>` в `calendar/+page.svelte`. **👤:** формальный апрув шагов 5/7; mass-resync до 3228.

## 2026-06-24 — Ф4 X5-gap шаг 4: webhook scope task — extended probe + acceptance

**Live:** crm/user ok, task missing; feature probes + JSON report; resync preflight блокирует без task. Док: `F4_X5_WEBHOOK_TASK_SCOPE_ACCEPTANCE.md`. **Оператор:** scope task на портале.

## 2026-06-24 — Ф4 X5-gap шаг 3: сумма + валюта — acceptance + backfill статус

**Код:** ✅. **Данные:** 663/3228 deal_amount; эталон 5227 → `15 780 $`. Док: `F4_X5_DEAL_AMOUNT_ACCEPTANCE.md`; resync resume после Errno 22.

## 2026-06-24 — Ф4: mass-resync — rate-limit, auto-sync pause, multi-contacts metrics

**Было:** Access denied при параллельных REST; contacts/deal не отслеживались в check. **Стало:** retry+semaphore в `bitrix_call`; `bitrix_resync_guard` паузит poll; state `with_multi_contacts`; check script — `contacts multi`, `b24-contact-*`. Прогон 162/3225.

## 2026-06-24 — Ф4 лиды: mass-resync bitrix_extra — фикс + перезапуск

**Было:** прогон завис на 40/3225; `bitrix_extra` 0; затем Access denied на workers=3. **Стало:** light enrich; agneko UF map; retry/backoff; resume/state; runbook; **50/3225** в БД с extra, прогон в фоне (workers=1).

## 2026-06-19 — Ф4 лиды: список — подписка и тип поставки (шаг 7)

**Было:** `bitrixExtra` только в карточке; в списке нельзя отфильтровать истекающие подписки или тип поставки. **Стало:** фильтры «Подписка» и «Тип поставки»; колонка «Подписка до» с бейджем (просрочена / истекает / ок); pytest + smoke PASS.

## 2026-06-19 — Ф4 лиды: mass-resync полей (шаг 6)

**Было:** `bitrix_extra`, мультиконтакты и `deal_amount` только у новых upsert; ~3225 старых лидов без полей. **Стало:** `resync_bitrix_lead_fields.py` — API enrich + merge без затирания ручных контактов; `--no-api` для UF offline; pytest 6 PASS; полный прогон `--workers 4` запущен в фоне.

## 2026-06-19 — Ф4 лиды: UI карточки X5-gap (шаг 5)

**Было:** `bitrixExtra` и мультиконтакты в API, но в UI карточки не отображались; сумма `15 780 USD`; нет бейджа «Повторный лид»; сырые UF только в `tech_json`. **Стало:** шапка `15 780 $` + бейдж; блок «Лицензия / подписка» (6–8 полей); readonly-список контактов; сворачиваемый fallback «Поля Битрикс (сырые UF)»; превью плитки «Карточка»; pytest mirror+smoke PASS. **Хвост:** mass backfills шагов 1–3, scope task, browser апрув — `BACKLOG.md`.

## 2026-06-19 — Ф4 лиды: webhook scope task (tasks.task.list)

**Было:** `tasks.task.list` → 401 (только `crm`+`user` на вебхуке); задачи Битрикс не импортировались, resync молча пропускал. **Стало:** `bitrix_webhook_scopes` + `check_bitrix_webhook_scopes.py`; ошибка с инструкцией включить **task**; preflight в resync; `resync_bitrix_lead_tasks.py`; pytest 10 PASS. **Оператор:** на портале B24 включить scope task и перезапустить resync.

## 2026-06-19 — Ф4 лиды: сумма + валюта (OPPORTUNITY)

**Было:** USD/EUR суммы только в `budget` текстом; `amount_rub` пусто для X5 (15 780 $). **Стало:** колонки `deal_amount`/`deal_currency`; API `amount`+`currency`; маппинг Битрикс; merge без затирания; отображение в шапке и панели карточки; analytics `lead_amount_rub` для RUB из `amount`; pytest 35+ PASS.

## 2026-06-19 — Ф4 лиды: мультиконтакты из Битрикс

**Было:** только `CONTACT_ID` → 1 контакт в `contacts[]` (X5: 1 вместо 5+). **Стало:** `crm.lead.contact.items.get` + параллельный `crm.contact.get`; все телефоны/email; primary → `lpr`; `merge_bitrix_contacts` при upsert сохраняет ручные контакты CRM; pytest 10 PASS.

## 2026-06-19 — Ф4 лиды: UF Битрикс → `bitrix_extra`

**Было:** UF подписки/лицензии/поставки только в `tech_json`, в API и UI не отдавались; фильтры по датам подписки невозможны. **Стало:** колонка `leads.bitrix_extra` (JSONB); `lead_bitrix_extra` + расширен `bitrix24_uf`/`enrich_fields_from_bitrix_row`; merge без затирания; `bitrixExtra` в `Lead.to_dict()`; offline backfill из `tech_json`; pytest 14 PASS (лид X5-подобный).

## 2026-06-22 — Ф4 лиды: Битрикс история + задачи/встречи

**Было:** таймлайн только при upsert (на 3225 лидах пусто); встречи Битрикс не попадали в `/leads/tasks`. **Стало:** `bitrix24_tasks` (activity + tasks.task → `tasks`); mass-resync `resync_bitrix_lead_engagement.py`; upsert тянет историю и дела; доки в `leads.md`; pytest 30+ PASS.

## 2026-06-22 — Ф4 лиды: массовый resync продуктов из Битрикс API

**Было:** offline backfill 0 (нет UF в `tech_json`); resync без `.env` и без КП. **Стало:** `fetch_bitrix_lead_products` тянет lead row, productrows, сделки, **коммерческие предложения**, имена из `crm.product.get`, сумму OPPORTUNITY; `resync_bitrix_lead_products.py` — `load_dotenv`, `--workers`/`--batch-size`, параллельный fetch; pytest 5 PASS; полный прогон 3225 b24-лидов через webhook (фон).

## 2026-06-22 — Ф4 лиды: продукты из Битрикс + плитка в карточке

**Было:** только `products_owned` строками из UF; в UI — textarea в slide-over, без цены и статуса. **Стало:** `lead_products` JSON (название, цена, статус sold/pipeline/owned); загрузка из UF + `crm.lead.productrows` + сделок; плитка «Продукты» в хабе; `resync_bitrix_lead_products.py`; pytest 23+ PASS; DevTools: плитка OK.

## 2026-06-22 — Ф4 лиды: отрасли из ОКВЭД (industry_bucket)

**Было:** отрасль — свободный текст; фильтр только substring/голос; группировки по отрасли нет. **Стало:** `okved_industry_map` (секция 01–99 → bucket); колонка `industry_bucket` + sync в `lead_profile`; backfill 3230/158; селект «Отрасль» + группировка на `/leads/list`; сегменты по `industry_bucket`; DevTools: фильтр и group-by OK; pytest 38+ PASS.

## 2026-06-22 — Ф4 лиды: дела видны в списке

**Было:** при сортировке по скору задачи лида не видны в `/leads/list`; создание задачи в карточке ставило `due: '—'`. **Стало:** `lead_task_list_flags` в GET `/api/leads`; сортировка «Дела срочные» по умолчанию; фильтры «Дела» (сегодня/просроч./открытые); KPI + бейдж в строке; deep link `/leads/tasks?filter=today`; дата по умолчанию при постановке задачи; pytest 41+ PASS (crm_leads + smoke).

## 2026-06-22 — Ф4 лиды: ОКВЭД из Битрикс UF (без Checko)

**Было:** ОКВЭД только из checko_json; B24 отдавал ИНН, но не ОКВЭД UF. **Стало:** `extract_okved_from_row` / `extract_employees_from_row`; enrich в `bitrix24_related`; `lead_profile` fallback с колонок лида; скрипт `resync_bitrix_lead_profiles.py`; pytest 12 PASS.

## 2026-06-22 — Ф4 лиды: группировка списка + backfill портрета

**Было:** только фильтры ОКВЭД/размер; backfill не гоняли; группировка в BACKLOG. **Стало:** `groupLeads` + селект «Группировка» (ОКВЭД/размер/этап) со сворачиваемыми заголовками; backfill 3230 лидов / 386 обновлено; DevTools: фильтры и группы OK; pytest 13+ PASS.

## 2026-06-19 — Ф4 лиды: сегментация — ОКВЭД, размер, portrait_score

**Было:** отрасль/ОКВЭД только внутри `checko_json`; нельзя фильтровать список по размеру компании или секции ОКВЭД; CSV без портретных полей. **Стало:** `core/lead_profile.py` + колонки в `Lead`; sync на CRUD/enrich/CSV/B24; фильтры «Размер» и «ОКВЭД сек.» + KPI портрета на `/leads/list`; `backfill_lead_profile.py`; pytest 28+ PASS.

## 2026-06-19 — Ф4 лиды: шапка списка /leads/list

**Было:** заголовок + 6 кнопок импорта в ряд + техстрока B24; фильтры без подписей. **Стало:** «+ Новый лид» + меню ⋯; KPI-строка; подписи Поиск/Сортировка/Тир/Подсказка балла + Сбросить; pytest smoke 4 PASS.

## 2026-06-19 — Ф4 лиды: единая шапка карточки (без дубля)

**Было:** две полоски — breadcrumb+toolbar и summary-карточка с тем же названием. **Стало:** один `<header>`: назад, название, компактная мета, иконки действий; хаб начинается с плиток; pytest smoke 10 PASS.

## 2026-06-19 — Ф4 лиды: хаб карточки + slide-over панели

**Было:** вкладки Обзор/Паспорт/Задачи/Письма/Агенты; обзор — три колонки inline, шум на экране. **Стало:** шапка лида + сетка плиток 2×3 (моб) / 3×2 (десктоп) с превью (стадия · N/M, ИНН, просрочки); контент в `LeadSlideOver` ~65% ширины; `?panel=` в URL; pytest smoke 9 PASS.

## 2026-06-22 — Ф4 интеграции: Битрикс полный маппинг + таймлайн

**Было:** только плоские поля лида; ИНН из UF-эвристики; poll только DATE_CREATE сегодня; комменты Битрикса не в CRM. **Стало:** company/contact/requisites, ИНН/ОГРН, домен, продукты, contacts ЛПР; `crm.activity` + timeline comments → `lead_communication_logs`; poll DATE_MODIFY + local batch; pytest 19 PASS.

## 2026-06-22 — Ф4 лиды: enrich → полный паспорт (checko_json)

**Было:** ✨ обогащал только phone/email/website/budget; паспорт пустой. **Стало:** по ИНН — `fetch_company` + `fetch_full_profile` + BuiltWith; ответ `passport` → PATCH `checkoJson`/`financialsJson`/`techJson`/`inn`/`ogrn`; связи и финблоки в паспорте; фильтр соц-хендлов в телефонах; pytest PASS.

## 2026-06-21 — Ф4 лиды: задачи из блока «Действия»

**Сделано:** чекбокс «Поставить задачу в календарь» + дата; задача с типом действия (Звонок/ВКС/…) → общий календарь; сверху список открытых задач лида с бейджами «Сегодня»/«Просрочено», раскрытие «Ещё N»; pytest 11 PASS.

## 2026-06-21 — Ф4 лиды: обзор три колонки

**Было:** 2 колонки (стадии+действия слева, карточка справа). **Стало:** шапка лида + `xl:grid-cols-3` — «Стадии и документы» | «Карточка клиента» | «Действия и история» с цветными рамками; pytest 9 PASS.

## 2026-06-21 — Ф4 лиды: вкладка «Паспорт клиента» вместо Checko

**Было:** вкладка Checko с частью секций, скрытые пустые разделы. **Стало:** «Паспорт» после Обзора — 20 разделов (общее, надёжность, реквизиты, контакты, ОКВЭД, финансы, налоги, руководитель, учредители, филиалы, **связи**, лицензии, Федресурс, госзакупки, проверки, арбитраж, долги, вакансии, история, технологии); `LeadPassportPanel` + `leadPassport.js`; pytest 9 PASS.

## 2026-06-21 — Ф4 лиды: единый блок «Действия и история»

**Было:** 4 блока (касания, комменты, история полей, лента). **Стало:** одна форма + свёрнутая лента; типы звонок/письмо/ВКС/личная встреча/коммент/заметка; `occurredAt` опционально; техаудит в `<details>`; pytest 20 PASS.

## 2026-06-21 — Ф4 лиды: scoreAdvisory спрятан с обзора

**Было:** подсказка 47/100 и breakdown на левой колонке обзора. **Стало:** только балл менеджера в шапке; подсказка — свёрнутый `<details>` под «Системные поля» справа; API без изменений.

## 2026-06-21 — Ф4 лиды: компактный путь сделки (следующий шаг + accordion)

**Было:** длинный список 18+ шагов, дубль ЛПР, «Следующий шаг» в подсказках. **Стало:** чипы фаз, один блок «Следующий шаг» с «Отметить», свёрнутый accordion; ЛПР только в квалификации; `nextStep` в API; pytest 28 PASS.

## 2026-06-19 — Ф4 лиды: блок контактов и автоматический ЛПР

**Было:** один контакт в плоских полях; «ЛПР установлен» — ручная галочка. **Стало:** `contacts[]` в карточке справа (роли, мульти тел/email/мессенджеры); при полном ЛПР шаг квалификации зелёный; синк в `contact`/`email`/`phone`; pytest 16+ PASS.

## 2026-06-19 — Ф4 лиды: split колонок обзора (квалификация слева, форма справа)

**Было:** swap целых колонок — этап/путь уехали вправо вместе с формой. **Стало:** слева шапка, этапы, stageHints, путь сделки, касания/комменты/лента; справа только «Карточка (редактирование)», суммы ₽, системные поля; убран `lg:order-*`; pytest 6 PASS.

## 2026-06-19 — Ф4 лиды: swap колонок обзора карточки

**Было:** слева редактирование, справа активность. **Стало:** слева касания/комменты/лента, справа этап/путь/форма. `lg:order-1/2`; pytest 6 PASS.

## 2026-06-19 — Ф4 лиды: путь сделки + мульти-подсказки по этапу

**Было:** апрувы — плоский чеклист внизу; одна-две подсказки в warnings; этап без сроков.  
**Стало:** `dealPath` (квалификация → доки до КП → закрытие), `stageHints[]` (🔴 срок 3/8/5 дн, доки, касания КП); UI под этапами; pytest 14+ PASS. Гейты этапа — позже.

## 2026-06-19 — Ф4 лиды: этапы под шапкой карточки

Перенос «Сменить этап» вверх; цветные кнопки `stageBadgeClass`; pytest 6 PASS.

## 2026-06-19 — Ф4 лиды: обзор карточки — две колонки full-width

Убран max-w-5xl по центру; слева поля/этап/апрувы, справа касания/комменты/лента; pytest 4 PASS.

## 2026-06-19 — Ф4 лиды: компактная шапка + сворачиваемый сайдбар

Иконки + title в тулбаре карточки; сайдбар w-14/w-56, скрыт на `/leads/{id}`, ☰; pytest 8 PASS.

## 2026-06-19 — Ф4 лиды: фикс 500 карточки (лишний `</div>`)

Vite/Svelte: `element_invalid_closing_tag` в overview; убран преждевременный закрывающий div; smoke 3 PASS.

## 2026-06-19 — Ф4 лиды: UX карточки — обзор на всю ширину

Убран сайдбар w-80; контент во вкладке «Обзор»; smoke `test_lead_card_page.py` 3 PASS.

## 2026-06-19 — Ф4 лиды: критичные пункты обхода

Карточка, UX фильтров, perf 3000+, голос update/этап — MAP + acceptance §Критично.

## 2026-06-19 — Ф4: блок «Интеграции CRM» (отдельно от Лидов)

`F4_CRM_INTEGRATIONS_ACCEPTANCE.md`; MAP после Дашборд; MVP OAuth/security/импорт; leads §П.0 вынесен. Код: создаём `/ops/integrations`.

## 2026-06-19 — Ф4 лиды §П.0: план интеграций с внешними CRM

Поэтапный план (Битрикс/Amo/HubSpot/CSV/webhooks/адаптеры); MAP §Лиды — первый пункт. Только доки.

## 2026-06-19 — Ф4 лиды: чеклист обхода п.3–9

Приоритеты (сейчас / ближайшее / когда-нибудь), критерии п.3–9 в `F4_LEADS_ACCEPTANCE.md`; MAP §Лиды — 7 новых `[ ]`. Только доки.

## 2026-06-19 — Ф4 лиды: апрув удаление (MAP [x])

Ручной тест list + карточка OK; MAP §Лиды п.2 закрыт.

## 2026-06-19 — Ф4 лиды п.2: удаление (list + карточка)

confirm + apiDelete; purge nurture/email перед DELETE; MAP §Лиды; pytest 20 PASS.

## 2026-06-19 — Ф4 дашборд п.1: модалка «Новый лид»

Глобальная `LeadCreateModal` (дашборд + `/leads/list`), POST `/api/leads`; acceptance `F4_DASHBOARD_ACCEPTANCE.md`; pytest `test_lead_create_ui.py` 5 + leads API 14 PASS.

## 2026-06-17 — Ф4: регресс industryOptions на карточке лида

`test_lead_card_page.py`, smoke GET `/leads/{id}`; DevTools без ReferenceError.

## 2026-06-17 — Ф4 баллы: сортировка списка + DevTools smoke

Сортировка warnings/delta; `smoke_scoring_f4_ui.py`; DevTools smoke list/ops/crm/breakdown; фикс `industryOptions` на карточке.

## 2026-06-17 — Ф4 баллы A–C: Ops веса, breakdown, фильтры списка

UI `scoring_advisory` в `/ops/crm`; breakdown подсказки на карточке; `hasScoreWarnings`/`scoreDivergent` в API списка + фильтры `/leads/list`.

## 2026-06-19 — Ф4 docs: план тюнинга баллов

`F4_SCORING_TUNING.md` — 6 критичных пробелов после P3; секция в PRD_MAP; F4_PLATFORM §D актуализирован.

## 2026-06-19 — P3: smoke экспорт баллов (DevTools + live HTTP)

`smoke_scoring_export.py`; Chrome DevTools: кнопка «Баллы» → xlsx 200; acceptance обновлён.

## 2026-06-17 — P3: экспорт баллов и воронки + [x] SLA в MAP

`GET /api/leads/scoring/export`, отчёт KPI+лиды+воронка по баллам, UI «Баллы» на аналитике; PRD_MAP P3 остаток закрыт.

## 2026-06-17 — P3: SLA-протоколы + эскалация (шаги 1–5)

Пресеты `sla_protocols`, назначение на лид (`PUT /api/leads/{id}/sla-protocol`), автозадачи при смене стадии, фоновый poll эскалации → Ops queue + Telegram critical; UI карточка лида, Ops CRM JSON, фильтры задач; acceptance `F3_SLA_PROTOCOLS_ACCEPTANCE.md`; pytest **24 PASS**.

## 2026-06-17 — Платформа: AmoCRM + HubSpot sync; Telegram inline + Ops critical

Import/push API, `amo_lead_id` / `hubspot_deal_id`, UI кнопки; callback approve/reject; Ops critical → Telegram; PRD_MAP CRM `[x]`.

## 2026-06-17 — Платформа: MAP [x] lead hunt + Telegram; Битрикс push

`[x]` в PRD_MAP для автопоиска и Telegram-бота; `POST /api/leads/{id}/push-bitrix`, `crm.lead.add/update`, UI «В Битрикс»; pytest **5 PASS**.

## 2026-06-17 — Платформа: Telegram-бот (MVP)

`integrations/telegram/`: long polling, уведомления новых кандидатов lead hunt, команды `/start` `/status` `/queue`; acceptance `F3_PLATFORM_TELEGRAM_ACCEPTANCE.md`; pytest **5 PASS**.

## 2026-06-19 — Платформа: lead hunt шаги 6–7 (UI оператора + закрытие acceptance)

`LeadHuntOperatorPanel`, вкладка «Авто-охота» в `/leadgen`, `POST approve-above`, DevTools smoke; PRD_MAP `[x]` ждёт «ок».

## 2026-06-19 — Платформа: lead hunt шаг 5 (фон + уведомления)

Фоновый loop в `main.py`, trace `lead_hunt_run` + `agent_run_log` при approve, баннер и badge в Ops UI; Telegram → BACKLOG; pytest **33 PASS**.

## 2026-06-19 — Платформа: lead hunt шаг 4 (очередь + апрув)

`GET /api/ops/lead-hunt/queue`, approve → `save_candidate_to_crm` + опциональный nurture; UI блок «Найдено агентами» на `/ops/queue` и `/leadgen`; pytest **27 PASS** (lead hunt suite).

## 2026-06-19 — Платформа: lead hunt цикл поиска (агенты)

`lead_hunt_search_cycle`: portrait/prospect → `run_pipeline` light → fanout analyst+marketer+economist, dedup ИНН/company, очередь.

## 2026-06-19 — Платформа: lead hunt шаги 3–6 (поиск, очередь, уведомления, UI)

`search_by_portrait` в прогоне, очередь pending/approve/reject → CRM, in-app уведомления + Ops queue, `/ops/lead-hunt`; pytest 15 PASS.

## 2026-06-18 — Платформа: lead hunt шаг 2 (ICP)

ICP из won + funnelBySource, Стратег LLM, версии в state, API icp/refresh.

## 2026-06-18 — Платформа: lead hunt шаг 1 (каркас)

Фоновый планировщик, config/state JSON, `/api/ops/lead-hunt/*`, ICP-превью из won-лидов.

## 2026-06-17 — Платформа: CSV импорт/экспорт лидов (шаг 1 CRM sync)

`crm_sync/csv_adapter`, API import-csv + export, UI `/leads/list`; Amo/HubSpot → BACKLOG.

## 2026-06-17 — Платформа: экспорт Excel/PDF

Воронка (csv/xlsx/pdf), карточка лида (pdf), списки тендеров (xlsx/pdf). `export_reports.py`, UI кнопки. Telegram-бот → BACKLOG.

## 2026-06-17 — Ф4 план: Аналитика v2 (тюнинг)

Прогноз на карточке, калибровка, LLM-Экономист, фидбек по агенту — `F4_ANALYTICS_V2_TUNING.md`.

## 2026-06-17 — Аналитика v2 закрыта: прогноз закрытия (Экономист)

Эвристика стадия+балл, `closureForecast`, UI на `/leads/analytics`. Блок MAP 4/4.

## 2026-06-17 — Аналитика v2: воронка по источнику

`funnelBySource` — стадии воронки отдельно по каналу лида.

## 2026-06-17 — Аналитика v2: эффективность агентов по трейсам

Срез 👍/👎 по агентам, needsAttention, `/ops/stats`, API analytics/agents.

## 2026-06-17 — Аналитика v2: когортный анализ

Месяц входа лида → конверсия; API/UI/CSV; `F3_ANALYTICS_V2_COHORT_ACCEPTANCE.md`.

## 2026-06-17 — Ф4 план: Тех. спец — тендеры (тюнинг)

Автопайплайн, автодоки, матрица ТЗ, CRM-действия, eval — `F4_TECH_TENDER_TUNING.md`.

## 2026-06-17 — Ф3 Тендеры: вердикт участия + MAP sources [x]

Структурированный `participation` из evaluate; UI вкладка «Вердикт»; сохранение в snapshot; апрув бесплатных источников.

## 2026-06-17 — Ф3 Тендеры: бесплатные источники + Контур в Ф4

`tender_sources`, Gosplan prod, min_relevance, DataNewton на карточке.

## 2026-06-17 — Ф3 уведомления + календарь

In-app уведомления, календарь, фоновый скан дедлайнов.

## 2026-06-17 — pytest.ini: StarletteDeprecationWarning

Удалён устаревший filterwarnings; pytest стартует без `-c NUL`.

## 2026-06-17 — Ф3 Тех. спец: мониторинг тендеров (п.1)

Правила слова/ОКПД2, фон, Ops-очередь, UI `/ops/tender-monitor`.

## 2026-06-17 — Ф3 Суфлёр MAP `[x]` + Ф4 рекомендации

Апрув суфлёр; чеклист тюнинга в `F4_STRATEGIST_SUGGESTER_TUNING.md`.

## 2026-06-17 — Ф3 Авто-суфлёр Стратега

**Было:** только ручное редактирование промптов; слабые ответы не агрегировались.

**Стало:** сбор 👎/gate → Groq-Стратег предлагает правки → апрув на `/ops/agents`; pytest 8 PASS.

## 2026-06-17 — Ф3 A/B промптов MAP `[x]`

Апрув пользователя — пункт MAP закрыт.

## 2026-06-17 — Ф3 A/B промптов по трейсам Hermes

**Было:** версии промптов и suggest-prompt, но нет сравнения baseline vs вариант на 👎 фразах.

**Стало:** `prompt_ab_traces.py`, API `POST /hermes/prompt/ab-traces`, UI `/ops/intents/improve`; pytest 5 PASS.

## 2026-06-17 — Ф3 Vendor crawl MAP `[x]`

Апрув «ок» — краулинг закрыт в PRD_MAP; тюнинг вынесен в Ф4.

## 2026-06-17 — Ф3 Vendor crawl шаг 4: Playwright SPA PDF

**Было:** PDF только из HTML и web search; ссылки за JS на SPA не попадали в очередь.

**Стало:** `vendor_crawl_playwright.py` — Chromium discover + fallback fetch; `use_playwright` (PT on); UI; pytest 29 PASS.

## 2026-06-17 — Ф3 Vendor crawl шаг 3: live PDF + RAG

**Было:** PDF search находил URL, но `fetch_failed` — `_is_fetchable_url` блокировал `.pdf`.

**Стало:** фикс fetch; live ME+PT — **10 PDF OK**, **871 чанк**, RAG tech_specialist видит PDF (ServiceDesk, NGFW и др.).

## 2026-06-17 — Ф3 Vendor crawl шаг 2: фильтр качества до чанков

**Было:** любой распарсенный текст шёл в RAG; мусор мог засорять базу.

**Стало:** `assess_crawl_text` — too_short, garbled, few_words, repetitive, low_letters; `quality_rejected` в отчёте; pytest 23 PASS.

## 2026-06-17 — Ф3 Vendor crawl шаг 1: автопоиск PDF

**Было:** PDF только из HTML-ссылок; 0 PDF в live v2.

**Стало:** `search_pdfs` + `site:домен filetype:pdf`; лимит `max_pdf_pages`; `%PDF` bytes; UI; pytest 18 PASS.

## 2026-06-17 — Ф3 Vendor crawl v2 (doc_urls, фильтр, PDF, 582 чанка)

**Было:** 8 стр лимит, 51 чанк, PT 3/8 из‑за woff2 в очереди.

**Стало:** `doc_urls` + UI; фильтр мусора; приоритет docs/products/PDF; sitemap; max 40 depth 2; live **80/80**, **582** чанков. pytest 13 PASS.

## 2026-06-17 — Ф3: gate `[x]` MAP + live vendor crawl

**Было:** gate A+B ✅, C в фоне; crawl только код/API/UI, без реальных сайтов.

**Стало:**
- Quality gate tuning — **`[x]` PRD_MAP** (апрув «ок»): live agents `overall_gate: pass`, Economist 93.3%, остальные 100%.
- Live crawl ManageEngine RU + PT Security → **51 чанк** в RAG tech_specialist; конфиг `vendor_crawl_config.json`.
- ISSUES live Ollama timeout → закрыта (enrich/rescue на CPU).

**Не сделано:** `[x]` MAP crawl (ждём «ок»); фильтр `.woff2` в краулере; economist-005.

## 2026-06-17 — Ф3 Vendor crawl: UI Ops + фоновый планировщик

**Сделано:** `/ops/vendor-crawl`, `vendor_crawl_background.py`, lifespan в `main.py`; auto_crawl в конфиге; pytest 11 PASS. **Коммит:** см. SESSION_STATE.

## 2026-06-17 — Ф3 Vendor crawl → RAG tech_specialist (API)

**Сделано:** `vendor_crawl.py` + config JSON + API `/api/rag/vendor-crawl/*`; дедуп source_id по URL; pytest 5 PASS; acceptance `F3_VENDOR_CRAWL_ACCEPTANCE.md`. **Не сделано:** UI Ops, cron — BACKLOG. **Коммит:** см. SESSION_STATE.

## 2026-06-17 — Ф3 Quality gate tuning: шаг 3 (live Hermes 36/36 + CPU profile)

**Сделано:** live Hermes **36/36** (100%) через parse_intent+rescue; enrich smoke **100%**; `GATE_CPU_PROFILE` (qwen2.5:3b, fast Hermes timeout); enrich-on-LLM-error у 5 агентов; `F3_GATE_TUNING_ACCEPTANCE.md`; agents-only фон. **Не сделано:** live agents C — в прогоне. **Коммит:** см. SESSION_STATE.

## 2026-06-17 — Ф3 Quality gate tuning: шаг 3 старт (live gate фон)

**Сделано:** проверка Ollama + `hermes3:latest`; backend :8000; запуск live full gate с `EVAL_OLLAMA_TIMEOUT=3600`, лог `gate_live_20260617_152400.log`. ISSUES → в работе. **Найдено:** конфликт `Tee-Object` + `--log-file` — в RUNBOOK только `--log-file`. **Не сделано:** прогон ещё идёт; prompt/rescue фиксы — по мере fail в логе. **Коммит:** см. SESSION_STATE.

## 2026-06-16 — Ф3 Quality gate tuning: шаг 2 (enrich smoke 100%)

**Было:** rescue 26/36, marketer без enrich, live Ollama timeout.

**Стало:** rescue 36/36; enrich analyst+marketer; `run_gate_enrich_smoke.py` — все агенты 100% @85%; acceptance обновлён; ISSUES live timeout. **Коммит:** `dc1220c`.

## 2026-06-13 — Ф3 Quality gate tuning: шаг 1

**Было:** Hermes 72%, Tech 60%, порог агентов 75%, gate Hermes без rescue.

**Стало:** порог 85% для всех агентов; Hermes gate через `parse_intent`; rescue/post_verify; enrich Tech/Economist/Strategist; pytest 59 (enrich + rescue). Live re-gate — следующий шаг. **Коммит:** `6efd107`.

## 2026-06-16 — DevTools MCP: массовая рассылка send 2/2

**Сделано:** Chrome DevTools MCP — полный цикл B + live send 2 писем (сегмент «без отрасли», me@). Acceptance + `email_nurture.md`. **Коммит:** `43c7746`.

## 2026-06-16 — Live UI smoke B (массовая рассылка)

**Сделано:** Playwright `smoke_campaign_mass_ui.py` — `/email` → Массовая → отрасли → счётчик → 3 LLM → test ib@ PASS; pytest testids. MCP DevTools недоступен. **Коммит:** `f968fbe`.

## 2026-06-16 — ops: этап C SESSION_STATE + README routes

**Сделано:** ops после `78c66d4`; README `email.py` chain_type/campaign; `crud.py` products_owned. **Коммит:** `3a87e7b`.

## 2026-06-16 — Этап C: products_owned + chain_type; smoke B API

**Сделано:** поле `products_owned`, типы цепочек new/cross/upsell, nurture UI; API smoke массовой; pytest 25 (email зона). **Коммит:** `78c66d4`.

## 2026-06-13 — fix: 500 industryCatalog (неверные импорты)

**Сделано:** `$lib/api.js`, `$lib/leadsStorage.js`, `$lib/leads/leadMailingUi.js` в `industryCatalog.js`; npm build OK. **Коммит:** `3eba285`.

## 2026-06-13 — D+: чекбоксы отраслей в массовой рассылке

**Сделано:** мультивыбор `industries[]`, счётчики в API, чекбокс «без отрасли»; pytest 16. **Коммит:** `e88a41f`.

## 2026-06-13 — Этап D: отрасль (справочник и дозаполнение)

**Сделано:** `GET /api/leads/industries`, поле `industry_verified`, модалка `LeadIndustryHost`, фильтр отрасли/verified в массовой рассылке, gate nurture без отрасли; pytest 12 (industry + campaign B). **Коммит:** `df12d01`.

## 2026-06-15 — Этап B: массовая рассылка по сегменту

**Сделано:** `EmailCampaignPanel`, `preview-llm`/`test-send`, send_now, RAG маркетолог; pytest 6. **Коммит:** `e2257b4`.

## 2026-06-15 — fix навсегда: store + LeadMailingHost в layout

**Сделано:** `leadMailingUi.js`, host в `+layout.svelte`, кнопка `openLeadMailing(lead)`; pytest 2. **Коммит:** `f47dd70`.

## 2026-06-15 — fix: drawer «Рассылка» не открывался

**Сделано:** `portal.js` → body; `LeadMailingDrawer` z-100 + onclose; pytest portal 2. **Коммит:** `e440e00`.

## 2026-06-15 — Рассылка касаний с карточки лида

**Сделано:** `LeadMailingDrawer`, реестр `leadMailingTypes.js`, кнопка на `/leads/{id}`, `EmailNurturePanel` lockLead/compact, deep link `/email`; smoke `test_lead_mailing_types.py`. **Коммит:** `14678ac`.

## 2026-06-15 — Email UI этап A: точечные касания из панели

**Сделано:** `EmailNurturePanel`, API `preview-llm`/`test-send`, RAG строгий, история chains; `email_nurture.md` §A. **Коммит:** `e425c77`.

## 2026-06-15 — LLM nurture: 3 письма под продукт (MaxPatrol VM)

**Сделано:** `marketer_nurture.py`, `email_nurture_llm.py`, `POST /nurture/start-llm`; live HOCHLAND→ib@ 3 emails; `docs/modules/email_nurture.md`; PRD_MAP. **Коммит:** `da4d49f`.

## 2026-06-15 — Nurture хвост A: DevTools UI + segment batch live

**Сделано:** `smoke_email_nurture_segment_live.py`; DevTools `/ops/email` таблица chains OK; segment `Nurture Live` started=2; BACKLOG LLM-тексты. **Коммит:** `6f69239`.

## 2026-06-15 — Nurture 20 касаний live + персонализация

**Сделано:** `email_nurture_plan.py` (шаблоны маркетолога, `{{company}}`/`{{contact}}`); `start-segment`, `process-due`; `smoke_email_nurture_live.py` — лид → 1-е письмо на ib@; pytest 14 passed; acceptance §Nurture. **Коммит:** `1a2edd7`.

## 2026-06-15 — Email live полный (FAQ real + UI)

**Сделано:** `smoke_email_faq_live.py`; me@ SMTP; FAQ ib@→me@ live; fix `email_thread_list` max(bool); DevTools `/email` `/ops/email` `/ops/email-agents`. **Коммит:** `82a5803`.

## 2026-06-13 — me@agneko.am: хост Яндекс (MX)

**Сделано:** `me@` на `imap.yandex.com` (MX → Yandex, не Hostland webmail); connect OK; `.env.example` комментарий; ISSUES закрыта. **Коммит:** `6ff7f4e`.

## 2026-06-13 — me@ диагностика (Hostland ложный след)

**Сделано:** `EMAIL_ACCOUNT_N_APP_PASSWORD`; `email_tls` insecure SSL; relink orphans `limit` + lead index; `smoke_email_faq.py`, `probe_email_host.py`; connect 400 с явным auth hint; pytest 21; me@ — IMAP Invalid login (креды cPanel). **Коммит:** `77419d9`.

## 2026-06-15 — Ф3 Email live smoke

**Сделано:** ib@ IMAP+SMTP OK; me@ connect 400; `smoke_email_smtp_send.py`; acceptance §Live. **Коммит:** `b207622`.

## 2026-06-15 — Ф3 Email: автономия

**Сделано:** FAQ autoreply по Ops-правилам; рассылки по сегменту; nurture 20 касаний + scheduler; autolink по домену; pytest 17 passed; `F3_EMAIL_AUTONOMY_ACCEPTANCE.md`; MAP Email `[x]`. **Коммит:** `9a3be09`.

## 2026-06-15 — Ф3 Voice: апрув, revise, history

**Сделано:** голос «да/нет» на approve-модалке; «короче» → revise-draft; история на `/ops/voice`; `approval_followup.py`, `revise_draft.py`, `voiceFollowup.js`; pytest 27 passed; `F3_VOICE_APPROVAL_ACCEPTANCE.md`; MAP Voice `[x]`. **Коммит:** `cad831c`.

## 2026-06-14 — Ф2 §9: enrich голос

**Сделано:** `enrich_lead` voice — rescue, `fetch_enrich_preview`, modal `apply/reject`, `voiceEnrichApply.js`; pytest 21 passed; `LEADS_ENRICH_VOICE_ACCEPTANCE.md`; MAP §9 п.2 `[x]`. **Коммит:** `cb0de76`.

## 2026-06-14 — Ф2 §8: Лидоген + голос

**Сделано:** navigate-only leadgen voice (`generate_lead`, `find_leads_portrait`, `cluster_company`); `voiceLeadgenContext` + autorun на `/leadgen`; `GET /won-portrait` из БД; lookalike won + `lookalike-import`; pytest 23 passed; DevTools autorun; `LEADGEN_VOICE_F2_ACCEPTANCE.md`; MAP §8 `[x]`. **Коммит:** `0c3ae08`.

## 2026-06-14 — Ф2 §7: Тендеры + голос

**Сделано:** `POST /evaluate` с document_text; `search_tenders`/`list_tenders` voice; `linked_lead_id` + link/create-lead API; UI `/tenders` + `tenderLink` на карточке лида; pytest 20 passed; `TENDERS_VOICE_ACCEPTANCE.md`; MAP §7 `[x]`. **Коммит:** `829d340`.

## 2026-06-14 — Ф2 §6: Аналитика + голос

**Сделано:** фильтры `period`/`source` в `analytics_metrics` + API summary/export; `conversionBySource`; voice navigate с query (`view=funnel|cycle|conversion`); UI `/leads/analytics` с контекстом и подсветкой; pytest 47 passed; `ANALYTICS_VOICE_ACCEPTANCE.md`; MAP §6 `[x]`. **Коммит:** `3911386`.

## 2026-06-14 — Ф2 §5 доп: Hermes prompt versioning

**Сделано:** версии Hermes в `hermes_prompt_store` + API `/hermes/prompt/versions/*`; UI `/ops/intents/improve`; `PromptVersionPanel` через `promptBasePath`; compare-роут до `{version_id}`; pytest 27 passed. **Коммит:** `60a045b`.

## 2026-06-14 — Ф2 §5: версионирование промптов в Ops

**Сделано:** `agent_prompt_versions.py`; API versions/restore/compare; UI история+откат+diff на `/ops/agents`; pytest 26 passed; `OPS_PROMPT_VERSIONING_ACCEPTANCE.md`; MAP §5 п.422–424 `[x]`. **Коммит:** `a883410`.

## 2026-06-14 — RAG хвост BACKLOG + §9 enrich на карточке

**Сделано:** `qa_structure.py` (`RAG_AUTO_STRUCTURE_LLM`); async `collect_deal_facts` (`RAG_DIALOGUE_LLM`); `fetch_urls_from_hits`/`page_fetch`; кнопка «Обогатить» `/leads/{id}`; smoke+cache; pytest 31 passed; `RAG_BACKLOG_TAIL_CLOSED.md`, `LEADS_CARD_ENRICH_ACCEPTANCE.md`; MAP §9 `[x]`. **Не закрыто:** quality gate ≥85% — **Ф3**. **Коммит:** `934a84f`.

## 2026-06-14 — Ф2 §4 п.4: кэш enrich + закрытие §4

**Сделано:** `enrich_cache.py`; `enrich_lead(force)`; API/UI force + бейдж кэша; GET/DELETE cache расширен; pytest 14 passed; `SEARCH_ENRICH_CACHE_ACCEPTANCE.md`; MAP п.418 `[x]`; **§4 «Поиск → RAG авто» закрыт (п.1–4).** **Коммит:** `9dcf749`.

## 2026-06-14 — Ф2 §4 п.3: «Сохранить в базу» везде в поиске

**Сделано:** `SearchSaveRagBar` + `saveToRagFromHits.js` на вкладках company/free/prospect/enrich/agent; `search_hits.py`; smoke обновлён; pytest 7 passed; `SEARCH_SAVE_EVERYWHERE_ACCEPTANCE.md`; MAP п.417 `[x]`. **Коммит:** `41c8f55`.

## 2026-06-14 — Ф2 §4 п.2: факты диалога агента → RAG

**Сделано:** `dialogue_facts.py`; `POST /ingest-dialogue`; авто `RAG_DIALOGUE_AUTO_INGEST` на ops run + voice fanout; UI «💾 В RAG»; voice save_to_rag → agent collection; pytest 7 passed; `AGENT_DIALOGUE_RAG_ACCEPTANCE.md`; MAP п.416 `[x]`.

## 2026-06-14 — Quality gate: baseline + Ф3 тюнинг в BACKLOG

**Сделано:** full gate 2026-06-14 зафиксирован (Hermes 72.2%, Tech 60%, overall fail); `AGENTS_GATE_TUNING_BASELINE.md`; BACKLOG «тюнинг ≥85% все» → Ф3; PRD_MAP §Агенты + §Ф3 Self-improvement. Тюнинг **не** в этом шаге. **Коммит:** `f5d4266`.

## 2026-06-14 — Ф2 §4 п.1: авто-чанки Search→RAG

**Сделано:** relevance score + `RAG_AUTO_RELEVANCE_THRESHOLD`; `POST /auto-ingest-rag`; UI автовыбор на `/search`; pytest 10 passed; `SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md`; MAP п.414→п.1 `[x]`. **Коммит:** `c1302fc`.

## 2026-06-14 — Ф2 §3 п.407: голосовые команды email

**Сделано:** list_emails/write_email/send_email E2E; marketer в оркестраторе; voiceEmailContext на `/email`; modal send→approve; pytest 12+ passed; `EMAIL_VOICE_COMMANDS_ACCEPTANCE.md`; MAP п.407 `[x]`; **§3 Email-агент закрыт.**

## 2026-06-14 — Ф2 §3 п.406: апрув и отправка email

**Сделано:** EmailApproveModal (reply/compose); voice send_email approve + thread_id reply; pytest 8 passed; `EMAIL_APPROVE_SEND_ACCEPTANCE.md`; MAP п.406 `[x]`.

## 2026-06-14 — Ф2 §3 п.405: анализ типа письма + черновик

**Сделано:** `POST /api/email/threads/{id}/analyze`; `email_thread_analyze.py` + `email_category_labels.py`; UI «Анализ + черновик» на `/email`; pytest 3+12 email zone passed; `EMAIL_DRAFT_ANALYZE_ACCEPTANCE.md`; MAP п.405 `[x]`.

## 2026-06-14 — email cleanup: legacy route + BACKLOG me@

**Сделано:** удалён `email/[mailbox].svelte`; BACKLOG `me@agneko.am` закрыт; PRD_MAP инфра п.5 ✅; pytest integration 9 passed.

## 2026-06-14 — Ф2 §3 п.404: список `/email`

**Сделано:** `emailListLogic.js`; enriched `GET /threads`; `/email` UI (фильтры, sync bar, apiFetch); pytest 13 passed; `EMAIL_LIST_PAGE_ACCEPTANCE.md`; MAP п.404 `[x]`.

## 2026-06-14 — Ф2 §3 п.403: фоновый синк входящих

**Сделано:** `email_sync/background.py` + `sync_all.py`; poll loop в `main.py`; `GET /api/email/sync/status`; `EMAIL_AUTO_SYNC_MINUTES`; pytest 19 passed; `EMAIL_BACKGROUND_SYNC_ACCEPTANCE.md`; MAP п.403 `[x]`.

## 2026-06-14 — Ф2 §3 п.402: IMAP/SMTP credentials в env

**Сделано:** `core/email_config.py`; `services/email_bootstrap.py`; `GET /api/email/config/status`; `POST /api/email/bootstrap-from-env`; smoke на общем конфиге; pytest 20 passed; `EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md`; MAP п.402 `[x]`.

## 2026-06-14 — хвост B/C: lookalike POST после voice approve

**Сделано:** `POST /api/leads/lookalike-import`; `services/lookalike_import.py`; frontend `lookalikeImport.js`; VoiceActionHost «Добавить»; BACKLOG строка снята; pytest 8 passed.

## 2026-06-14 — Ф2 §2 п.396: сценарий похожие клиенты · §2 закрыт

**Сделано:** `find_similar_clients`; similar_context + search_by_portrait; voice modal similar_leads; pytest 6 passed; `SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md`; MAP п.396 `[x]`; **§2 Оркестрация — все пункты `[x]`.**

## 2026-06-14 — Ф2 §2 п.395: сценарий еженедельный отчёт

**Сделано:** `weekly_report`; report_context; analyst/economist/marketer/strategist; voice modal KPI; VoiceActionHost; pytest 7 passed; `SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md`; MAP п.395 `[x]`.

## 2026-06-14 — Ф2 §2 п.394: сценарий оценка тендера (тех + эконом)

**Сделано:** `evaluate_tender`; tender_context; economist/tech/strategist; voice modal; pytest; `SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md`; MAP п.394 `[x]`.

## 2026-06-14 — Ф2 §2 п.393: сценарий анализ + письмо

**Сделано:** `analyze_and_email`; scenarios/analysis_email.py; rescue/supervisor/modal; pytest 48 passed; `SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md`; MAP п.393 `[x]`.

## 2026-06-14 — Ф2 §2 п.3: синтез в один ответ → модалка

**Сделано:** `voice/synthesis.py`; fanout+strategist → modal; `payload.synthesis`; VoiceActionHost «Решение»; pytest 44 passed; `FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md`; MAP п.392 `[x]`.

## 2026-06-14 — Ф2 §2 п.2: параллельный fanout 2+ агентов

**Сделано:** `agents/fanout_parallel.py`; `FanoutPlan.parallel_fanout`; Hermes `parallel` → orchestrator; leadgen pre-fanout; pytest 20 passed; `FANOUT_PARALLEL_ACCEPTANCE.md`; MAP п.391 `[x]`.

## 2026-06-14 — Ф2 §2 п.1: LangGraph supervisor (выборочный fanout)

**Сделано:** `agents/supervisor.py`, `agents/graph.py`; orchestrator + pipeline `hermes_agents`; pytest 15 passed; `FANOUT_SUPERVISOR_ACCEPTANCE.md`.

## 2026-06-14 — Ф2 Voice Layer §1: UI + rescue eval (закрыт)

**Сделано:** фронт voice_action (modal/navigate/filter/minScore/approve); `voiceApproveHandlers.js`; eval `cases_modules.jsonl`; `smoke_voice_layer.py` 72 passed; `VOICE_LAYER_ACCEPTANCE.md`; MAP §1 `[x]`. Live LLM eval модулей — опционально в BACKLOG 🟢.

## 2026-06-13 — Ф2 Voice Layer §1: Hermes module + intent + ui_action

**Сделано:** контракт `module_contract.py`; промпт/rescue/slot_normalize; `voice_action` + `rag_context`; pipeline; pytest 47+10; `smoke_hermes_modules.py`; `HERMES_MODULES_ACCEPTANCE.md`. Модули: email, search, analytics, agents, rag.

## 2026-06-13 — Ops: упаковка `docs/operations/` по фазам

**Сделано:** `session/`, `baselines/`, `phase1/{домен}/`, `phase2/agents/`, `debt/`; `operations/README.md`. Коммиты: `036fd61`, `f4cf977`.

## 2026-06-13 — Переход Ф1 → Ф2 (handoff)

**Сделано:** решение: DoD Ф1 6/6 ✅, идём в Ф2; `PHASE2_ENTRY.md` для следующего агента; HANDOFF + MAP § Ф2 обновлены. Коммиты: `db8960e`, `4592830`. Push **не** делали — ждём go. Незакоммичено: только runtime `backend/data/*`.

## 2026-06-13 — Agents quality gates: шаг 7 (pytest, без live LLM)

**Сделано:** pytest gate block 34 passed — config/пороги, delta was→became, артефакты JSON, cases 36+15×5, API gate, acceptance_sync, CLI `--check-only`/`--log-file`. Live LLM gate **не** в CI. Fix cp1251 stdout (`_emit`, gaps `!=`, JSON ensure_ascii).

## 2026-06-13 — Gate CLI: --log-file + ASCII progress

**Сделано:** `run_agents_quality_gate.py --log-file` (line-buffered); `set_gate_logger` в `gate.py`; warmup/agent лог в файл; ASCII вместо `→`/`…` (Windows cp1251); sort артефактов по имени; pytest `tests/scripts/test_run_agents_quality_gate.py`.

## 2026-06-13 — Fix: Vite 500 gate delta {@const}

**Сделано:** `{@const}` перенесён под `{#if}`/`{#each}` в `AgentGatePanel.svelte` и `insights/+page.svelte`. Коммит: `273aca8`.

## 2026-06-13 — Agents quality gates: петля обучения шаг 6

**Сделано:** `gate_delta.py` (было % → стало % в JSON и API); `/ops/tuning` — «Импорт failed из gate»; дельта на карточках eval + insights; ссылки eval↔tuning. Коммит: `7be7bdb`. pytest gate 13.

## 2026-06-13 — Agents quality gates: UI eval+insights финал

**Сделано:** вкладки Hermes/gate на `/ops/intents/eval`; скачивание JSON; режимы прогона + лимиты; default dataset `eval-failed-gate`; bulk failed; блок обучения; insights pass rate grid + empty hint; API download/ensure-dataset/bulk; pytest 15; Puppeteer smoke eval. Коммит: `596d2e1`.

## 2026-06-12 — Agents quality gates: UI eval + insights (шаг 5)

**Сделано:** AgentGatePanel на `/ops/intents/eval` (вкладки, pass rate, в датасет); insights gate; API latest/run/failed-to-dataset; BACKLOG что не вышло на 3–4.

## 2026-06-12 — Agents quality gates: acceptance sync + дыры MAP (шаг 4)

**Сделано:** `acceptance_sync.py`, `--write-acceptance`, `--agents-only`, маркеры GATE_STATUS/GAPS; BACKLOG хвост шага 3; MAP 🔲 + список дыр; live прогон 5 агентов запущен.

## 2026-06-12 — Agents quality gates: прогон Ollama + gate script/API (шаг 3)

**Сделано:** `run_agents_quality_gate.py`, `core/agent_eval/gate.py`, `POST/GET /api/ops/eval/agents-gate`; Ollama check+warmup; timeout 600s; smoke live (Ollama hermes3) — пороги не пройдены на smoke.

## 2026-06-12 — Agents quality gates: eval-кейсы 6 агентов (шаг 2)

**Сделано:** `eval/agents/*.jsonl` (15×5), Hermes 36 в `cases.jsonl`; `core/agent_eval` (load + score); `seed_agent_eval_cases.py`; pytest smoke 12 тестов.

## 2026-06-12 — Agents quality gates: рамка + карта обучения (шаг 0–1)

**Сделано:** пороги Hermes 85%/30, агенты 75%/15; `phase2/agents/AGENTS_LEARNING_MAP.md`, `phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md`; PRD_MAP/BACKLOG/langgraph — eval через Ollama, `[x]` только после live gate.

## 2026-06-12 — Coverage hygiene: policy + smoke + CI cov log

**Сделано:** `PR_CHECKLIST.md` (тест на фичу); 16 smoke-тестов leadgen/email_sync/integrations; CI pytest печатает `TOTAL %` без fail-under; cov **51.7%** (+0.3).

## 2026-06-12 — CI: rescue eval-007 + branch protection

**Было:** GitHub Actions run #2 — оба job красные: `eval-007` «создай задачу… из лида» → `list_leads` (на CI нет `.env`, fastpath выкл).  
**Стало:** `rescue.py` — `create_task` раньше city-filter `list_leads`; `HERMES_ENABLE_FASTPATH=0` в CI; push; required checks на `main`.

## 2026-06-11 — fix: pytest warnings (email + starlette)

**Было:** 5 warnings — email-тесты `return bool`, StarletteDeprecationWarning httpx testclient.  
**Стало:** `test_email_integration.py` на `assert`; `filterwarnings` в `pytest.ini`; 500 passed без warnings.

## 2026-06-11 — fix: cryptography в requirements + venv/docs

**Сделано:** `cryptography` в `requirements.txt` (venv падал на `core/crypto`); доки/CI — `python -m pytest`, venv в SETUP/README/COVERAGE/CI_BASELINE.

## 2026-06-11 — CI: pytest + smoke на push/PR

**Сделано:** `.github/workflows/ci.yml` — jobs `pytest (sqlite)` и `smoke (ops·leads·voice)`; `scripts/ci_smoke.py`; `CI_BASELINE.md`; branch protection — вручную в GitHub.

## 2026-06-11 — Coverage: pytest-cov baseline 51.4%

**Сделано:** `requirements-dev.txt` (pytest-cov); `backend/.coveragerc`; команда `pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing`; baseline **51.4%** в `COVERAGE_BASELINE.md`; MAP ориентиры Ф2/Ф3; маркер `live_eval` (исключён из регрессии); фиксы: voice WS без `str(e)`, RAG stubs не ломают suite, brave backoff reset.

## 2026-06-11 — Email: fix дат IMAP + inbox filter

**Сделано:** `_parse_msg_date` для datetime; repair 362 битых дат по UID; inbox показывает все категории (не только inbound); DevTools = Yandex «Сегодня».

## 2026-06-11 — Email: кнопка Sync + POST /api/email/sync

**Сделано:** отдельная синхронизация без пароля; IMAP SINCE `last_synced_at−1д`; UI «🔄 Синхронизировать»; `smoke_email_sync.py`; 7 pytest; DevTools OK.

## 2026-06-11 — Email: live connect ib@agneko.com (Яндекс IMAP)

**Сделано:** `emailStorage.js` → `apiFetch`; лимит `EMAIL_IMAP_FETCH_LIMIT`; `smoke_email_connect.py`; mock pytest; DevTools `/email` 504 треда; `EMAIL_CONNECT_ACCEPTANCE.md`. **Хвост:** `me@agneko.am` на `mail.agneko.am` — отдельный пароль.

## 2026-06-11 — Ops: baseline Ф1 formalized

**Сделано:** аудит `/ops` (реальные API, без UI-моков); `smoke_ops_baseline.py` 33 pytest; DevTools `/ops`, `/ops/agents`; `OPS_BASELINE_ACCEPTANCE.md`.

## 2026-06-11 — Тендеры: PDF extract live smoke + curl в acceptance

**Сделано:** `smoke_tender_pdf_extract.py` (ключ из корневого `.env`); в `smoke_tenders_baseline`; PowerShell/curl гайд в `TENDERS_BASELINE_ACCEPTANCE.md`.

## 2026-06-11 — Аналитика: baseline Ф1 formalized

**Сделано:** KPI на `/leads/analytics` (воронка, конверсия, чек, цикл); API summary/export; убран mock `/analytics`; 10 pytest; DevTools + Puppeteer; `ANALYTICS_BASELINE_ACCEPTANCE.md`.

## 2026-06-11 — Тендеры: apiFetch + DevTools PDF UI OK

**Сделано:** tenderApi на apiFetch (X-API-Key); DevTools: upload PDF → «✓ текст готов · 23 симв.»; .env.example SMARTCRM_API_KEY.

## 2026-06-11 — Тендеры: PDF → текст в analyze

**Сделано:** `POST /documents/extract`, UI загрузка → `document_text`, pytest + fixture `sample_tz.pdf`.

## 2026-06-11 — Тендеры: закрыты хвосты п.2–5, п.7

**Сделано:** Serper/Tavily в `/search`; `tender_saved` + Мои/Архив; `POST /analyze` LLM; Gosplan UI; fix 400; тесты saved/web.

## 2026-06-11 — Тендеры: Ф1 baseline formalized

**Сделано:** таблица MAP, `TENDERS_BASELINE_ACCEPTANCE.md`, `smoke_tenders_baseline.py`, `test_tenders_baseline_smoke.py`; фикс HTTP 400→500 на `/api/tenders/search`; BACKLOG хвосты (Мои/Архив MOCK, Gosplan tail).

## 2026-06-11 — PRD/MAP: синхрон после ревью доков

**Сделано:** `PRD.md` — навигация, Ф1 ✅, P2→Ф1 drift; `PRD_MAP.md` — TOC, DoD Ф2, сценарии Ф2, coverage ориентир, сводка голос/лидоген; `LEADGEN_VOICE_ACCEPTANCE.md`.

## 2026-06-11 — Голос: mic E2E + Ф1 DoD закрыт + Ф2 leadgen voice smoke

**Сделано:** `test_voice_mic_ws_e2e.py`, `smoke_voice_mic_e2e.py`, dev `voice-simulate-mic`, `test_leadgen_voice_ws.py`; `VOICE_MIC_E2E_ACCEPTANCE.md`; MAP/BACKLOG DoD 6/6.

## 2026-06-10 — PRD_MAP: выровнен (финал MAP-doc)

**Сделано:** «Поиск и RAG» — одна таблица без дублей; шапки «чеклист = таблица» в Лиды/Баллы/Поиск; пометка в шапке MAP. MAP-doc pass закрыт.

## 2026-06-10 — PRD_MAP: агенты, безопасность, инфра прод, coverage

**Сделано:** quality gates агентов (ссылки ops/eval, HERMES_*); таблицы безопасность/инфра прод; блок coverage + dev-gates; `langgraph.md` одна секция.

## 2026-06-10 — PRD_MAP: порядок Фазы 2

**Сделано:** блок «Порядок Фазы 2» — очередь 1–9, фундамент/важно/можно позже; §1 Voice ≠ лиды Ф1; процесс `go` по номеру; HANDOFF ссылка.

## 2026-06-10 — PRD_MAP: бизнес-сценарии Фазы 1

**Сделано:** 7 сценариев «менеджер может…» с ✅/⚠️ и привязкой к блокам MAP; процесс «сценарий → техтаблица»; без дубля PRD.

## 2026-06-10 — PRD_MAP: Definition of Done — Фаза 1

**Сделано:** 6 критериев DoD фазы (таблица); ссылка на dev-gates = DoD пункта; п.5 голос код ✅ / E2E ⚠️; п.6 «ок в Ф2»; вердикт 4/6.

## 2026-06-10 — PRD_MAP: статусы ⚠️ голос + сводка

**Сделано:** легенда `[x]` vs ⚠️; колонка «Статус» в таблице «Голос → лиды»; сводка «частично ⚠️ E2E микрофон»; процесс снятия ⚠️ в BACKLOG; README одна строка.

## 2026-06-10 — PRD_MAP: хвост Ф1 → только BACKLOG

**Сделано:** устаревший блок «Хвост Фазы 1» (Hermes/voice_action 🔴) заменён на указатель «Открытые хвосты Ф1»; ссылки на BACKLOG § ручная работа / голос; HANDOFF без дубля таблицы; BACKLOG синхрон (п.98, инфра-триггер).

## 2026-06-10 — PRD_MAP: выравнивание чеклистов и фаз

**Сделано:** легенда ✅/⚠️/🔲; DoD Фаза 1 + сценарии; убраны дубли списков (таблицы = истина); голос ⚠️ E2E; хвост Ф1 → `BACKLOG`; порядок Ф2; блоки безопасность / инфра прод / quality gates агентов; сводка модулей синхронизирована.

**Зачем:** одна истина для агентов; видно к чему вернуться до старта Ф2.

## 2026-06-10 — Leadgen: автосейв в портрете и кластере

**Сделано:** `persist_autosave.py`; `save_to_crm` в `/portrait` и `/cluster`; UI чекбокс для всех режимов; `crm_saved[]`; 6 pytest.

## 2026-06-10 — Leadgen: dedup по ИНН при сохранении в CRM

**Сделано:** `persist_card.py` + update по ИНН в `_save_to_crm`; `crm_lead_created` в ответе; UI «Обновлён»; 4 pytest dedup.

## 2026-06-10 — Leadgen: автосейв в CRM + commit-ops override

**Сделано:** `crm_threshold.py`, порог из конфига; 10 pytest; `smoke_leadgen_autosave.py`; UI testid; DevTools E2E скор 84 → лид #3187; `LEADGEN_AUTOSAVE_ACCEPTANCE.md`; усилен `commit-ops`/`AGENTS.md` (override глобального User Rule); удалены `CURSOR_USER_RULES_*.md`.

## 2026-06-10 — Leadgen: кластер / холдинг (перепроход)

**Сделано:** API-тесты, integration mock, `smoke_leadgen_cluster.py`, testid UI, DevTools E2E Хохланд 4 субъекта, `LEADGEN_CLUSTER_ACCEPTANCE.md`; portrait Groq review → BACKLOG Ф2.

## 2026-06-10 — Leadgen portrait: progress UI + Chrome DevTools MCP E2E

**Сделано:** `portraitProgress.js` — стадии/таймер/полоса при поиске по портрету; pytest smoke; DevTools E2E через **user-chrome-devtools** (POST 200, progress виден).

**Зачем:** UX при долгом POST; канонический MCP-прогон вместо cursor-ide-browser.

## 2026-06-10 — Leadgen: хвост ИНН + DevTools portrait E2E

**Сделано:** канон `leadgen/inn_constants.py`, импорты в smoke/API-тестах, docs на Хохланд (без Сбера в leadgen), `asyncio.run` в test_leadgen, DevTools E2E portrait (cursor-ide-browser), `test_inn_constants.py`.

**Зачем:** один источник live-ИНН, acceptance без drift, warnings pytest убраны.

## 2026-06-10 — Leadgen: развод ИНН мок vs live (эталон портрета)

**Сделано:** `inn_constants.py` — мок `7707070010` (ТехноСофт), live `5040048921` (Хохланд); убран `7736207543` (реальный Яндекс в ЕГРЮЛ); обновлены фикстуры, smoke, UI placeholders; `LEADGEN_INN_FIX.md`; smoke portrait live OK (3 кандидата).

**Зачем:** «странный эталон» — не баг Checko, а конфликт тестовых данных с ЕГРЮЛ.

## 2026-06-10 — Убран конфликт «commit по запросу» в HANDOFF

**Сделано:** HANDOFF — канон `commit-ops`; `check_rules_commit_conflict.py` — EN-паттерны (`commit только по явному`, `go commit`); `CURSOR_USER_RULES_SNIPPET.md` — override для Settings.

**Зачем:** агенты читали HANDOFF и ждали явного запроса на commit вопреки `smartcrm-commit-ops.mdc`.

## 2026-06-09 — Pre-commit: SESSION_STATE без отложенного коммита

**Сделано:** `session_state_validate.py`, git pre-commit hook, `install_git_hooks.ps1/.sh`, интеграция в `check_agent_step.py` и `smartcrm-commit-ops.mdc`.

**Зачем:** git pre-commit блокирует журнал SESSION_STATE с отложенным коммитом или `done` без хеша.

## 2026-06-09 — Leadgen: поиск по портрету (перепроход)

**Сделано:** API `/portrait` только с `reference_inn`, фиксы `re`/`_parse_json_safe`, select лида → критерии, smoke + DevTools, `LEADGEN_PORTRAIT_ACCEPTANCE.md`.

**Зачем:** PRD_MAP перепроход portrait: эталон → Checko/Tavily/Brave → match + LLM review.

## 2026-06-08 — Leadgen: анализ по ИНН/названию (перепроход)

**Сделано:** API-тесты `/api/leadgen/analyze`, smoke `smoke_leadgen_inn_analysis.py`, fix нормализации `website` (без двойного https), testid на `/leadgen` direct, DevTools E2E Сбербанк ИНН, `LEADGEN_INN_ANALYSIS_ACCEPTANCE.md`.

**Зачем:** PRD_MAP перепроход с проверкой пайплайна Checko → gather → агенты и поисковиков.

## Как писать запись

```
## [дата] — [название] (`go` | `hotfix` | процесс)

**Сделано:** …
**Зачем / Причина:** …
```

| Тип | Маркер | Пример |
|-----|--------|--------|
| Фича | `go` | P1 балльная воронка |
| Hotfix | `hotfix` | TCP обрывы Postgres |
| Процесс | без маркера | Реорганизация `docs/` |

**Правило:** изменение кода или архитектуры без записи здесь = не зафиксировано для следующей сессии.

## [2026-06-09] — Iron commit: ответ только после git commit (процесс)

**Сделано:** `commit-ops` — ответ только после commit; `check_agent_step` FAIL на done без хеша; зачистка SESSION_STATE; коммит leadgen ИНН.

**Зачем:** агенты закрывали шаг без commit в git.

## [2026-06-08] — Правила: хвост прогона A / B / C (процесс)

**Сделано:** обязательные три блока после commit+ops — A (из плана не сделано), B (BACKLOG в прогоне), C (доп. починки); `SESSION_STATE` + ответ агента; `check_agent_step.py` FAIL без A/B/C.

**Зачем:** агент не скрывает незакрытый scope, отложенное и побочные задачи.

## [2026-06-08] — Правила: только безусловный commit+ops (процесс)

**Сделано:** зачистка всех формулировок отложенного коммита в `.mdc`, `AGENTS.md`, ops-журналах; `check_rules_commit_conflict.py` сканирует `SESSION_STATE`; канон — один: `git commit` при закрытии шага.

**Зачем:** агенты не откладывали коммит и не спрашивали разрешение.

## [2026-06-09] — PRD_MAP Ф2: enrich cache + кнопка на карточке (план)

**Сделано:** `PRD_MAP.md` §4 кэш enrich, §9 кнопка `/leads/{id}`; BACKLOG + acceptance ссылки.

## [2026-06-09] — enrich-lead усиление: Brave, Checko, CRM apply (`go`)

**Сделано:** `brave_limit.py` кэш+semaphore; `enrich_sources.py` Checko/ИНН, таргет LinkedIn/ЛПР, scrape сайта; UI выбор лида + PATCH; 28 pytest.

## [2026-06-09] — enrich-lead smoke из поиска (`go`)

**Сделано:** фикс Brave в `enrich_lead`, валидация `lead.company`, фильтр null из LLM, только веб-провайдеры; 8 pytest + `smoke_search_enrich_lead.py`; DevTools enrich Сбербанк; `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` с тонкими местами.

**Зачем:** закрыть последний пункт блока «Поиск и RAG» — live E2E обогащения лида.

## [2026-06-08] — RAG п.5: «сохранить в базу» из /search (`go`)

**Сделано:** проброс `source_url` в метаданные чанков при `ingest-batch`; `total_chunks` в ответе save; UI «✓ Сохранить в базу» + testid; 6 pytest; `smoke_rag_save_from_search.py`; DevTools E2E (поиск → превью → save); `SEARCH_RAG_SAVE_ACCEPTANCE.md`.

**Зачем:** агенты при retrieval видят URL источника; flow из поиска в Chroma работает без ручных обходных путей.

**Не в scope:** enrich-lead smoke, авто-чанки Ф2, full-page fetch по URL.

## [2026-06-08] — RAG п.4: upload PDF/текста в /rag (`go`)

**Сделано:** pytest ingest/upload/preview; `smoke_rag_upload.py`; testid на UI; DevTools ручной текст + живые PDF в списке; `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`.

**Не в scope:** save из `/search` (п.5), enrich smoke, авто-чанки.

## [2026-06-08] — RAG п.3: Chroma RAG + агенты перепроход (`go`)

**Сделано:** `test_rag_api.py`, `smoke_rag_chroma.py` (1592 чанка, by_agent); `/rag` → apiFetch; `SEARCH_CHROMA_ACCEPTANCE.md` «было/стало»; PRD_MAP п.3 ✅.

**Не в scope п.3:** полный E2E upload PDF (п.4), save из поиска (п.5), enrich smoke, pgvector.

**Зачем:** подтвердить живую базу и фильтр `for_agent`, не только галочку в MAP.

## [2026-06-08] — RAG п.2: 6 режимов поиска перепроход (`go`)

**Сделано:** pytest API 6 эндпоинтов + unit modes; `smoke_search_modes.py`; `data-testid` на 6 табах/submit; DevTools табы + free live; `SEARCH_MODES_ACCEPTANCE.md` с блоком «НЕ СДАЛИ»; PRD_MAP п.2 ✅.

**Не в scope п.2 (явно):** Chroma/p.3, `/rag` upload/p.4, save button/p.5, enrich-lead live smoke, авто-чанки Ф2.

**Зачем:** закрыть п.2 по шаблону п.1 — автотесты + acceptance + честный хвост.

## [2026-06-08] — RAG п.1 хвост: apiFetch + live smoke + UI (`go`)

**Сделано:** `search/+page.svelte` — все `fetch` → `apiFetch`/`apiPost`; `smoke_search_providers.py` — `_load_env()` для live probe; DevTools полный UI-клик; `SEARCH_PROVIDERS_ACCEPTANCE.md` таблица «сделано/проверено»; `BACKLOG.md` — хвост п.2–5 на потом.

**Зачем:** дожать п.1 до acceptance-уровня голосового блока (не только API evaluate_script).

## [2026-06-08] — RAG п.1 Serper + Brave + Tavily перепроход (`go`)

**Сделано:** фикс кэша `company_search.py`; pytest моки провайдеров + API; `smoke_search_providers.py`; DevTools `/search` live run; `SEARCH_PROVIDERS_ACCEPTANCE.md`; PRD_MAP перепроход.

**Зачем:** закрыть первый пункт блока «Поиск и RAG» по тому же шаблону, что голос/Whisper.

## [2026-06-08] — BACKLOG: ручная работа по фазам (`go`)

**Сделано:** секция «👤 Ручная работа (только ты)» в `BACKLOG.md` — таблица Фаза MAP / блок PRD / пункт / чеклист; критерий 100% закрытия Ф1 голоса; обновлены «Активный хвост» и «Сводный хвост».

**Зачем:** не потерять единственный открытый шаг (микрофон E2E) и spot-check перед Фазой 2.

## [2026-06-08] — хвост BACKLOG «Голос → лиды» #2–#11 (`go`)

**Сделано:** `add_communication` (Hermes + список лидов); `stage_fuzzy` + crm_settings; чипы industry/city; индикатор fanout в layout; `/health/whisper?ping=1`; Pydantic `@field_validator` в `email.py`; eval-034–036; фикс eval-003/020 rescue; `test_voice_approve_ui.py`; `smoke_hermes_leads_live.py`; `VOICE_LEADS_TAIL_ACCEPTANCE.md`.

**Зачем:** закрыть теххвост блока агентом; E2E микрофон остаётся на пользователе.

## [2026-06-08] — смоук голосовых сценариев, блок «Голос → лиды» (`go`)

**Сделано:** `test_voice_lead_scenarios.py` S01–S09, `smoke_voice_lead_scenarios.py` (47 pytest + chain); DevTools API/WS на :5174; `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md`; BACKLOG сводный хвост.

**Зачем:** PRD_MAP п.5 + закрытие базового голосового контура по лидам.

## [2026-06-08] — полные интенты лидов (`go`)

**Сделано:** `analyze_lead`, `lead_history`, фильтры `stage`/`industry`/`city`; `lead_context.py`, `lead_list_view.py`; фронт фильтры + модалка истории; 34 pytest `smoke_hermes_leads_full.py`.

**Зачем:** PRD_MAP п.4 — голос покрывает аналитику, историю и умные фильтры списка.

## [2026-06-08] — voice_action UI (`go`)

**Сделано:** бэкенд `voice/voice_action.py` + WS `type: voice_action`; фронт `VoiceActionHost`, stores navigate/filter/modal/approve; delete через апрув; 8 pytest + `smoke_voice_action.py`; `VOICE_ACTION_ACCEPTANCE.md`.

**Зачем:** PRD_MAP п.3 — голос даёт UI-реакции, не только toast.

## Связь с другими ops-доками

```
CHANGELOG.md     — что сделано (этот файл)
SESSION_STATE.md — что делается сейчас
HANDOFF.md       — передача следующей сессии
ISSUES.md        — что сломано
BACKLOG.md       — отложено по PRD_MAP
```

**Агент:** старт → читает CHANGELOG (контекст) → после шага с `go` → новая запись + SESSION_STATE.

## Хронология (сводка)

| Период | Главное |
|--------|---------|
| 2026-05-03 | Аудит доков, операционные журналы |
| 2026-05-04 | Балльная воронка P1–P3, hotfix Postgres/ORM |
| 2026-06-07 | PRD v2/MAP, docs-реорг, P6 сплиты, smartcrm-правила |
| 2026-06-08 | Перепроход «Лиды» п.1–12, балльная воронка смоук, commit+ops канон |

## Статус продукта (снимок)

| Область | Статус |
|---------|--------|
| P1–P3 балльная воронка | ✅ в коде |
| Блок «Лиды» PRD_MAP | ✅ acceptance |
| Docs / процесс агента | ✅ smartcrm-*.mdc |
| Voice Layer полный | 🔲 хвост Ф1 |
| Email-агент | 🔲 Фаза 2 |
| Официальный старт Фазы 2 | 🔲 ждёт `go` после закрытия хвоста Ф1 |

---

## 2026-06-08 — PRD_NOTES §CHANGELOG → шапка операционного журнала

**Сделано:** роль, формат записей, типы (`go`/hotfix/процесс), связь с SESSION_STATE/HANDOFF/ISSUES/BACKLOG, хронология-сводка, снимок статуса продукта — в шапку этого файла; `PRD_NOTES` — только ссылка на канон.

**Зачем:** один источник истории; агенты не дублируют журнал в NOTES.

---

## 2026-06-08 — Hermes: интенты по лидам (перепроход)

**Сделано:** `slot_normalize.py`, усилен rescue/fastpath; `smoke_hermes_leads.py` 40 pytest; BACKLOG eval закрыт; `HERMES_LEADS_ACCEPTANCE.md`.

**Зачем:** закрыть PRD_MAP п.2 CRUD/стадия/задача с воспроизводимым смоуком без зависимости от flaky Groq.

---

## 2026-06-08 — Whisper STT: перепроход и смоук

**Сделано:** `smoke_whisper_stt.py`, тесты voice/smoke; фикс 503 на `/api/voice/transcribe` и `error` в WS при сбое STT; live Groq OK; `WHISPER_STT_ACCEPTANCE.md`.

**Зачем:** закрыть PRD_MAP п.1 «Whisper → текст» с воспроизводимой проверкой.

---

## 2026-06-08 — Балльная воронка: смоук формулы и приоритетов

**Сделано:** `lead_priority_tier.py`, `smoke_scoring_funnel.py`, 21 pytest (формула scoreAdvisory, API, фильтр critical в списке); `SCORING_FUNNEL_ACCEPTANCE.md`; PRD_MAP пункт закрыт.

**Зачем:** закрыть хвост PRD_MAP «смоук формулы и приоритетов в списке» без регрессии лидов.

---

## 2026-06-08 — PRD_NOTES → канон (стек, docs map, gaps)

**Сделано:** контент после ~1834 перенесён в `ARCHITECTURE.md#справочник-стека`, `docs/README.md`, `BACKLOG.md#документация-фаза-2`, `stack/RAG.md#коллекции-chroma`; дубли в `PRD_NOTES.md` удалены.

**Зачем:** один источник правды, агенты не путают NOTES с каноном.

---

## 2026-06-08 — AGENTS.md + verify: Project Rules перебивают User Rules

**Сделано:** расследование хранения User Rules (облако Cursor, не файл); `AGENTS.md`; `verify_cursor_rules_precedence.py`; `CURSOR_USER_RULES_STATUS.md`.

**Зачем:** агент не может править Settings → Rules; project-level override без ручной правки UI.

---

## 2026-06-08 — Процесс: единое правило commit + ops

**Сделано:** `smartcrm-commit-ops.mdc` — канон (всегда `git commit` + ops; `git push` только по явному go). Остальные `.mdc` ссылаются на него без дублей. `check_rules_commit_conflict.py` — автопроверка формулировок в rules/ops.

**Зачем:** единое правило коммита без дублей в документах.

---

## 2026-06-08 — Acceptance блока «Лиды»: 81 pytest + DevTools + фикс tasks

**Сделано:** acceptance suite, smoke localhost:5174, фикс `/leads/tasks`, LEADS_BLOCK_ACCEPTANCE.md.

---

## 2026-06-08 — PRD_MAP п.12 + блок «Лиды» закрыт

**Сделано:** smoke_leads_block.py (71 pytest), leadsRouteManifest, расширена зона crm_leads; перепроход п.1–12 завершён.

---

## 2026-06-08 — PRD_MAP п.11: редиректы /crm → /leads

**Сделано:** crmRedirectMap.js, рефактор 9 route loaders, campaign redirect, тесты.

---

## 2026-06-08 — PRD_MAP п.10: лог касаний лида

**Сделано:** leadCommunications.js, RU-типы в UI, валидация API, тесты call/meeting/email.

---

## 2026-06-08 — PRD_MAP п.9: правила переходов стадий

**Сделано:** stageTransition.js, apiPatch для смены стадии, подсказки в UI, тесты API+normalize.

---

## 2026-06-08 — PRD_MAP п.8: аудит полей лида

**Сделано:** `leadAudit.js`, RU-лейблы в UI, тесты PATCH→audit и util.

---

## 2026-06-08 — PRD_MAP п.7: комментарии к лиду

**Сделано:** фикс рекурсии в карточке, `leadComments.js`, валидация пустого комментария, тесты API.

---

## 2026-06-08 — PRD_MAP п.6: задачи по лиду и SLA

**Сделано:** lead_id фильтр, overdue/today, задачи на карточке лида, taskApi с apiFetch, тесты.

---

## 2026-06-08 — PRD_MAP п.5: карточка лида (поля, ₽, апрувы, касания)

**Сделано:** apiFetch для activity; leadCardMoney/Activity; поле должность; тесты engagement API.

---

## 2026-06-08 — PRD_MAP п.4: фильтры и сортировка списка лидов

**Сделано:** приоритет-фильтр, сортировка по баллу/приоритету/компании; `leadListFilter.js`; тесты lib.

---

## 2026-06-08 — PRD_MAP п.3: Kanban drag & drop на воронке

**Сделано:** DnD карточек между колонками, оптимистичный PATCH, rollback при `stage_transition_blocked`; тесты lib + API.

---

## 2026-06-08 — feat: автосинк лидов из Битрикс24 (`f2727a3`)

**Сделано:** `webhooks_bitrix.py`, `bitrix24_sync.py`, `amount_rub`, `GET bitrix-sync-status`, фоновый опрос, тесты integrations.

---

## 2026-06-08 — BACKLOG: туннель + исходящий вебхук Битрикса

**Сделано:** запись в `BACKLOG.md`; мгновенный синк отложен (не блокер Ф1); п.3 ждёт `go`.

---

## 2026-06-08 — PRD_MAP п.2: поля Битрикс + автосинк лидов

**Сделано:** маппинг полей (+ `amount_rub`); `bitrix24_sync.py` (один лид, фоновый опрос); `POST /api/webhooks/bitrix/events`; `GET /api/leads/bitrix-sync-status`; тесты 7 passed; `docs/modules/bitrix.md` § автосинк.

**Зачем:** новый лид в Битриксе должен попадать в SmartCRM без ручной кнопки (вебхук мгновенно + опрос как страховка).

---

## 2026-06-08 — PRD_MAP: журнал перепрохода, п.1 CRUD ✅

**Сделано:** в `PRD_MAP.md` (§ Лиды) — таблица перепрохода 2026-06-08; п.1 CRUD отмечен OK; текущий шаг → п.2 «Поля уровня Битрикс».

---

## 2026-06-08 — PRD_MAP п.1: CRUD лидов UI + frontend dev (win-arm64)

**Сделано:** форма редактирования карточки лида (`leadCardEdit.js`, `/leads/{id}`); фикс `npm run dev` (Vite 6, rollup wasm, lightningcss binding script); тесты `test_leads_api` + `test_lead_card_edit`; DevTools-смоук CRUD.

**Зачем:** закрыть хвост п.1 «CRUD лидов (API + UI)» перед переходом к п.2 PRD_MAP.

---

## 2026-06-08 — Правила: коммит+ops безусловно

**Сделано:** `agent-workflow` §0; `task-workflow`, `dev-gates`, `.cursorrules`, `RULES_MATRIX`; `check_agent_step.py` — незакоммиченное = FAIL.

**Причина:** агенты пропускали коммит на закрытии шага.

---

## 2026-06-08 — Правила: матрица, enforcement, зачистка ops, PRD_MAP

**Сделано:**

| Артефакт | Суть |
|----------|------|
| `docs/operations/baselines/RULES_MATRIX.md` | Живая матрица правил + таблицы старта/регрессии/финиша |
| `backend/scripts/check_agent_step.py` | Проверка ops перед «done» |
| `smartcrm-*.mdc` | Таблица старта сессии; регрессия → что писать в отчёт; fix agent-workflow |
| `PRD_MAP.md` | п.118 закрыт (P6 в git); убран устаревший хвост «коммит локальных» |
| `BACKLOG.md` | Таблица хвоста синхронизирована |
| `docs/archive/deprecated-process-2025-05.md` | Архив устаревшего процесса (нейтральное имя) |
| ops | Убраны устаревшие формулировки из журналов |

**Причина:** `go ops sync` — готовность к работе по полной.

---

## 2026-06-07 — Правила: smartcrm-канон, всегда коммит+ops, регрессия по зонам

**Сделано:**

| Артефакт | Суть |
|----------|------|
| `.cursor/rules/smartcrm-*.mdc`, `.cursorrules` | Единый канон процесса; п.0 приоритета; старт сессии; honest report; стоп после шага |
| `docs/operations/CURSOR_USER_RULES_SNIPPET.md` | Текст для Cursor User Rules |
| `backend/scripts/run_zone_regression.py` | Регрессия по зонам (p1/p6/all) |

**Причина:** аудит правил и выравнивание процесса.

---

## 2026-06-07 — Dev gates (DoD, регрессия, миграции, API, hot-path)

**Сделано:** `smartcrm-dev-gates.mdc` — приоритет правил, DoD пункта PRD_MAP, таблица pytest по зонам, Migration/API gates, hot-path список. Синхрон: `agent-workflow`, `repo-layout` §6, `.cursorrules` как индекс.

---

## 2026-06-07 — BACKLOG + правило хвоста (PRD_MAP)

**Сделано:** `docs/operations/session/BACKLOG.md`; § бэклог в `smartcrm-task-workflow.mdc` — привязка **только к пунктам PRD_MAP**, фаза MAP опционально («когда закрывать»).

---

## 2026-06-07 — Anti-hallucination в task-workflow

**Сделано:** в `smartcrm-task-workflow.mdc` § «Честный отчёт» — обязательная секция «Не сделано / не проверено» после каждого шага; запрет на ложный done без факта тестов.

---

## 2026-06-07 — Правило workflow задач (PRD_MAP)

**Сделано:** `.cursor/rules/smartcrm-task-workflow.mdc` — явный пункт + `go`, тест на каждое изменение, коммит/ops без напоминания, push/deploy только по апруву. Ссылка в `smartcrm-repo-layout.mdc` §6.

---

## 2026-06-07 — Backend README pack + правило синхронизации

**Сделано:**
- 15× `backend/**/README.md` — карта зон простыми словами.
- Правило §5 **Backend README Sync** в `.cursor/rules/smartcrm-repo-layout.mdc` (апрув `go readme rule`).
- Справочник: `docs/dev/BACKEND_README_SYNC_DRAFT.md` (статус: применено).

**Обязательство агентов:** при изменениях в `backend/` обновлять README зоны в том же коммите.

---

## 2026-06-07 — P6 (шаг 4–9): остаток монолитов

**Сделано:**
- `core/qa_agent.py` → `core/qa/`
- `api/routes/tenders.py` → `api/routes/tenders/`
- `agents/analyst.py` → `agents/analyst/`
- `rag/search.py` → `rag/search/`
- `leadgen/pipeline.py` → `leadgen/pipeline/` (9 модулей, re-export публичного API)
- `leadgen/modules/checko.py` → `leadgen/modules/checko/` (cache, http_client, helpers, parse, search, endpoints, person)

**Тесты:** `test_leadgen` + `test_voice_pipeline` + tender/qa/analyst/rag — **114 passed**.

**Правки совместимости:** monkeypatch путей checko в тестах; `voice.pipeline.parse_intent` для mock; `employees_unknown` в portrait match.

---

## 2026-06-07 — P6 (шаг 3): сплит `api/routes/ops`

**Сделано:** `ops.py` (970 строк) → `api/routes/ops/{schemas,eval_cases,traces,dashboard,hermes,voice,eval,agents,logs,crm,__init__}.py`. URL `/api/ops/*` без изменений; 34 роута. Тест `test_ops_closes_groq_client` обновлён под пакет.

---

## 2026-06-07 — P6 (шаг 2): сплит `core/hermes`

**Сделано:** `hermes.py` (664 строки) → `core/hermes/{config,prompts,prompts_data,parse,rescue,cache,providers,text_utils,json_parse,__init__}.py`. Поведение `parse_intent` без изменений; импорты `from core.hermes import …` сохранены. Тесты: Parser 5 passed, voice prompt 1 passed.

---

## 2026-06-07 — P6 (шаг 1): сплит `api/routes/leads`

**Сделано:** `leads.py` (403 строки) → `api/routes/leads/{schemas,presenter,crud,engagement,bitrix_routes,__init__}.py`. Контракт API без изменений; pytest 21 passed.

---

## 2026-06-07 — P5: миграция документации в вложенные папки

**Сделано:** удалены 17 плоских `docs/*.md`; канон в `product/`, `modules/`, `start/`, `api/`, `email/`, `voice/`, `agents/`, `archive/`, `dev/`; таблица «Старые пути» в `docs/README.md`. `reference/CRM-points-system/` не коммитится.

---

## 2026-06-07 — P4: email integration test в tests/integration/

**Сделано:** `backend/test_email_integration.py` → `backend/tests/integration/test_email_integration.py`; путь в `docs/email/setup.md`.

---

## 2026-06-07 — P3: убрана backend/backend/data/

**Сделано:** `tender_sources_ab.json` → `backend/data/`; дубль `via_qa` и каталог `backend/backend/` удалены; предупреждение в `tender_sources_ab.py` (запуск из `backend/`).

---

## 2026-06-07 — P2: корень без мусора + анти-накопление

**Сделано:** `swagger.json` + DataNewton schema → `docs/api/openapi/`; артефакты → `backend/data/artifacts/` (gitignore); пустой `result.json` и `server.log` убраны; `.gitignore`; правила «куда новые файлы / не плодить папки» в `smartcrm-repo-layout.mdc`, `REPO_LAYOUT.md`. P2 → done в `LAYOUT_AUDIT`.

---

## 2026-06-07 — P1: тесты в backend/tests/

**Сделано:** `tests/` (корень) удалён; перенос в `backend/tests/api/`, `core/`, `rag/`; общий `backend/tests/conftest.py` (SQLite + X-API-Key). `LAYOUT_AUDIT` P1 → done.

---

## 2026-06-07 — Правила структуры репо и лимиты кода

**Сделано:** `.cursor/rules/smartcrm-repo-layout.mdc` (куда класть, тесты, запрет mv без `go`); `smartcrm-code-split.mdc` (цель 50 / стоп 200); `docs/dev/REPO_LAYOUT.md`; `docs/dev/LAYOUT_AUDIT.md` (пакеты P1–P6); ссылки в `CONTRIBUTING.md`, `docs/README.md`. Переносов файлов нет.

---

## 2026-06-07 — Техдельта v3 в документацию

**Сделано:** без дублей текста — канон в `PRD.md` + точечные секции и перекрёстные ссылки:

| Тема | Файл |
|------|------|
| `voice_action`, WS, Hermes `ui_action` | `PRD.md`, `ARCHITECTURE.md#контракт-voice_action` |
| Пакет Стратег → UI | `langgraph.md#пакет-voice_action` |
| Search-to-Q&A | `PRD.md`, `RAG.md#search-to-qa` |
| Email Ассистирующий / Автономный | `PRD.md` |
| Gate платного API тендеров | `tenders.md#экономика-и-gate` |
| Lookalike won + апрув | `leadgen.md#lookalike`, `PRD.md` |
| Чеклисты со ссылками | `PRD_MAP.md` |
| Журнал (без копипаста) | `PRD_NOTES.md` |

---

## 2026-06-07 — PRD_MAP: чеклисты Фаза 1–3 из PRD_NOTES

**Сделано:** `PRD_MAP.md` — полные чеклисты всех фаз (`[x]` сдано по коду, перепроход на баги; хвост Фазы 1: Hermes + voice_action). `PRD_NOTES.md` — навигация, таблица роутов, placeholder стек/доки, ссылки на MAP. Обновлены `PRD.md`, `docs/README.md`.

---

## 2026-06-07 — PRD_MAP: карта продукта

**Сделано:** пользователь добавил карту CRM в дельту; вынесено в `docs/product/PRD_MAP.md` (фазы, модули, статусы ✅/🔲, диаграммы агентов и голоса). `PRD.md` — ссылка-навигатор; `PRD_DELTA_v2.md` — только архив дельты; обновлены `docs/README.md`, `.cursorrules`.

---

## 2026-06-07 — PRD v2: слияние дельты в основной PRD

**Сделано:** `docs/product/PRD.md` переписан — единый roadmap Фаза 1–3 (Voice, Email, RAG, оркестрация, тендеры, аналитика, балльная воронка); дубли между фазами и дельтой убраны. `PRD_DELTA_v2.md` — архив со ссылкой на основной PRD.

---

## 2026-06-07 — PRD Delta v2 (отдельный документ)

**Сделано:** добавлен `docs/product/PRD_DELTA_v2.md` — дополнение к `PRD.md`: Voice Layer, Email-агент, Self-improvement, оркестрация агентов, roadmap тендеров, аналитика v2. *(Слито в PRD.md в том же дне.)*

---

## 2026-05-04 — P1 код: подсказка балла, суммы ₽, менеджер владеет score (`go`)

**Сделано:**

| Область | Изменения |
|---------|------------|
| БД | `leads.amount_rub`, `leads.paid_amount_rub` (NUMERIC), лёгкие `ALTER` в `db/session.py` при `init_db`. |
| Модель / API | `Lead.to_dict` + `LeadCreate`/`LeadPatch`; `GET/PATCH/POST /api/leads` для одного лида возвращают `scoreAdvisory`. |
| Логика | `core/lead_score_advisory.py` — `suggestedScore`, `warnings`, без записи в `score`. |
| Конфиг | `crm_settings_store`: `manager_sets_score`, `agents_may_update_score`, `scoring_advisory_enabled`, `scoring_advisory`. |
| Публичный CRM | `GET /api/crm/config` — флаги для фронта. |
| Ops | `PUT /api/ops/crm-settings` — новые поля в `CrmSettingsUpdate`. |
| Агенты | `tools.update_lead_score` пропускает PATCH при дефолтных флагах. |
| Фронт | `/leads/[id]`: суммы, предупреждения, подсказка; `fetchLeadById` в `leadsStorage.js`. |
| Тесты | `backend/tests/test_lead_score_advisory.py`. |
| Доки | Уточнены `docs/product/PRD.md` (приложение C, P1), `docs/product/ARCHITECTURE.md` под модель «менеджер + подсказка». |

**Причина:** ответы пользователя (0–100, балл менеджера, деньги, предупреждения) + **`go`** на P1-код.

---

## 2026-05-04 — P2: комментарии, аудит полей, правила перехода стадий (`go`)

**Сделано:**

| Область | Изменения |
|---------|------------|
| БД / ORM | Таблицы `lead_comments`, `lead_field_audits` (FK `ON DELETE CASCADE`), импорт в `init_db`. |
| Конфиг | `stage_transition_rules` в `crm_settings_store` + нормализация; `GET /api/crm/config` → `stageTransitionRules`; Ops `PUT` принимает `stage_transition_rules`. |
| Логика | `core/stage_transition.py`, `core/lead_field_audit_util.py`. |
| API | `GET/POST /api/leads/{id}/comments`, `GET /api/leads/{id}/audit`; `PATCH /api/leads/{id}` — гейты по правилам, аудит трекаемых полей; заголовок `X-Actor-Name` для аудита. |
| Фронт | `/leads/[id]`: блоки комментариев и истории полей; `apiUpdateLead` — разбор `stage_transition_blocked`; `/ops/crm` — textarea JSON правил. |
| Тесты | `backend/tests/test_stage_transition.py`. |
| Доки | `docs/product/ARCHITECTURE.md` — актуализация API и шага внедрения P2. |

**Причина:** явный **`go`** пользователя на P2 и дальнейшее развитие по PRD.

---

## 2026-05-04 — P3: апрувы в подсказке, лог касаний, расширенный аудит (`go` «по очереди»)

**Сделано:**

| Область | Изменения |
|---------|------------|
| БД / ORM | Колонка `leads.approvals` (JSON); таблица `lead_communication_logs`; у `lead_field_audits` — `event_type`, `metadata`. |
| Логика | `core/lead_approvals.py`, бонус апрувов в `lead_score_advisory` (`approval_weights`, `approval_bonus_cap`). |
| API | `LeadCreate`/`LeadPatch` + merge апрувов; `GET/POST .../communications`; аудит с `event_type` / `metadata` для касаний. |
| Фронт | `leadApprovals.js`, merge в `enrichLeadForCard`; карточка лида: чеклист апрувов, блок касаний, метка `eventType` в истории. |
| Тесты | Расширен `test_lead_score_advisory.py` (бонус и cap). |

**Причина:** перенос слоёв A/B/C из Rails CRM points без перезаписи `score` менеджером.

---

## 2026-05-04 — hotfix: пул asyncpg при обрывах TCP к Postgres

**Сделано:** `pool_pre_ping=True`, `pool_recycle` (env `DATABASE_POOL_RECYCLE_SEC`, по умолчанию 280) в `backend/db/session.py`; комментарий в `.env.example`. Дополнительно: нормализация `@localhost`→`127.0.0.1` (`DATABASE_FORCE_IPV4`), дефолт `DATABASE_URL` на `127.0.0.1`, `connect_args` (`timeout`, опционально `DATABASE_SSL=disable`).

**Причина:** 500 на `/api/leads` и связанных маршрутах из‑за `ConnectionResetError` / `ConnectionDoesNotExistError` при установлении соединения (часто Windows + `localhost`→`::1` vs Postgres только на IPv4).

---

## 2026-05-04 — hotfix: старт uvicorn после P3 ORM (`LeadFieldAudit`)

**Сделано:** в `lead_field_audit.py` — импорт `Optional`/`Any`, аннотация `Mapped[Optional[dict[str, Any]]]` для `audit_metadata`; в `lead.py` — `approvals: Mapped[Optional[dict[str, Any]]]`. Иначе `MappedAnnotationError` / `NameError: Optional` и 500 на всех маршрутах лидов.

**Причина:** инцидент в прод-логике старта; запись в `ISSUES` + `SESSION_STATE`.

---

## 2026-05-04 — P1 закрытие: fetch карточки лида по смене id, `docs/agents/langgraph.md` (`go` «добей»)

**Сделано:** на `/leads/[id]` `fetchLeadById` вызывается только при смене `params.id` (меньше лишних запросов при обновлении store); в `docs/agents/langgraph.md` зафиксированы гейт `update_lead_score`, `scoreAdvisory`, настройки Ops.

**Причина:** явный **`go`** на завершение итерации после P1.

---

## 2026-05-04 — PM + Architect: балльная воронка лидов (дельта PRD и ARCHITECTURE, `go`)

**Сделано:**

| Артефакт | Содержание |
|----------|------------|
| `docs/product/PRD.md` | Роли; фича «балльная воронка лидов» (проблема, ценность, scope, P1–P3, не-скоуп, метрики, риски, зависимости); приложения A–G; объём ≥250 строк. |
| `docs/product/ARCHITECTURE.md` | Раздел домена лидов и скоринга: as-is/to-be, решения по умолчанию, план DDL/API/модулей, безопасность, порядок внедрения, матрица агентов, traceability к Rails-референсу; ≥250 строк. |

**Причина:** пользовательский **`go`** на шаг PM и Architect без кода.

---

## 2026-05-03 — Аудит документации + операционные журналы (go пользователя)

**Сделано:** заготовки `docs/operations/*`, реорганизация доков. Архив устаревшего процесса → [`docs/archive/deprecated-process-2025-05.md`](../archive/deprecated-process-2025-05.md).

---
