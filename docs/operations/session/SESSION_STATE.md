# SESSION_STATE

Краткий прогресс сессии — **обязательно** после каждого действия (1–2 строки). Шаг с изменениями файлов → `git commit` **до** отчёта. Канон: `workflow/smartcrm-commit-ops.mdc`.

**По завершении задачи:** сначала `git commit`, затем в строке `Коммит: \`hash\`` — хеш из этого коммита (не прочерк, не «потом»).

2026-07-18 | Действие: CoffeeOS workflow шаг 2 — SBR: spec-build-review.mdc, todo.md, RED/GREEN в commit-ops/task-workflow/dev-gates/index; BACKLOG шаги 3–6 | Коммит: `a5f72b3` | Хвост A: project-rules, merged отчёт, doc links, scratch, scope SBR апрув | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 1 — `.cursor/rules/workflow/` (6 mdc), `project/` placeholder, `smartcrm-index.mdc`; rename code-split→file-size-split; обновлены AGENTS.md, .cursorrules, RULES_MATRIX, verify_cursor_rules_precedence.py; BACKLOG шаги 2–6 | Коммит: `c4318aa` | Хвост A: SBR, project-rules, merged отчёт, mass doc links, scratch | Хвост B: BACKLOG § CoffeeOS migration | Хвост C: нет | Статус: done

2026-06-27 | Действие: email backfill — skip auth error после 3 fail, RR advance; pytest 4 PASS | Коммит: `7437c8a` | Хвост A: ib@ пароль/SECRET_KEY | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: email backfill — батчи по датам, API, UI кнопка, скрипт; pytest email_sync 20 PASS; live: ib@ AUTH FAILED | Коммит: `ee17841` | Хвост A: Sent-папка не в backfill; browser не кликали | Хвост B: нет | Хвост C: ib@ IMAP AUTH — проверить пароль/SECRET_KEY | Статус: done

2026-06-25 | Действие: тред /email Yandex — EmailThreadView, strip цитат, сайдбар «Письма на тему»; pytest 11 PASS | Коммит: `d1ad85e` | Хвост A: browser не кликали; карточка лида без паритета | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: UI /email Yandex Mail — sidebar, search chips, папки, звёзды; F4_EMAIL_YANDEX_UI.md; pytest 8 PASS | Коммит: `cb54ff8` | Хвост A: browser апрув не кликали | Хвост B: нет | Хвост C: Trash/Drafts/Spam placeholder | Статус: done

2026-07-01 | Действие: spawn_bitrix_backfill_focused — поля/tasks/products/import; task scope OK; timeline done; FAQ/IMAP выкл; pytest 2 PASS | Коммит: `7d40b32` | Хвост A: дождаться fields+import | Хвост B: нет | Хвост C: requisite.list Access denied (не блокер) | Статус: in_progress

2026-06-29 | Действие: B24 mass backfill — spawn 5 workers + import-bitrix API; B24 API OK; FAQ/почта выкл в .env; fix load_dotenv в resync_bitrix_lead_profiles | Коммит: `91bb262` | Хвост A: дождаться fields/tasks/products; перезапуск uvicorn для EMAIL_AUTO_SYNC=0 | Хвост B: нет | Хвост C: DB pool конкуренция import+workers — перезапуск sequential | Статус: in_progress

2026-06-27 | Действие: кнопка «Сбросить» всегда видна в /leads/list (фикс. позиция после поиска); smoke test | Коммит: `490e5e5` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: persistence фильтров /leads/list — sessionStorage leadListFilterState.js; restore при возврате с карточки; pytest 4 PASS | Коммит: `d790ee4` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: LeadCardCoachBanner на хабе /leads/[id] — просрочки, доки, паспорт, скоринг; alert на плитках; pytest 3 PASS | Коммит: `aa53b96` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: listStageSummary — этап/путь/сроки в GET /api/leads + UI колонка Этап (прогресс, дни, дело); batch_stage_entered_at; pytest 10 PASS | Коммит: `267c713` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: listCoach — суфлёр «что сделать» в GET /api/leads + UI /leads/list (дела, путь сделки, дозаполнить); pytest 41 PASS leads zone | Коммит: `eff2bb2` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: фильтр «На дату» в /leads/list — openTaskDueDates в API, date picker в UI; pytest 9 PASS | Коммит: `b301757` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: task_intent dropdown (tasks/карточка/activity) + Ops day_priority JSON; API intent-catalog; тесты 53 PASS crm_leads | Коммит: `24c7f4b` | Хвост A: нет | Хвост B: нет | Хвост C: фикс import в task.py | Статус: done

2026-06-27 | Действие: «Мой день» — lead_day_priority, intents, API dayRank, UI sort+badge, stage_hints wait_stale; pytest crm_leads 51 PASS | Коммит: `6fcf5d4` | Хвост A: dropdown task_intent, Ops веса | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-27 | Действие: docs — спека «Мой день» F4_DAY_PRIORITY.md; PRD_MAP §Мой день (8 пунктов); phase4/README, F4_LEADS_ACCEPTANCE, F4_SCORING_TUNING, leads.md, BACKLOG, core/README | Коммит: `f212757` | Хвост A: код lead_day_priority после go | Хвост B: BACKLOG запись | Хвост C: нет | Статус: done

2026-06-27 | Действие: restart B24 backfill — spawn 5 workers; spawn fields→--only-missing; resume timeline 2610/3228; 🔴 B24 MySQL Connection refused на портале | Коммит: `0287f39` | Хвост A: догрузить ~618 timeline + ~191 fields после B24 | Хвост B: нет | Хвост C: ISSUES B24 MySQL | Статус: blocked

2026-06-26 | Действие: restart mass B24 backfill — spawn_bitrix_backfill_all (поля/таймлайн/tasks/products/watch); timeline resume 2490→2520+/3228; fields ~94% extra | Коммит: `98727cf` | Хвост A: дождаться 3228 timeline+tasks | Хвост B: нет | Хвост C: нет | Статус: in_progress

2026-06-25 | Действие: docs — чеклист Ф4 Email: `F4_EMAIL_TUNING.md`, PRD_MAP §Email (17 пунктов), phase4/README | Коммит: `5b77eb0` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: апрув обхода воронка/дела/задачи/календарь/фокус/аналитика — PRD_MAP 556–559 [x], F4 §П.4/4b/6/7 | Коммит: `505331f` | Хвост A: голос отложен | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: апрув обхода карточки лида — PRD_MAP п.550/552/555 [x], F4_LEADS_ACCEPTANCE §П.3 | Коммит: `a95f8ab` | Хвост A: воронка/задачи/аналитика не обходили | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: апрув обхода `/leads/list` — PRD_MAP п.551/553/557 [x], F4_LEADS_ACCEPTANCE §П.5 чеклист | Коммит: `bb73709` | Хвост A: карточка/воронка/аналитика не обходили | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: docs — исходящий вебхук B24 + ngrok пошагово (`docs/start/BITRIX_OUTBOUND_WEBHOOK.md`); ссылки bitrix.md, BACKLOG, docs/README | Коммит: `1ed3816` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: убрать Аналитика из корневого сайдбара — только /leads/analytics; test_app_sidebar_ui; pytest 8 PASS | Коммит: `c23b32a` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-25 | Действие: resume mass B24 backfill — fields+timeline resume 270+tasks+products+watch; engagement --resume; spawn_bitrix_backfill_all; pytest 1 PASS | Коммит: `042b5bd` | Хвост A: дождаться 3228 по всем слоям | Хвост B: нет | Хвост C: параллельные прогоны грузят B24 API | Статус: in_progress

2026-06-24 | Действие: /leads/deals B24-стиль — activities API, фильтры scheduled/today/tomorrow, менеджер, время в B24 due; list+tasks завтра; pytest 17 PASS | Коммит: `29d1380` | Хвост A: browser /leads/deals не кликали | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-24 | Действие: B24 таймлайн → «Действия и история» — bitrix24_timeline_extra, UI leadActivityTimeline, check_bitrix_engagement_backfill, --timeline-only state; smoke 5 +6; mass timeline в фоне; pytest 5 PASS | Коммит: `fb20f91` | Хвост A: browser Liqvor не кликали; mass timeline 3228 в фоне | Хвост B: нет | Хвост C: crm.timeline.comment.list Access denied на части лидов (портал) | Статус: done (код)

2026-06-24 | Действие: fix 404 /api/leads/leads/coverage|managers — пути в leadsStorage; fallback менеджеров из списка; smoke test; activity resync 3228 done 359 tasks | Коммит: `05446af` | Хвост A: browser не кликали | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-24 | Действие: фильтр менеджера /leads/list — GET /managers, dropdown, колонка, карточка; CRM_OPERATOR_NAME; pytest 8+35 crm_leads PASS | Коммит: `a5079a1` | Хвост A: browser UI не кликали; CRM_OPERATOR_NAME в .env не задан | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-24 | Действие: /leads/list coverage — сегменты B24/паспорт/пустые/проигран/без дел; GET /api/leads/coverage; чипы-фильтры UI; pytest 12+34 crm_leads PASS | Коммит: `f9123bf` | Хвост A: mass resync + activity resync в фоне; browser UI не кликали | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-24 | Действие: /leads/tasks фильтры статус+срок+эскалация; task_list_filter API; бейджи; pytest 8 PASS | Коммит: `9e1d76b` | Хвост A: mass resync в фоне | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-24 | Действие: UI /leads/tasks — список сверху, модалка создания+SLA, tasksPageFilters; pytest 2 PASS | Коммит: `3739c5b` | Хвост A: mass resync в фоне | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-24 | Действие: crm.activity синк без scope task; include_tasks_module; smoke 5 OK; full resync tasks в фоне; pytest 16 PASS | Коммит: `511b753` | Хвост A: mass fields resync + activity resync в фоне | Хвост B: нет | Хвост C: нет | Статус: in_progress

2026-06-24 | Действие: 👤 апрув шаг 5/7; resync ~1205/3228 running; --only-missing + watch_fields_resync_then_retry; pytest 2 PASS | Коммит: `1b81d9a` | Хвост A: дождаться 3228 + only-missing pass | Хвост B: нет | Хвост C: 141 API errors burst @1045–1185 | Статус: in_progress

2026-06-24 | Действие: X5-gap прогон — DevTools шаг5/7+calendar OK; F4_X5_BROWSER_APPROVAL; fix calendar +page.svelte; resync 985/3228 running | Коммит: `d81ed3c` | Хвост A: mass-resync до 3228; 👤 ок 5/7; scope task | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: in_progress

2026-06-24 | Действие: шаг 4 webhook scope task — extended probe (feature API), JSON report, F4_X5_WEBHOOK_TASK_SCOPE_ACCEPTANCE; live task missing; pytest 8 PASS | Коммит: `ae3fa9c` | Хвост A: 👤 scope task на B24 + resync | Хвост B: BACKLOG шаг 4 | Хвост C: requisite.list Access denied | Статус: blocked (портал)

2026-06-24 | Действие: mass-resync хвост 1–3 — rate-limit/retry в bitrix_call, auto-sync pause, multi-contacts metrics; 162/3225 extra, 106 multi; pytest 6+ PASS; прогон resume w2 | Коммит: `1f103f5` | Хвост A: дождаться 3225; scope task; browser | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: in_progress

2026-06-19 | Действие: список шаг 7 — фильтры подписка/тип поставки, колонка «Подписка до»; pytest 8 PASS | Коммит: `a228e9d` | Хвост A: browser апрув после mass-resync | Хвост B: BACKLOG шаг 7 | Хвост C: нет | Статус: done

2026-06-19 | Действие: mass-resync полей шаг 6 — resync_bitrix_lead_fields.py, bitrix_lead_fields_sync; pytest 6 PASS; smoke limit 2 OK; полный прогон 3225 в фоне | Коммит: `8c6e5e5` | Хвост A: дождаться полного прогона; scope task; browser апрув | Хвост B: BACKLOG шаг 6 | Хвост C: нет | Статус: in_progress

2026-06-19 | Действие: UI карточки X5-gap шаг 5 — LeadBitrixExtraPanel, LeadContactsReadonlyList, бейдж повторного лида, formatDealAmountLabel `$`; pytest lib+smoke 21 PASS; BACKLOG сводка хвостов 1–5 | Коммит: `cd62bbf` | Хвост A: mass backfill 1–3, scope task п.4, browser апрув 3+5 | Хвост B: BACKLOG § X5-gap | Хвост C: нет | Статус: done

2026-06-19 | Действие: webhook scope task — probe crm/user/task, fix 401 tasks.task.list, resync_bitrix_lead_tasks, preflight; pytest 10 PASS; live: task missing на портале | Коммит: `59490d3` | Хвост A: оператор должен включить scope task в B24 и запустить resync | Хвост B: нет | Хвост C: нет | Статус: blocked (портал)

2026-06-19 | Действие: сумма+валюта — deal_amount/deal_currency, API amount/currency, UI шапка+панель, Битрикс OPPORTUNITY; pytest 28+ PASS. | Коммит: `85f88ef` | Хвост A: mass backfill deal_amount на 3225 не запускали; апрув UI в браузере | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-19 | Действие: мультиконтакты Битрикс — contact.items, 5 контактов X5-like, merge_bitrix_contacts; pytest 10 PASS. | Коммит: `2497736` | Хвост A: mass resync contacts на 3225 не запускали | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-19 | Действие: UF Битрикс → bitrix_extra — lead_bitrix_extra, enrich/merge upsert, API bitrixExtra, миграция JSONB; pytest 14 PASS (X5-like). | Коммит: `503914d` | Хвост A: mass backfill bitrix_extra на 3225 не запускали | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: Битрикс история+задачи — bitrix24_tasks, resync_bitrix_lead_engagement, upsert sync; pytest 30 PASS; docs leads.md+PRD_MAP. | Коммит: `c9e0cb8` | Хвост A: mass resync 3225 в фоне | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: массовый resync продуктов — bitrix24_products (lead.get, КП, product.get, OPPORTUNITY); resync --workers + load_dotenv; pytest 5 PASS; фоновый прогон 3225 лидов (~140+ с продуктами на момент коммита). | Коммит: `164be96` | Хвост A: полный resync 3225 в фоне не дождались | Хвост B: нет | Хвост C: нет | Статус: in_progress

2026-06-22 | Действие: продукты Битрикс — lead_products, bitrix24_products, плитка+панель UI, resync script; DevTools OK; pytest 23 PASS; backfill offline 0. | Коммит: `bffbf62` | Хвост A: на проде re-import с webhook для цен | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: отрасли из ОКВЭД — okved_industry_map, industry_bucket, фильтр+группировка list, backfill 3230/158, DevTools OK; pytest 38 PASS. | Коммит: `0a58b61` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: дела в списке — lead_task_list_flags, сортировка tasks_urgent, фильтры Дела, KPI+бейдж, fix due в карточке; pytest crm_leads 30 + unit/smoke 11 PASS. | Коммит: `cb3c63b` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: Битрикс UF ОКВЭД/сотрудники → lead_profile; resync_bitrix_lead_profiles.py; pytest 12 PASS; import skip (нет webhook), backfill 0. | Коммит: `464fe88` | Хвост A: re-import на проде с BITRIX24_WEBHOOK_URL | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: группировка list (groupLeads ОКВЭД/размер/этап), backfill 3230/386, DevTools фильтры+группы OK; pytest 13 PASS. | Коммит: `d3be5c9` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: сегментация лидов — lead_profile (ОКВЭД normalize, employees_band, portrait_score), колонки Lead, sync CRUD/enrich/CSV/B24, фильтры list, backfill script; pytest 28+ PASS. | Коммит: `28517cd` | Хвост A: backfill на прод не запускали; UI в браузере не проверяли | Хвост B: сворачиваемые группы в списке — BACKLOG | Хвост C: нет | Статус: done

2026-06-19 | Действие: /leads/list — шапка (Новый лид + ⋯ импорт), KPI, фильтры с подписями, сброс; pytest smoke 4+5 PASS. | Коммит: `20edfdb` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-19 | Действие: карточка лида — хаб плиток 2×3/3×2 + slide-over ~65% (LeadHubTile, LeadSlideOver, leadHubPreview); вкладки убраны; ?panel= deep link; pytest smoke 9 PASS. | Коммит: `2f6b55c` | Хвост A: апрув UI в браузере не делали | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-22 | Действие: enrich → полный паспорт checko_json (Checko+BuiltWith, passport PATCH, фильтр телефонов); pytest rag+lib+leads API 14 PASS. | Коммит: `5c17439` | Хвост A: live Checko на Hochland в браузере не проверяли | Хвост B: вакансии/налоги/история — BACKLOG | Хвост C: нет | Статус: done

2026-06-21 | Действие: блок действий — постановка задачи в календарь + список задач (срок/просрочка, раскрытие); pytest 11 PASS. | Коммит: `89b22d6` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Статус: done

2026-06-21 | Действие: вкладка «Паспорт клиента» вместо Checko — 20 разделов (связи, финансы, риски…); LeadPassportPanel + leadPassport.js; pytest 9 PASS. | Коммит: `7e58d47` | Хвост A: enrich→checko_json не в этом шаге | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go (enrich в паспорт). | Статус: done

2026-06-21 | Действие: scoreAdvisory убран с обзора → LeadScoreAdvisoryPanel под Системные поля справа; pytest 6 PASS. | Коммит: `3fa4302` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-21 | Действие: компактный путь сделки — next step + accordion; убран дубль ЛПР в До КП; pytest 28 PASS. | Коммит: `bae1dbf` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-19 | Действие: блок контактов в карточке + авто ЛПР в dealPath; contacts JSON; pytest 16 PASS. | Коммит: `4de81c1` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-19 | Действие: split колонок обзора — слева воронка+активность, справа только форма/₽/системные; pytest 6 PASS. | Коммит: `89e2a97` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-19 | Действие: swap колонок обзора — активность слева, редактирование справа; pytest 6 PASS. | Коммит: `fccff15` | Хвост A: апрув в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-19 | Действие: путь сделки dealPath + stageHints API/UI; LeadDealPathPanel; pytest 14 PASS. | Коммит: `f4053ce` | Хвост A: апрув UI в браузере; гейты этапа не делали | Хвост B: жёсткие блоки перехода — после апрува | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-19 | Действие: этапы карточки — под шапкой, stageBadgeClass, убран блок снизу; pytest 6 PASS. | Коммит: `0795b14` | Хвост A: апрув обход в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: ждём go. | Статус: done

2026-06-19 | Действие: обзор карточки — 2 колонки full-width, left/right testid; pytest 4 PASS. | Коммит: `bd4b1e1` | Хвост A: апрув обход в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: reload /leads/{id}. | Статус: done

2026-06-19 | Действие: UX карточки — иконки в шапке + сворачиваемый/скрытый сайдбар на lead card; pytest 8 PASS. | Коммит: `20d9490` | Хвост A: апрув обход в браузере | Хвост B: нет | Хвост C: vite build падает на tenderApi.js (не этот шаг) | Следующий шаг: reload /leads/{id}. | Статус: done

2026-06-19 | Действие: фикс 500 карточки лида — лишний `</div>` в overview; vite compile OK; smoke 3 PASS. | Коммит: `463ba98` | Хвост A: апрув обход карточки в браузере | Хвост B: нет | Хвост C: нет | Следующий шаг: reload /leads/{id}. | Статус: done

2026-06-19 | Действие: UX карточки лида — обзор full-width, вкладки level-3; smoke 3 PASS. | Коммит: `22347dd` | Хвост A: апрув обход карточки | Хвост B: нет | Хвост C: нет | Следующий шаг: обход + фильтры list. | Статус: done

2026-06-19 | Действие: Ф4 лиды — 4 критичных пункта в MAP + acceptance; только docs. | Коммит: `dc4f08a` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: обход критичных. | Статус: done

2026-06-19 | Действие: Ф4 блок «Интеграции CRM» — отдельный MAP + F4_CRM_INTEGRATIONS_ACCEPTANCE; leads очищен; только docs. | Коммит: `16328d9` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go код /ops/integrations. | Статус: done

2026-06-19 | Действие: Ф4 лиды §П.0 — план интеграций внешних CRM, MAP первым пунктом; только docs. | Коммит: `8029025` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go шаг 1 integrations или обход карточки. | Статус: done

2026-06-19 | Действие: Ф4 лиды — чеклист обхода (приоритеты + п.3–9), MAP §Лиды; только docs. | Коммит: `c0e68d9` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: обход п.3 карточка. | Статус: done

Шаблон строки:

`[дата] | Действие:[…] | Коммит:`хеш` | Хвост A:[план не сделано — нет/список] | Хвост B:[BACKLOG в прогоне — нет/список] | Хвост C:[доп. починки — нет/список] | Следующий шаг:[…] | Статус:done`

**Хвост A/B/C обязателен** в каждой новой записи (`check_agent_step.py`).

**Правило:** в строке только реальный `Коммит: \`hash\`` — иначе FAIL (`check_agent_step` + **pre-commit hook**).

2026-06-19 | Действие: апрув Ф4 лиды п.2 удаление — ручной тест OK, MAP [x]. | Коммит: `263a111` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: обход лидов дальше. | Статус: done

2026-06-19 | Действие: MAP Ф4 — секция «Лиды» перенесена после «Дашборд» (docs only). | Коммит: `8650e34` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP удаление лидов. | Статус: done

2026-06-19 | Действие: Ф4 лиды п.2 — удаление (confirm, list+card, apiDelete, purge FK); MAP §Лиды; pytest 20 PASS. | Коммит: `16ac2da` | Хвост A: DevTools smoke не делали | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP удаление. | Статус: done

2026-06-19 | Действие: Ф4 дашборд п.1 — модалка «Новый лид» (дашборд + /leads/list), POST БД, acceptance + MAP; pytest 19 PASS. | Коммит: `f5e4274` | Хвост A: DevTools smoke руками не делали | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP дашборд п.1 · обход дашборда. | Статус: done

2026-06-17 | Действие: хвост C — регресс industryOptions: test_lead_card_page.py, smoke /leads/{id}, DevTools /leads/3191 без ReferenceError. | Коммит: `31242ec` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф4 D–F или Ф4-A. | Статус: done

2026-06-17 | Действие: Ф4 сортировка warnings/delta + DevTools smoke + smoke_scoring_f4_ui.py; фикс industryOptions карточка; pytest/smoke 11 PASS. | Коммит: `0d66a41` | Хвост A: нет | Хвост B: нет | Хвост C: industryOptions ReferenceError на /leads/[id] — починили | Следующий шаг: go Ф4 D–F или Ф4-A интеграции. | Статус: done

2026-06-17 | Действие: Ф4 баллы A–C — Ops scoring_advisory UI, breakdown карточка, флаги+фильтры списка; pytest 17 PASS. | Коммит: `618bffe` | Хвост A: DevTools/smoke UI не кликал; сортировка по warnings — не делали; MAP [x] ждёт «ок» | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP Ф4 баллы A–C или go D–F. | Статус: done

2026-06-19 | Действие: docs Ф4 баллы — F4_SCORING_TUNING.md, секция в PRD_MAP, F4_PLATFORM §D. | Коммит: `11abbf1` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф4-A интеграции или Ф4 баллы-A. | Статус: done

2026-06-19 | Действие: smoke экспорт баллов — DevTools «Баллы» xlsx 200, smoke_scoring_export.py OK (pytest 13 + live 245KB). | Коммит: `f6459af` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: Ф4 экран интеграций. | Статус: done

2026-06-17 | Действие: P3 [x] SLA MAP + экспорт баллов/воронки — scoring/export API, UI «Баллы», acceptance; pytest 19 PASS. | Коммит: `39f452e` | Хвост A: DevTools/smoke руками не делали | Хвост B: нет | Хвост C: нет | Следующий шаг: Ф4 экран интеграций. | Статус: done

2026-06-17 | Действие: P3 SLA шаги 1–5 — протоколы, API назначения, автозадачи, эскалация+Telegram, UI; pytest 24 PASS. | Коммит: `5852ffd` | Хвост A: живой smoke/DevTools не делали; MAP [x] ждёт «ок»; экспорт баллов (505) не трогали | Хвост B: нет | Хвост C: фикс моков в unit-тестах SLA | Следующий шаг: «ок» MAP SLA или go 505. | Статус: done

2026-06-17 | Действие: docs Ф4 платформа — F4_PLATFORM_TUNING.md, секция в PRD_MAP + phase4 README. | Коммит: `9797d84` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф4-A экран интеграций. | Статус: done

2026-06-17 | Действие: Ф3 платформа шаги 2–5 — Amo+HubSpot sync, Telegram inline+Ops critical, [x] CRM MAP. | Коммит: `c2949ce` | Хвост A: живой smoke Amo/HubSpot/Б24 не делали | Хвост B: нет | Хвост C: нет | Следующий шаг: баллы P3 SLA или Ф4. | Статус: done

2026-06-17 | Действие: Ф3 платформа шаг 0–1 — [x] MAP lead hunt+Telegram, Битрикс push (adapter, API, UI, pytest). | Коммит: `c7d986c` | Хвост A: живой smoke Б24 не делали | Хвост B: Amo/HubSpot следующий шаг | Хвост C: нет | Следующий шаг: AmoCRM import/export. | Статус: done

2026-06-17 | Действие: Ф3 Telegram-бот MVP — poll, notify lead hunt, /start /status /queue, acceptance, pytest. | Коммит: `01ae21b` | Хвост A: Ops critical wiring не подключён | Хвост B: inline approve/reject → BACKLOG | Хвост C: нет | Следующий шаг: «ок» MAP Telegram. | Статус: done

2026-06-19 | Действие: Ф3 lead hunt шаги 6–7 — UI оператора, approve-above, acceptance, DevTools smoke. | Коммит: `7045476` | Хвост A: PRD_MAP [x] ждёт «ок» | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP автопоиск. | Статус: done

2026-06-19 | Действие: Ф3 lead hunt шаг 5 — фон loop, trace+agent_run_log, баннер/badge Ops. | Коммит: `a6e670f` | Хвост A: DevTools smoke UI не кликал | Хвост B: Telegram lead hunt → BACKLOG | Хвост C: нет | Следующий шаг: «ок» MAP автопоиск. | Статус: done

2026-06-19 | Действие: Ф3 lead hunt шаг 4 — queue API, approve→CRM+nurture, UI /ops/queue + /leadgen. | Коммит: `4d1cf33` | Хвост A: DevTools smoke UI не кликал | Хвост B: нет | Хвост C: circular import queue↔candidates — lazy import | Следующий шаг: «ок» MAP автопоиск. | Статус: done

2026-06-19 | Действие: Ф3 lead hunt цикл агентов — search_cycle, fanout, dedup БД. | Коммит: `c22ade8` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP автопоиск. | Статус: done

2026-06-19 | Действие: Ф3 lead hunt шаги 3–6 — поиск, очередь, уведомления, UI /ops/lead-hunt. | Коммит: `85acdee` | Хвост A: нет | Хвост B: нет | Хвост C: UI API pending при reload uvicorn в smoke | Следующий шаг: «ок» MAP автопоиск. | Статус: done

2026-06-18 | Действие: Ф3 lead hunt шаг 2 — ICP из won + funnelBySource + Стратег, версии state. | Коммит: `080a2cf` | Хвост A: поиск кандидатов (шаг 3), UI ops — нет | Хвост B: шаги 3–6 → BACKLOG | Хвост C: нет | Следующий шаг: go шаг 3 search_by_portrait. | Статус: done

2026-06-18 | Действие: Ф3 Платформа — lead hunt шаг 1 (каркас, ops API, poll). | Коммит: `d24fcba` | Хвост A: UI /ops не делали | Хвост B: шаги 2–6 lead hunt → BACKLOG | Хвост C: нет | Следующий шаг: go шаг 2–3 поиск кандидатов. | Статус: done

2026-06-17 | Действие: Ф3 Платформа — CSV импорт/экспорт лидов (шаг 1 CRM sync). | Коммит: `0c49729` | Хвост A: UI в браузере не кликал | Хвост B: Amo/HubSpot → BACKLOG | Хвост C: нет | Следующий шаг: go шаг 2 Битрикс push. | Статус: done

2026-06-17 | Действие: Ф3 Платформа — экспорт Excel/PDF (воронка, карточка, тендеры); Telegram → BACKLOG. | Коммит: `2bf1adf` | Хвост A: нет | Хвост B: Telegram-бот в BACKLOG | Хвост C: нет | Следующий шаг: «ок» MAP · импорт CRM / Ф4. | Статус: done

2026-06-17 | Действие: Ф4 docs — F4_ANALYTICS_V2_TUNING; PRD_MAP §Ф4 analytics (6 пунктов). | Коммит: `0b49c45` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф4 analytics п.1 или Платформа. | Статус: done

2026-06-17 | Действие: Аналитика v2 п.4 прогноз закрытия — lead_close_forecast, closureForecast, UI; блок MAP 4/4; pytest 19 PASS. | Коммит: `eae481e` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» аналитика · Платформа/Ф4. | Статус: done

2026-06-17 | Действие: Аналитика v2 п.3 воронка по источнику — funnelBySource, UI /leads/analytics, CSV; pytest 17 PASS. | Коммит: `a6ee217` | Хвост A: п.4 прогноз закрытия | Хвост B: нет | Хвост C: нет | Следующий шаг: go прогноз Экономист. | Статус: done

2026-06-17 | Действие: Аналитика v2 п.2 агенты по трейсам — agent_trace_analytics, API, /ops/stats, improve links; pytest 5 PASS. | Коммит: `cc2385d` | Хвост A: п.3–4 аналитики | Хвост B: нет | Хвост C: нет | Следующий шаг: go воронка по источнику. | Статус: done

2026-06-17 | Действие: Аналитика v2 п.1 когорты — compute_cohorts, API/UI/CSV, acceptance; pytest 15 PASS. | Коммит: `8297650` | Хвост A: п.2–4 аналитики — не трогали | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» когорты · go п.2 агенты по трейсам. | Статус: done

2026-06-17 | Действие: Ф4 docs — F4_TECH_TENDER_TUNING; PRD_MAP §Ф4 + phase4 README. | Коммит: `f93cf96` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф4 автопайплайн или Аналитика v2. | Статус: done

2026-06-17 | Действие: MAP п.3 sources [x] апрув; п.4 вердикт участия — tender_participation, API participation, UI вкладка Вердикт, snapshot; pytest 29 PASS зона. | Коммит: `11711c5` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP п.4 · Аналитика v2 по go. | Статус: done

2026-06-17 | Действие: MAP п.2 [x]; tender_sources + Gosplan prod + фильтры + DataNewton UI; Контур→Ф4 gate-doc; pytest 35 PASS зона. | Коммит: `f58477e` | Хвост A: п.4 участвовать — не трогали | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP п.3. | Статус: done

2026-06-17 | Действие: MAP мониторинг [x]; уведомления+календарь тендеров; pytest 16 PASS. | Коммит: `f19fe51` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP п.2. | Статус: done

2026-06-17 | Действие: pytest.ini — убран битый StarletteDeprecationWarning; test_pytest_config 2 PASS. | Коммит: `5840750` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP мониторинг п.1. | Статус: done

2026-06-17 | Действие: Тех. спец мониторинг тендеров — tender_monitor, API, фон, UI /ops/tender-monitor; MAP переименование; pytest 9 PASS. | Коммит: `9f13868` | Хвост A: нет | Хвост B: нет | Хвост C: pytest.ini StarletteDeprecationWarning — локально -c NUL | Следующий шаг: «ок» MAP п.1. | Статус: done

2026-06-17 | Действие: Ф4 суфлёр tuning + MAP [x] апрув суфлёр. | Коммит: `c18920b` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: Ф3 тендеры / Ф4. | Статус: done

2026-06-17 | Действие: авто-суфлёр Стратега — strategist_suggester, API, UI /ops/agents; MAP A/B [x]; pytest 8 PASS. | Коммит: `3c9523d` | Хвост A: runtime агентов читает override — Ф4 | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP суфлёр. | Статус: done

2026-06-17 | Действие: Ф4 A/B промптов tuning — чеклист 8 пунктов phase4/agents + BACKLOG + PRD_MAP. | Коммит: `be8c154` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP A/B; суфлёр Стратега. | Статус: done

2026-06-17 | Действие: A/B промптов по трейсам — prompt_ab_traces, API ab-traces, UI improve; MAP crawl [x]; pytest 5 PASS. | Коммит: `2230dc0` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP A/B; суфлёр Стратега. | Статус: done

2026-06-17 | Действие: Ф4 vendor crawl tuning — чеклист 4 пункта в phase4/rag + BACKLOG + PRD_MAP. | Коммит: `0bed5e6` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» Ф3 crawl; A/B промптов. | Статус: done

2026-06-17 | Действие: vendor crawl шаг4 — Playwright SPA PDF (discover+fetch); use_playwright PT; UI; pytest 29 PASS; live discover PT 0 (PDF уже search). | Коммит: `36fbaa4` | Хвост A: нет | Хвост B: нет | Хвост C: live discover 0 на PT seed — search покрывает | Следующий шаг: «ок» MAP crawl. | Статус: done

2026-06-17 | Действие: vendor crawl шаг3 — live ME+PT; фикс PDF fetch; 10 PDF/871 чанк; RAG tech_specialist OK; pytest 24 PASS. | Коммит: `dc5af2e` | Хвост A: Playwright шаг4 | Хвост B: нет | Хвост C: Tavily 432 | Следующий шаг: «ок» MAP или шаг4. | Статус: done

2026-06-17 | Действие: vendor crawl шаг2 — assess_crawl_text, quality_rejected stats, UI; pytest 23 PASS. | Коммит: `46a697e` | Хвост A: шаг3 live+PDF keys | Хвост B: нет | Хвост C: нет | Следующий шаг: шаг3 live прогон. | Статус: done

2026-06-17 | Действие: vendor crawl шаг1 — PDF search site:домен, max_pdf_pages, vendor_crawl_pdf*; UI; pytest 18 PASS; live search 0 без API keys. | Коммит: `1e4691e` | Хвост A: шаг2 фильтр мусора PDF | Хвост B: нет | Хвост C: Brave/Tavily keys для live PDF search | Следующий шаг: шаг 2 фильтр. | Статус: done

2026-06-17 | Действие: vendor crawl v2 — doc_urls, фильтр мусора, PDF, sitemap, приоритет; UI textarea; live 80/80 стр 582 чанка; pytest 13 PASS. | Коммит: `a319702` | Хвост A: Playwright SPA, голос doc_urls — BACKLOG | Хвост B: нет | Хвост C: PDF 0 на ME/PT (код готов) | Следующий шаг: «ок» MAP crawl; A/B промптов. | Статус: done

2026-06-17 | Действие: gate acceptance live table agents_gate_20260617_124414.json. | Коммит: `dfa1866` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: «ок» MAP crawl. | Статус: done

2026-06-17 | Действие: gate `[x]` MAP (апрув «ок» A+B+C); live vendor crawl ManageEngine+PT → 51 чанк RAG; конфиг vendor_crawl_config.json; ops acceptance/baseline/ISSUES. | Коммит: `57ccb65` | Хвост A: нет | Хвост B: фильтр woff2/next static — BACKLOG | Хвост C: economist-005 — опционально | Следующий шаг: «ок» MAP crawl; A/B промптов. | Статус: done

2026-06-17 | Действие: vendor crawl UI /ops/vendor-crawl + фон vendor_crawl_background; pytest 11 PASS; BACKLOG UI/cron закрыт. | Коммит: `880ea30` | Хвост A: нет | Хвост B: нет | Хвост C: gate C фон | Следующий шаг: «ок» MAP crawl. | Статус: done

2026-06-17 | Действие: Ф3 vendor crawl — config+crawl+API tech_specialist RAG; pytest 5 PASS; acceptance F3_VENDOR_CRAWL. | Коммит: `8bb5192` | Хвост A: UI Ops + cron расписание | Хвост B: BACKLOG UI/cron | Хвост C: gate C фон | Следующий шаг: «ок» MAP crawl; UI или gate. | Статус: done

2026-06-17 | Действие: перезапуск agents-only live gate (C) — GATE_CPU_PROFILE + SKIP_WARMUP; лог `gate_live_agents_20260617_*.log` (см. терминал); старый зависший убит. | Коммит: `9347802` | Хвост A: C в фоне | Хвост B: нет | Хвост C: нет | Следующий шаг: апрув → след. задача; дочитать лог. | Статус: in_progress

2026-06-17 | Действие: gate fix — agents-only warmup qwen2.5:3b, GATE_SKIP_WARMUP; Ollama 3 models RAM → медленно; agents фон 154500.log. | Коммит: `16dade2` | Хвост A: live agents C фон | Хвост B: нет | Хвост C: Ollama RAM — ISSUES | Статус: in_progress

2026-06-17 | Действие: Ф3 gate шаг 3 — live Hermes 36/36; enrich smoke 100%; GATE_CPU_PROFILE; agents-only фон; F3_GATE_TUNING_ACCEPTANCE; enrich-on-error агенты. | Коммит: `05302f1` | Хвост A: live agents C — фон gate_live_agents_*.log | Хвост B: нет | Хвост C: pytest starlette env FAIL — smoke python OK | Следующий шаг: дочитать agents лог → fix; `[x]` после «ок». | Статус: in_progress

2026-06-17 | Действие: Ф3 live gate шаг 3 старт — фон Ollama timeout 3600; лог gate_live_20260617_152400.log. | Коммит: `f32c3a6` / `b8d2d0e` | Хвост A: прогон в работе | Хвост B: нет | Хвост C: Tee+log-file | Следующий шаг: live re-gate. | Статус: done

2026-06-16 | Действие: Ф3 gate шаг 2 — rescue 36/36, enrich analyst/marketer, enrich smoke 100% @85%; acceptance; ISSUES Ollama timeout; pytest 112 PASS. | Коммит: `dc1220c` | Хвост A: live Ollama re-gate — не завершён (ReadTimeout) | Хвост B: нет | Хвост C: ISSUES live gate timeout | Следующий шаг: «ок» → [x] MAP или GPU re-gate. | Статус: done

2026-06-16 | Действие: Ф3 gate tuning шаг 1 — порог 85%, Hermes parse_intent, rescue/post_verify, enrich Tech/Economist/Strategist; pytest gate 59 PASS (WSL). | Коммит: `6efd107` | Хвост A: live full gate с Ollama — не гоняли | Хвост B: нет | Хвост C: нет | Следующий шаг: go live re-gate + acceptance. | Статус: done

2026-06-16 | Действие: DevTools MCP smoke B — массовая send 2/2 live (me@, сегмент без отрасли); acceptance F3. | Коммит: `43c7746` | Хвост A: нет | Хвост B: лимит писем/день — BACKLOG | Хвост C: нет | Следующий шаг: апрув «ок» B/C/D. | Статус: done

2026-06-16 | Действие: Live UI smoke B (Playwright): /email Массовая — чекбоксы, счётчик, 3 LLM, test ib@ PASS; скрипт + pytest testids. | Коммит: `f968fbe` | Хвост A: нет | Хвост B: лимит писем/день — BACKLOG (не в scope) | Хвост C: MCP DevTools errored — Playwright | Следующий шаг: апрув «ок» B/C/D. | Статус: done

2026-06-16 | Действие: docs README routes — chain_type, products_owned, campaign API; CHANGELOG ops. | Коммит: `f8a557b` | Хвост A: UI DevTools массовой — не гоняли (API smoke OK) | Хвост B: нет | Хвост C: нет | Следующий шаг: апрув «ок» B/C/D. | Статус: done

2026-06-16 | Действие: Этап C — products_owned, chain_type new/cross/upsell, nurture UI; smoke B API (industries+segment); pytest email 25; BACKLOG лимит/день. | Коммит: `78c66d4` | Хвост A: UI DevTools массовой — не гоняли (API smoke OK) | Хвост B: лимит писем/день → BACKLOG | Хвост C: нет | Следующий шаг: апрув «ок» B/C/D. | Статус: done

2026-06-15 | Действие: fix рассылка навсегда: leadMailingUi store + LeadMailingHost в root layout; кнопка openLeadMailing(lead); pytest ui 2. | Коммит: `f47dd70` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: проверить UI. | Статус: done

2026-06-15 | Действие: fix drawer «Рассылка»: portal в body (не обрезался overflow), onclose вместо bindable, z-100; EmailNurturePanel leadId; pytest portal 2. | Коммит: `e440e00` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: проверить UI / go B. | Статус: done

2026-06-15 | Действие: Рассылка с карточки лида: LeadMailingDrawer, реестр leadMailingTypes, кнопка «Рассылка» /leads/{id}, EmailNurturePanel lockLead/compact, deep link /email?lead&panel=nurture; smoke pytest 1. | Коммит: `14678ac` | Хвост A: нет | Хвост B: этапы B–D — BACKLOG | Хвост C: нет | Следующий шаг: go этап B или апрув. | Статус: done

2026-06-15 | Действие: Этап A UI: EmailNurturePanel на /email — превью LLM, тест ib@, запуск цепочки 1/3/20, история; API preview-llm/test-send; RAG строгий; pytest 18. | Коммит: `e425c77` | Хвост A: нет | Хвост B: этапы B–D — BACKLOG/plan | Хвост C: нет | Следующий шаг: go этап B (массовый сегмент) или апрув A. | Статус: done

2026-06-15 | Действие: LLM nurture пилот: marketer_nurture + start-llm API + smoke 3 письма MaxPatrol VM на ib@ (lead 3187 HOCHLAND); docs/modules/email_nurture.md; PRD_MAP; pytest 17. | Коммит: `da4d49f` | Хвост A: нет | Хвост B: расширение до 20 LLM касаний — BACKLOG после апрув | Хвост C: нет | Следующий шаг: апрув LLM nurture → go 20 касаний или Self-improvement. | Статус: done

2026-06-15 | Действие: Nurture хвост A закрыт: DevTools /ops/email таблица 4 chains OK; smoke_email_nurture_segment_live started=2 (chains 3–4); acceptance обновлён. | Коммит: `6f69239` | Хвост A: нет | Хвост B: LLM-тексты 20 касаний → BACKLOG (ждём апрув) | Хвост C: нет | Следующий шаг: апрув nurture → go LLM 20 касаний. | Статус: done

2026-06-15 | Действие: Nurture live: персонализация {{company}}/{{contact}}, start-segment API, smoke_email_nurture_live OK (lead 3191, emails_sent=1); pytest test_email_f3 14 passed; acceptance §Nurture; README routes/scripts. | Коммит: `1a2edd7` | Хвост A: DevTools /ops/email таблица — браузер без PUBLIC_SMARTCRM_API_KEY; segment batch live не гоняли | Хвост B: нет | Хвост C: LLM-генерация текстов nurture — не в scope (шаблоны детерминированные) | Следующий шаг: апрув nurture → go Ф3 Self-improvement. | Статус: done

2026-06-15 | Действие: Email live полный: me@ SMTP, FAQ live ib@→me@, fix threads API max(bool); DevTools /email /ops/email; smoke_email_faq_live.py; pytest 16. | Коммит: `82a5803` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: апрув Email → go Self-improvement. | Статус: done

2026-06-13 | Действие: me@ fix — IMAP/SMTP на imap.yandex.com (MX Яндекс); connect OK imported=50; ib@ regression OK; FAQ on me@; pytest 21; ISSUES me@ закрыта. | Коммит: `6ff7f4e` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф3 Self-improvement. | Статус: done

2026-06-13 | Действие: повтор me@ connect после смены пароля — IMAP Invalid login; relink OK scanned=100; FAQ smoke OK; pytest 21; DevTools busy. | Коммит: `a987047` | Хвост A: me@ — пароль не принят mail.agneko.am (cPanel) | Хвост B: нет | Хвост C: нет | Следующий шаг: webmail login me@ → верный пароль в .env. | Статус: done

2026-06-15 | Действие: F3 Email хвосты A: per-account pwd, insecure SSL, relink limit+index, FAQ smoke прайс; me@ IMAP Invalid login; pytest 21; relink live scanned=100 ~15s. | Коммит: `77419d9` | Хвост A: me@ connect — креды cPanel/webmail | Хвост B: нет | Хвост C: DevTools webmail me@ не проверен (browser busy) | Следующий шаг: сброс пароля me@ → connect; go Ф3 Self-improvement. | Статус: done

2026-06-15 | Действие: F3 Email live smoke: ib@ connect+sync+SMTP OK; me@ connect 400; smoke_email_smtp_send.py; acceptance §Live. | Коммит: `b207622` | Хвост A: me@agneko.am IMAP; relink timeout; FAQ inbound live | Хвост B: нет | Хвост C: me@ → ISSUES 🟡 | Следующий шаг: go Ф3 Self-improvement. | Статус: done

2026-06-15 | Действие: Ф3 §Email: FAQ autoreply, segment campaigns, 20-touch nurture, domain autolink; pytest 17 passed; MAP Email `[x]`; acceptance F3_EMAIL_AUTONOMY. | Коммит: `9a3be09` | Хвост A: live SMTP/IMAP смоук — не запускали | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф3 Self-improvement или ручной email смоук. | Статус: done

2026-06-15 | Действие: Ф3 §Voice: голосовой апрув да/нет, revise «короче», ops history; pytest 27 passed 1 skipped; MAP Voice `[x]`; acceptance F3_VOICE_APPROVAL. | Коммит: `cad831c` | Хвост A: live DevTools смоук approve/revise — не запускали (фронт не поднят) | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф3 Email или ручной смоук голоса. | Статус: done

2026-06-14 | Действие: §9 enrich голос: enrich_lead modal preview+апрув PATCH; pytest 21 passed; DevTools lead-card-enrich; MAP §9 закрыт. | Коммит: `cb0de76` | Хвост A: live voice modal в DevTools — timeout (контракт pytest OK) | Хвост B: нет | Хвост C: нет | Следующий шаг: go §1 Voice Layer или Ф3 gate. | Статус: done

2026-06-14 | Действие: §8 Лидоген+голос: voice navigate autorun /leadgen, won-portrait DB, lookalike modal; pytest 23 passed; DevTools autorun; MAP §8 закрыт. | Коммит: `0c3ae08` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go §1 Voice Layer или Ф3 gate. | Статус: done

2026-06-14 | Действие: §7 Тендеры: evaluate+document_text, voice search/list, linked_lead_id, link/create-lead UI; pytest 20 passed; MAP §7 закрыт. | Коммит: `829d340` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go §8. | Статус: done

2026-06-14 | Действие: §6 Аналитика+голос: period/source API+UI, conversionBySource, voice query navigate; pytest 47 passed; MAP §6 закрыт. | Коммит: `3911386` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go §7. | Статус: done

2026-06-14 | Действие: §5 доп — Hermes prompt versions: store+API+UI improve; PromptVersionPanel общий; pytest 27 passed; хвост A закрыт. | Коммит: `60a045b` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go §6. | Статус: done

2026-06-14 | Действие: Ф2 §5 — версии промптов Ops: store, restore, compare, UI /ops/agents; pytest 26 passed; §5 закрыт. | Коммит: `a883410` | Хвост A: Hermes prompt versioning — не делали | Хвост B: нет | Хвост C: нет | Следующий шаг: go §6 аналитика. | Статус: done

2026-06-14 | Действие: RAG хвост BACKLOG + §9 enrich карточка: LLM flags, page_fetch, кнопка /leads/{id}; pytest 31 passed. | Коммит: `934a84f` | Хвост A: quality gate ≥85% — Ф3, не делали | Хвост B: нет | Хвост C: нет | Следующий шаг: go §5 или Ф3 gate. | Статус: done

2026-06-14 | Действие: Ф2 §4 п.4 — кэш enrich (company+ИНН+industry, TTL 24ч): enrich_cache, force API/UI, pytest 14 passed; §4 закрыт. | Коммит: `9dcf749` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go §5 Self-improvement. | Статус: done

2026-06-14 | Действие: Ф2 §4 п.3 — save везде в /search: SearchSaveRagBar на 5 вкладках; pytest 7+smoke OK. | Коммит: `41c8f55` | Хвост A: §4 п.4 enrich cache | Хвост B: нет | Хвост C: нет | Следующий шаг: go §4 п.4. | Статус: done

2026-06-14 | Действие: Ф2 §4 п.2 — факты диалога→RAG: dialogue_facts, ingest-dialogue, auto ops/voice, UI /agents; pytest 7 passed. | Коммит: `a27bf1c` | Хвост A: §4 п.3–4 (save everywhere, enrich cache) | Хвост B: LLM facts structure — BACKLOG (как Q&A) | Хвост C: нет | Следующий шаг: go §4 п.3. | Статус: done

2026-06-14 | Действие: BACKLOG+docs — quality gate Ф3 тюнинг (baseline 72.2/60/73.3%, цель ≥85% все); Ф2 не закрываем по gate. | Коммит: `f5d4266` | Хвост A: сам тюнинг не делали | Хвост B: запись в BACKLOG + AGENTS_GATE_TUNING_BASELINE | Хвост C: нет | Следующий шаг: go §4 п.2. | Статус: done

2026-06-14 | Действие: Ф2 §4 п.1 — авто-чанки RAG: relevance, auto-ingest-rag, UI /search; pytest 10 passed. | Коммит: `c1302fc` | Хвост A: §4 п.2–4 (факты, save everywhere, enrich cache) | Хвост B: LLM Q&A structure — BACKLOG | Хвост C: нет | Следующий шаг: go §4 п.2. | Статус: done

2026-06-14 | Действие: Ф2 §3 п.407 — голос email: list/write/send, voiceEmailContext, marketer orchestrator; pytest 33 passed. | Коммит: `cbc44c0` | Хвост A: §4 RAG / voice E2E MAP | Хвост B: нет | Хвост C: нет | Следующий шаг: §3 закрыт → go §4 или gate. | Статус: done

2026-06-14 | Действие: Ф2 §3 п.406 — апрув перед отправкой: EmailApproveModal, voice send_email preview+thread reply; pytest 8 passed. | Коммит: `1b3cfb3` | Хвост A: п.407 голос email | Хвост B: нет | Хвост C: нет | Следующий шаг: go §3 п.407. | Статус: done

2026-06-14 | Действие: Ф2 §3 п.405 — анализ типа + черновик: POST /threads/{id}/analyze, UI модал, pytest 15 passed. | Коммит: `2216377` | Хвост A: п.406–407 (апрув, голос email) | Хвост B: нет | Хвост C: нет | Следующий шаг: go §3 п.406 апрув. | Статус: done

2026-06-14 | Действие: live full quality gate 111 кейсов — фон; ollama serve + gate_full_20260614_1628.log; backend email+bitrix auto-sync OK. | Коммит: `6e28c5f` | Хвост A: дождаться артефакта agents_gate_*.json | Хвост B: §3 п.405 черновик после анализа | Хвост C: нет | Следующий шаг: итог gate + go п.405. | Статус: in_progress

2026-06-14 | Действие: cleanup — удалён email/[mailbox].svelte; BACKLOG me@ закрыт; PRD инфра п.5 ✅; pytest 9 passed. | Коммит: `1bd3c95` | Хвост A: п.405–407 email | Хвост B: нет | Хвост C: нет | Следующий шаг: go §3 п.405 черновик. | Статус: done

2026-06-14 | Действие: Ф2 §3 п.404 — список /email: enriched threads, emailListLogic, UI sync bar; pytest 13 passed. | Коммит: `8f6f3ed` | Хвост A: п.405–407 (черновик, апрув, голос) | Хвост B: legacy email/[mailbox].svelte | Хвост C: me@agneko.am — BACKLOG | Следующий шаг: go §3 п.405 черновик. | Статус: done

2026-06-14 | Действие: Ф2 §3 п.403 — фоновый IMAP-синк, poll loop, GET /sync/status; pytest 19 passed. | Коммит: `20ce084` | Хвост A: п.404–407 email (UI, черновик, апрув, голос) | Хвост B: нет | Хвост C: me@agneko.am отдельный пароль — BACKLOG | Следующий шаг: go §3 п.404 `/email`. | Статус: done

2026-06-14 | Действие: Ф2 §3 п.402 — IMAP/SMTP env: email_config, bootstrap API, acceptance; pytest 20 passed. | Коммит: `2b84cfd` | Хвост A: п.403–407 email (фон, UI, черновик, апрув, голос) | Хвост B: нет | Хвост C: me@agneko.am отдельный пароль — BACKLOG | Следующий шаг: go §3 п.403 фоновый синк. | Статус: done

2026-06-14 | Действие: хвост B/C — lookalike-import API + VoiceActionHost approve; pytest 8 passed. | Коммит: `bf3e4d8` | Хвост A: нет | Хвост B: нет | Хвост C: check_agent_step paths (уже в d686a32) | Следующий шаг: go §3 email IMAP/SMTP. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.396 find_similar_clients — analyst∥marketer→modal lookalike; pytest 6 passed; §2 оркестрация закрыта. | Коммит: `d9d5f4b` | Хвост A: нет (§2 done) | Хвост B: lookalike POST /api/leads → §8 MAP | Хвост C: fix VoiceActionHost modalAction | Следующий шаг: go §3 email или §8 lookalike. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.395 weekly_report — analyst∥economist∥marketer→modal KPI; pytest 7 passed. | Коммит: `c799a4d` | Хвост A: §2 п.396 похожие клиенты | Хвост B: нет | Хвост C: fix strategist f-string syntax | Следующий шаг: go §2 п.396. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.394 evaluate_tender — tech∥economist→modal; pytest 15 passed. | Коммит: `96b9843` | Хвост A: §2 п.395–396 | Хвост B: нет | Хвост C: нет | Следующий шаг: go §2 п.395 отчёт. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.393 analyze_and_email — analyst∥marketer→modal; pytest 48 passed. | Коммит: `8af96ec` | Хвост A: §2 п.394–396 | Хвост C: fix pipeline agents до run_agents | Следующий шаг: go §2 п.394 тендер. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.3 синтез → modal — synthesis.py, VoiceActionHost, pytest 44 passed. | Коммит: `338d4f5` | Хвост A: §2 п.393–396 (именованные сценарии) | Хвост B: нет | Хвост C: нет | Следующий шаг: go §2 п.393 анализ+письмо. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.2 parallel fanout 2+ — fanout_parallel.py, Hermes parallel, pytest 20 passed. | Коммит: `1460d62` | Хвост A: §2 п.392–396 (синтез модалка, сценарии) | Хвост B: нет | Хвост C: нет | Следующий шаг: go §2 п.392 синтез модалка. | Статус: done

2026-06-14 | Действие: Ф2 §2 п.1 LangGraph supervisor — выборочный fanout; pytest 15 passed. | Коммит: `d3ca7e0` | Хвост A: §2 п.2–7 (сценарии, синтез модалка) | Хвост B: нет | Хвост C: нет | Следующий шаг: go §2 п.2 parallel fanout или сценарии. | Статус: done

2026-06-14 | Действие: фон live LLM eval модулей (--full 56 кейсов Groq+Ollama); скрипт run_eval_modules_live.py. | Коммит: `fb72e24` | Хвост A: дождаться артефакта modules_live_*.json | Хвост B: нет | Хвост C: нет | Следующий шаг: итог eval + §2 fanout. | Статус: in_progress

2026-06-14 | Действие: Ф2 §1 Voice Layer закрыт — UI voice_action + rescue eval + smoke 72 passed. | Коммит: `f2b618e` | Хвост A: live LLM eval модулей (опц.) | Хвост B: нет | Хвост C: нет | Следующий шаг: go §2 fanout или §8 leadgen+голос. | Статус: done

2026-06-13 | Действие: Ф2 §1 Hermes module+ui_action (email/search/analytics/agents/rag); smoke 47+10 pytest. | Коммит: `42b14d1` | Хвост A: Voice Layer UI п.2–5; LLM eval analytics/RAG | Хвост B: UI period/minScore, send_email live → BACKLOG | Хвост C: нет | Следующий шаг: go Voice Layer UI или §2 fanout. | Статус: done

2026-06-13 | Действие: push 29 коммитов main → origin/main (1b6293d..81dbc32). | Коммит: — (push only) | Хвост A: full live gate | Хвост B: Ф2 go+номер | Хвост C: runtime не в git | Следующий шаг: Ф2 или gate. | Статус: done

2026-06-13 | Действие: ops упаковка session/phase1/phase2/baselines/debt + README; ссылки, pre-commit. | Коммит: `036fd61` | Хвост A: layout кода → debt | Хвост B: Ф2 ждёт go | Хвост C: push ждём go | Следующий шаг: задача → push. | Статус: done

2026-06-13 | Действие: переход Ф1→Ф2 — PHASE2_ENTRY, HANDOFF, MAP. | Коммит: `db8960e` | Хвост A: full gate | Хвост B: Ф2 go | Хвост C: runtime | Следующий шаг: push. | Статус: superseded

2026-06-13 | Действие: smoke gate artifact + full gate 🔄 + cp1251; MAP 🟡; шаг 7 pytest 34. | Коммит: `450e981` | Хвост A: full gate green | Хвост B: MAP [x] после ok | Хвост C: marketer/tech fail | Следующий шаг: дождаться full gate. | Статус: superseded

2026-06-13 | Действие: шаг 7 done — pytest gate 34 passed, acceptance CI note; ops CHANGELOG+HANDOFF. | Коммит: `c47a007` | Хвост A: live gate smoke+full | Хвост B: MAP 🔲 | Хвост C: hermes3 re-pull | Следующий шаг: smoke после pull. | Статус: done

2026-06-13 | Действие: gate CLI --log-file, set_gate_logger, ASCII лог, sort артефактов; pytest scripts+artifacts. | Коммит: `60d9a51` | Хвост A: live smoke agents-only | Хвост B: MAP 🔲 | Хвост C: cp1251 fixed | Следующий шаг: smoke limit 2 в фоне. | Статус: done

2026-06-13 | Действие: live gate smoke прерван на warmup (CPU). | Коммит: `71b2206` tools | Хвост A: MAP 🔲 | Хвост B: шаг 7 pytest частично | Хвост C: Unicode | Следующий шаг: перезапуск smoke. | Статус: superseded

2026-06-13 | Действие: fix Vite 500 — {@const} под {#if}/{#each} в AgentGatePanel+insights. | Коммит: `273aca8` | Хвост A: live gate MAP 🔲 | Хвост B: шаг 7 pytest | Хвост C: нет | Следующий шаг: gate с лимитами или full. | Статус: done

2026-06-13 | Действие: шаг 6 петля обучения — gate_delta was→became %; /ops/tuning импорт failed; insights+eval дельта; pytest 13 gate. | Коммит: `7be7bdb` | Хвост A: live gate MAP 🔲 | Хвост B: must_contain tuning | Хвост C: нет | Следующий шаг: full gate --write-acceptance. | Статус: done

2026-06-13 | Действие: UI gate eval+insights финал — вкладки Hermes/gate, download JSON, режимы+лимиты, bulk→eval-failed-gate, insights pass rate; API download/ensure/bulk; pytest 15; fix import $components. | Коммит: `596d2e1` | Хвост A: live full gate MAP 🔲 | Хвост B: EVAL_OLLAMA_TIMEOUT=1200 | Хвост C: agents-only оборван analyst | Следующий шаг: утренний run_agents_quality_gate --write-acceptance. | Статус: done

2026-06-12 | Действие: agents quality gates шаг 5 — UI eval+insights, API latest/failed→dataset; BACKLOG незакрытый live; 9 pytest gate. | Коммит: `27e4925` | Хвост A: ночной full gate Hermes+агенты | Хвост B: [x] MAP после зелёного | Хвост C: agents-only фон оборвался | Следующий шаг: live gate EVAL_OLLAMA_TIMEOUT=1200. | Статус: done

2026-06-12 | Действие: agents quality gates шаг 4 — acceptance_sync, --write-acceptance, GATE_GAPS, BACKLOG; live --agents-only 🔄; MAP 🔲. | Коммит: `2161abc` | Хвост A: полный live Hermes+агенты | Хвост B: UI шаг 5 | Хвост C: Hermes CPU timeout | Следующий шаг: дождаться live 5 агентов / Hermes ночью. | Статус: done

2026-06-12 | Действие: agents quality gates шаг 3 — run_agents_quality_gate.py, POST /api/ops/eval/agents-gate, Ollama smoke+full run; 16 pytest gate. | Коммит: `adf4568` | Хвост A: полный live gate ≥ порогов | Хвост B: UI /ops/eval шаг 5 | Хвост C: Hermes CPU медленный — EVAL_OLLAMA_TIMEOUT=600 | Следующий шаг: дождаться полного gate / тюнинг. | Статус: done

2026-06-12 | Действие: agents quality gates шаг 2 — eval/agents 15×5, core/agent_eval, seed+pytest 12. | Коммит: `eecc65a` | Хвост A: run_agents_quality_gate.py | Хвост B: live Ollama gate | Хвост C: UI /ops/eval | Следующий шаг: шаг 3 gate script. | Статус: done

2026-06-12 | Действие: agents quality gates шаг 0–1 — пороги, AGENTS_LEARNING_MAP, AGENTS_QUALITY_GATE_ACCEPTANCE, PRD_MAP/BACKLOG; Ollama eval. | Коммит: `363d1dd` | Хвост A: eval-кейсы+скрипт gate | Хвост B: UI /ops/eval | Хвост C: me@agneko.am | Следующий шаг: шаг 2 кейсы. | Статус: done

2026-06-12 | Действие: coverage hygiene — PR checklist+тест на фичу (4c09615), smoke 51.7% (1ab5410), CI cov term (3ab71b3); 516 pytest. | Коммит: `3ab71b3` | Хвост A: MAP п.3–5 | Хвост B: me@agneko.am | Хвост C: нет | Следующий шаг: push+go Ф2. | Статус: done

2026-06-12 | Действие: push+CI green run #3 + branch protection main (pytest+smoke required). | Коммит: `7346885` | Хвост A: MAP п.3–5 milestones | Хвост B: me@agneko.am | Хвост C: нет | Следующий шаг: go Ф2. | Статус: done

2026-06-12 | Действие: CI green path — fix rescue create_task до list_leads (eval-007); HERMES_ENABLE_FASTPATH=0 в ci.yml. | Коммит: `6fca8ca` | Хвост A: push+branch protection | Хвост B: MAP п.3–5 | Хвост C: нет | Следующий шаг: push. | Статус: done

2026-06-11 | Действие: pytest clean — email assert, filterwarnings starlette, live_eval в доках; 500 passed 0 warnings, ci_smoke OK. | Коммит: `f3974c2` | Хвост A: push+branch protection GitHub | Хвост B: MAP п.3–5 milestones | Хвост C: me@agneko.am | Следующий шаг: push. | Статус: done

2026-06-11 | Действие: fix venv — cryptography в requirements.txt; доки python -m pytest+venv; CI python -m pytest; тест deps. | Коммит: `58d7a2d` | Хвост A: (.venv) pip install -r requirements.txt заново | Хвост B: push+branch protection | Хвост C: me@agneko.am | Следующий шаг: в venv `python -m pytest -q`. | Статус: done

2026-06-11 | Действие: CI — GitHub Actions ci.yml (pytest+smoke jobs), ci_smoke.py ops/leads/voice, CI_BASELINE.md; локально 498+132 pytest OK. | Коммит: `0477431` | Хвост A: branch protection в GitHub вручную | Хвост B: cov fail-under в CI — отдельно | Хвост C: me@agneko.am пароль | Следующий шаг: push + включить required checks. | Статус: done

2026-06-11 | Действие: Coverage — pytest-cov, requirements-dev.txt, .coveragerc, baseline 51.4%, live_eval marker, fix voice str(e)+RAG stubs+brave backoff; 498 pytest. | Коммит: `878e159` | Хвост A: CI cov gate — отдельный шаг | Хвост B: me@agneko.am пароль | Хвост C: нет | Следующий шаг: go Ф2 или CI cov. | Статус: done

2026-06-11 | Действие: Email fix — парсинг дат IMAP, repair 362 UID, inbox filter (support/pricing), DevTools=Yandex сегодня. | Коммит: `dae7f08` | Хвост A: me@agneko.am — пароль | Хвост B: EMAIL_IMAP_FETCH_LIMIT=500 в .env | Хвост C: нет | Следующий шаг: go Ф2 рассылки или Агенты. | Статус: done

2026-06-11 | Действие: Email Sync — POST /sync, IMAP SINCE, кнопка 🔄 на /email, smoke_email_sync, 7 pytest, live+DevTools ib@ OK. | Коммит: `b20b2d9` | Хвост A: me@agneko.am — пароль | Хвост B: автофон sync → Ф2 | Хвост C: нет | Следующий шаг: go Агенты MAP или Ф2 рассылки. | Статус: done

2026-06-11 | Действие: Email connect — `emailStorage.js` apiFetch, `EMAIL_IMAP_FETCH_LIMIT`, smoke+mock pytest, ib@agneko.com live (504 треда), DevTools /email OK; acceptance+MAP. | Коммит: `6d84234` | Хвост A: me@agneko.am — пароль mail.agneko.am | Хвост B: рассылки/UX почты → Ф2 | Хвост C: нет | Следующий шаг: go Агенты MAP или пароль me@. | Статус: done

2026-06-11 | Действие: Ops Ф1 — аудит 12 вкладок (реальные API), `smoke_ops_baseline.py` 33 pytest, DevTools /ops+/agents, acceptance+MAP. | Коммит: `d561372` | Хвост A: нет | Хвост B: версионирование промптов → Ф2 | Хвост C: нет | Следующий шаг: go Агенты MAP или Ф2. | Статус: done

2026-06-11 | Действие: PDF extract — `smoke_tender_pdf_extract.py`, curl/PowerShell в acceptance (корневой .env, пути cwd), в tenders baseline. | Коммит: `0350f79` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ops или Ф2. | Статус: done

2026-06-11 | Действие: аналитика Ф1 — KPI /leads/analytics, API summary/export, убран mock /analytics, 10 pytest, DevTools+Puppeteer (3184 лида, CSV 200). | Коммит: `5eeeff8` | Хвост A: нет | Хвост B: голос по метрикам → Ф2 | Хвост C: средний чек/цикл «—» пока нет выигранных | Следующий шаг: go Ops перепроход или Ф2. | Статус: done

2026-06-11 | Действие: apiFetch в tenderApi + DevTools UI PDF OK (23 симв, extract 200). | Коммит: `21c88fd` | Хвост A: frontend/.env локально (gitignore) | Хвост B: нет | Хвост C: нет | Следующий шаг: go Ф2. | Статус: done

2026-06-11 | Действие: PDF→текст — `/documents/extract`, UI upload→analyze, pytest+fixture, DevTools /tenders (uvicorn :8000 завис — перезапуск). | Коммит: `1f3eaeb` | Хвост A: нет | Хвост B: live UI upload после рестарта API | Хвост C: нет | Следующий шаг: go Ф2. | Статус: done

2026-06-11 | Действие: тендеры хвосты закрыты — Serper/Tavily, tender_saved, analyze LLM, Gosplan UI, 29 pytest. | Коммит: `21e9e1d` | Хвост A: PDF→analyze опц. | Хвост B: live spot-check ключей 🟢 | Хвост C: нет | Следующий шаг: go Ф2 §8 или §1 Voice. | Статус: done

2026-06-11 | Действие: тендеры Ф1 baseline — MAP таблица, smoke+pytest, acceptance, fix search 400, BACKLOG хвосты. | Коммит: `2acf0da` | Хвост A: нет | Хвост B: Мои/Архив UI, Gosplan tail 🟡 | Хвост C: Ф2 §7 агент MOCK | Следующий шаг: go Ф2 или тендеры п.4. | Статус: done

2026-06-11 | Действие: doc-sync — PRD навигация+Ф1✅; MAP TOC/DoD Ф2/сценарии Ф2/coverage/сводка; LEADGEN_VOICE_ACCEPTANCE.md; waitForWsOpen. | Коммит: `30f7460` | Хвост A: нет | Хвост B: spot-check approve/fanout 🟡 | Хвост C: Ф2 §8 live UI | Следующий шаг: Ф2 §8 live или §1 Voice Layer — ждём go. | Статус: done

2026-06-11 | Действие: mic E2E — WS audio tests, dev voice-simulate-mic, leadgen voice smoke; Ф1 DoD 6/6; MAP/BACKLOG/HANDOFF. | Коммит: `8d2d196` | Хвост A: нет | Хвост B: spot-check approve/fanout 🟡 | Хвост C: Ф2 §8 live UI pipeline | Следующий шаг: Ф2 §8 live или §1 Voice Layer. | Статус: done

2026-06-10 | Действие: MAP-doc финал — Поиск/RAG таблица, шапки Лиды/Баллы/Поиск; HANDOFF «MAP выровнен». | Коммит: `2890523` | Хвост A: нет (MAP-doc закрыт) | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: go Ф2 оч.1/5 | Следующий шаг: продукт по `go`. | Статус: done

2026-06-10 | Действие: MAP п.7–10 — quality gates агентов, безопасность, инфра прод, coverage; langgraph.md; сводка MAP. | Коммит: `6a6c516` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: go Ф2 оч.1/5 | Следующий шаг: MAP-doc хвост или `go`. | Статус: done

2026-06-10 | Действие: MAP п.6 — порядок Ф2 очередь 1–9, фундамент/позже, §1≠лиды Ф1, go по номеру; HANDOFF+BACKLOG. | Коммит: `d76b604` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: go кандидаты оч.1 или оч.5 | Следующий шаг: MAP-doc или `go` Ф2. | Статус: done

2026-06-10 | Действие: MAP п.5 — 7 бизнес-сценариев Ф1, привязка к блокам, процесс «сценарий→таблица»; README. | Коммит: `55a888d` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон 🔴, DoD п.6 | Хвост C: spot-check 🟡 | Следующий шаг: MAP-doc п.6 порядок Ф2 / `go`. | Статус: done

2026-06-10 | Действие: MAP п.4 DoD Ф1 — 6 критериев, dev-gates ссылка, п.5 голос код/E2E, п.6 «ок в Ф2»; BACKLOG sync. | Коммит: `418827f` | Хвост A: MAP-doc дубль Поиск/RAG, шапки | Хвост B: микрофон E2E 🔴, п.6 ждём | Хвост C: spot-check 🟡 | Следующий шаг: MAP-doc п.5 или `go` Ф2. | Статус: done

2026-06-10 | Действие: MAP п.3 — легенда [x] vs ⚠️, колонка Статус в «Голос», сводка «частично», BACKLOG как снять ⚠️; README. | Коммит: `0e7e0ff` | Хвост A: MAP-doc дубль Поиск/RAG, шапки таблиц | Хвост B: микрофон E2E 🔴 | Хвост C: п.3/5 spot-check 🟡 | Следующий шаг: MAP-doc или микрофон руками. | Статус: done

2026-06-10 | Действие: хвост Ф1 — указатель в MAP, канон BACKLOG; убраны ложные 🔴 Hermes/voice_action; HANDOFF без дубля таблицы; BACKLOG п.98+инфра. | Коммит: `c27517b` | Хвост A: MAP-doc: дубль Поиск/RAG, шапки таблиц | Хвост B: микрофон E2E 🔴 | Хвост C: нет | Следующий шаг: MAP-doc п.3 или `go` продукт. | Статус: done

2026-06-10 | Действие: PRD_MAP выровнен — легенда, DoD Ф1, сценарии, убраны дубли, голос ⚠️, хвост→BACKLOG, порядок Ф2, безопасность/инфра прод; HANDOFF+CHANGELOG. | Коммит: `59b0af7` | Хвост A: нет | Хвост B: микрофон E2E 🔴 | Хвост C: нет | Следующий шаг: `go` продукт (Ф2 §8 / §1 / микрофон руками). | Статус: done

2026-06-10 | Действие: leadgen автосейв портрет+кластер — `persist_autosave.py`, `save_to_crm` в API, UI `leadgen-autosave-crm`, `crm_saved[]`, 24 pytest autosave block. | Коммит: `5ef5b3f` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: голосовые Ф2. | Статус: done

2026-06-10 | Действие: leadgen dedup ИНН (вариант A) — `persist_card.py`, update по ИНН, `crm_lead_created`, UI «Обновлён», 14 pytest. | Коммит: `3dfa15d` | Хвост A: нет | Хвост B: autosave портрет/кластер — Ф2 | Хвост C: нет | Следующий шаг: голосовые Ф2. | Статус: done

2026-06-10 | Действие: leadgen автосейв CRM — `crm_threshold.py`, 10 pytest, smoke, DevTools E2E скор 84 → лид #3187; усилен commit-ops (override User Rules); удалены `CURSOR_USER_RULES_*.md`. | Коммит: `a8f4c6a` | Хвост A: нет | Хвост B: dedup по ИНН в CRM — BACKLOG | Хвост C: persist `_fmt_money` import | Следующий шаг: голосовые Ф2. | Статус: done

2026-06-10 | Действие: убран конфликт commit в HANDOFF; EN-паттерны в `check_rules_commit_conflict.py`; `CURSOR_USER_RULES_SNIPPET.md`. | Коммит: `8bc2554` | Хвост A: snippet в Cursor Settings — вручную у пользователя | Хвост B: нет | Хвост C: нет | Следующий шаг: `go` шаг 2 warnings. | Статус: done

2026-06-10 | Действие: leadgen кластер/холдинг — API+integration tests, smoke live 4 субъекта Хохланд, testid UI, DevTools MCP POST cluster 200; portrait Groq review → BACKLOG Ф2; `LEADGEN_CLUSTER_ACCEPTANCE.md`. | Коммит: `c291a32` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: автосохранение CRM или Ф2. | Статус: done

2026-06-10 | Действие: portrait progress UI (`portraitProgress.js`, testids) + DevTools E2E **user-chrome-devtools** MCP (progress «Загружаем эталон…», POST portrait 200, 3 кандидата). | Коммит: `3ebb811` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: следующий MAP. | Статус: done

2026-06-10 | Действие: хвост ИНН 1–6 — `leadgen/inn_constants.py`, импорты smoke/API, docs Хохланд, asyncio.run, DevTools portrait E2E (cursor-ide-browser POST 200, 3 кандидата), `test_inn_constants.py` 10 pytest. | Коммит: `1bb0645` | Хвост A: нет | Хвост B: нет | Хвост C: user-chrome-devtools MCP errored — cursor-ide-browser | Следующий шаг: следующий пункт MAP. | Статус: done

2026-06-10 | Действие: шаг 1 «странный эталон» — развод ИНН: мок `7707070010` ТехноСофт, live `5040048921` Хохланд; `inn_constants.py`, `LEADGEN_INN_FIX.md`; smoke portrait 9 pytest + live 3 кандидата (gaps=[]); hook utf-8 fix `session_state_validate.py`. | Коммит: `4de231d` | Хвост A: pytest warnings (asyncio/email) | Хвост B: нет | Хвост C: DevTools portrait (MCP недоступен) | Следующий шаг: шаг 2 warnings. | Статус: done

2026-06-09 | Действие: pre-commit hook (`29f5164`) + ops/UTF-8 fix (`26374f8`); hook установлен, validate OK. | Коммит: `b83940d` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: портрет leadgen в git. | Статус: done

2026-06-09 | Действие: commit-ops — явно: commit без согласования пользователя; зачистка SESSION_STATE портрет. | Коммит: `525fa19` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: `go` портрет в git. | Статус: done

2026-06-09 | Действие: PRD_MAP leadgen «Поиск по портрету» — API only reference_inn, fix re/_parse_json_safe, select лида CRM, smoke 9 pytest + live 3 кандидата, DevTools fetch 200; `LEADGEN_PORTRAIT_ACCEPTANCE.md`. | Хвост A: кластер MAP | Хвост B: нет | Хвост C: 3 бага portrait pipeline | Следующий шаг: портрет leadgen в git + `go` кластер. | Статус: in_progress

2026-06-09 | Действие: iron commit — усилены `commit-ops`, `check_agent_step`, `check_rules_commit_conflict`; зачистка SESSION_STATE; ответ только после commit. | Коммит: `7eba527` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: `go` портрет. | Статус: done

2026-06-08 | Действие: правило хвоста прогона A/B/C — `commit-ops`, `task-workflow`, `AGENTS.md`, `RULES_MATRIX`, `check_agent_step.py`; три сценария: план не сделано / BACKLOG в прогоне / доп. починки. | Коммит: `5c0b636` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Следующий шаг: PRD_MAP. | Статус: done

2026-06-09 | Действие: PRD_MAP Ф2 — §4 кэш enrich, §9 кнопка на карточке лида; BACKLOG + SEARCH_ENRICH_LEAD_ACCEPTANCE синхрон. | Следующий шаг: по `go` следующий пункт. | Статус: done

2026-06-09 | Действие: enrich хвост — Brave cache/semaphore, Checko/ИНН, LinkedIn/ЛПР запросы, scrape сайта, CRM select+PATCH; 28 pytest; PRD_MAP §2 enrich ✅. | Следующий шаг: Ф2 авто-чанки. | Статус: done

2026-06-09 | Действие: enrich-lead smoke — Brave fix, API validation, 20 pytest, live Сбербанк phone/email/website; DevTools таб enrich OK; `SEARCH_ENRICH_LEAD_ACCEPTANCE.md`; PRD_MAP enrich ✅; блок RAG закрыт. | Следующий шаг: Ф2 авто-чанки или другой блок MAP. | Статус: done

2026-06-08 | Действие: RAG п.5 save из поиска — `source_url` в metadata, `test_rag_ingest_batch*.py` 6 pytest, `smoke_rag_save_from_search.py`; DevTools `/search` таб RAG → 1 чанк cbr.ru; `SEARCH_RAG_SAVE_ACCEPTANCE.md`; блок п.1–5 ✅. | Следующий шаг: enrich-lead smoke или Ф2. | Статус: done

2026-06-08 | Действие: RAG п.4 upload PDF/txt — `test_rag_upload.py`, `test_rag_upload_api.py`, `smoke_rag_upload.py` 8 pytest; DevTools `/rag` текст «В базу» 1 чанк + PDF в источниках; `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`; PRD_MAP п.4 ✅. | Следующий шаг: `go` п.5 save из поиска. | Статус: done

2026-06-08 | Действие: RAG п.3 Chroma — `test_rag_api.py`, `smoke_rag_chroma.py` 11 pytest, live 1592 чанка (economist 960 / all 624 / marketer 8); `/rag` apiFetch; `SEARCH_CHROMA_ACCEPTANCE.md`; PRD_MAP п.3 ✅. DevTools: серверы не запущены — pytest + прямой count Chroma OK. | Коммит: `97778b2` | Следующий шаг: `go` п.4. | Статус: done

2026-06-08 | Действие: зачистка правил — только безусловный `git commit` при закрытии шага; убраны отложенные формулировки в `.mdc`, `AGENTS.md`, ops; усилен `check_rules_commit_conflict.py`. | Коммит: `02ef689` | Следующий шаг: PRD_MAP RAG п.3. | Статус: done

2026-06-08 | Действие: коммит+push RAG п.1 хвост + п.2 — `97778b2` (код/тесты/acceptance; ops CHANGELOG/HANDOFF уже были в HEAD). | Следующий шаг: `go` RAG п.3 Chroma. | Статус: done

2026-06-08 | Действие: RAG п.2 — 6 режимов перепроход: `test_search_modes_api.py` + `test_search_modes.py`, `smoke_search_modes.py` 19 pytest + live free; DevTools 6 табов + free live 10 результатов; `SEARCH_MODES_ACCEPTANCE.md` (сделано/НЕ сдали); PRD_MAP п.2 ✅; BACKLOG п.3–5. | Коммит: `97778b2` | Статус: done

2026-06-08 | Действие: RAG п.1 хвост — `/search` все API через `apiFetch`/`apiPost`; `smoke_search_providers.py` грузит `.env`; DevTools UI «Сбербанк»→«Найти»→7 результатов; `SEARCH_PROVIDERS_ACCEPTANCE.md` таблица; `BACKLOG.md`. | Коммит: `97778b2` | Статус: done

2026-06-08 | Действие: PRD_MAP RAG п.1 — перепроход Serper/Brave/Tavily: фикс cache в `company_search.py`, `test_search_providers.py` + API smoke, `smoke_search_providers.py` 11 pytest; DevTools `/search` — 3 ключа ✓, `/run` Сбербанк → 7 результатов; `SEARCH_PROVIDERS_ACCEPTANCE.md`. | Коммит: `eb138bd` | Следующий шаг: `go` RAG п.2 «6 режимов поиска». | Статус: done

2026-06-08 | Действие: BACKLOG § «Ручная работа (только ты)» — таблица Фаза/блок/пункт: 🔴 микрофон E2E (Ф1 п.1), 🟡 approve+fanout spot-check, 🟢 live Groq опционально, Ф2 Битрикс туннель; синхрон «Активный хвост». | Следующий шаг: пользователь — строка 🔴 в BACKLOG; после OK — строка в SESSION_STATE. | Коммит: `b4ca224` | Статус: done

2026-06-08 | Действие: хвост BACKLOG «Голос → лиды» #2–#11 (кроме #1 микрофон) — add_communication, fuzzy stage, чипы, fanout UI, health/whisper, email field_validator, eval-034–036, approve testids, smoke_hermes_leads_live; `VOICE_LEADS_TAIL_ACCEPTANCE.md`; pytest smoke зелёный. | Коммит: `352eed2` | Статус: done

2026-06-08 | Действие: п.5 смоук голоса — S01–S09 pytest 23 + chain 47; DevTools localhost:5174 API+WS OK; `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md`; BACKLOG сводный хвост блока. | Следующий шаг: блок «Голос → лиды» закрыт → Фаза 2 или Битрикс. | Статус: done

2026-06-08 | Действие: п.4 полные интенты — analyze_lead, lead_history, фильтры stage/industry/city; smoke_hermes_leads_full 34 passed; BACKLOG хвост п.4. | Следующий шаг: `go` п.5 смоук голосовых. | Статус: done

2026-06-08 | Действие: voice_action п.3 — `voice_action.py`, WS событие, фронт VoiceActionHost + stores; 8 pytest + smoke; `VOICE_ACTION_ACCEPTANCE.md`, PRD_MAP [x]. | Следующий шаг: `go` п.4 полные интенты или п.5 смоук. | Статус: done

2026-06-08 | Действие: BACKLOG — отложены pgvector, LiveKit, Litestar (триггеры + фазы MAP). | Следующий шаг: `go` хвост Ф1 голос/Hermes. | Статус: done

2026-06-08 | Действие: PRD_NOTES §CHANGELOG → шапка `operations/session/CHANGELOG.md`; NOTES — ссылка на канон. | Следующий шаг: хвост Ф1 Hermes/voice или `go` Фаза 2. | Статус: done

2026-06-08 | Действие: BACKLOG — таблица «Осталось Голос→лиды» (п.3 voice_action, п.4 интенты, п.5 смоук); PRD_MAP порядок voice_action выше полных интентов. | Следующий шаг: `go` п.3 voice_action. | Статус: done

2026-06-08 | Действие: Hermes п.2 — slot_normalize, rescue, smoke_hermes_leads 40 passed; BACKLOG hermes eval закрыт; `HERMES_LEADS_ACCEPTANCE.md`. | Следующий шаг: voice_action или полные интенты. | Статус: done

2026-06-08 | Действие: BACKLOG — Pydantic `@validator` в `email.py` → `@field_validator` (🟢, шум в pytest). | Следующий шаг: п.2 Hermes / voice_action. | Статус: done

2026-06-08 | Действие: Whisper STT п.1 — `smoke_whisper_stt.py` 14+1 live Groq; фикс 503/WS error; `WHISPER_STT_ACCEPTANCE.md`; DevTools WS OK. | Следующий шаг: п.2 Hermes интенты или п.3 voice_action. | Статус: done

2026-06-08 | Действие: балльная воронка — `lead_priority_tier.py`, `smoke_scoring_funnel.py`, 21 pytest; PRD_MAP смоук ✅; `SCORING_FUNNEL_ACCEPTANCE.md`. | Следующий шаг: `go` голос → лиды или распределение PRD_NOTES. | Статус: done

2026-06-08 | Действие: PRD_NOTES → канон: стек в ARCHITECTURE, карта docs в README, gaps в BACKLOG, RAG коллекции; NOTES обрезан (~500 строк дублей). | Следующий шаг: ждём апрув блока Лиды / `go` п.3. | Статус: done

2026-06-08 | Действие: BACKLOG — туннель :8000/:5173 + исходящий вебхук Битрикса (отложено, Ф2/DevOps); ISSUES/PRD_MAP/HANDOFF обновлены. | Следующий шаг: `go` на п.3 Kanban DnD. | Статус: done

2026-06-08 | Действие: коммит п.2 — `f2727a3` feat: автосинк Битрикс (webhooks_bitrix, bitrix24_sync, amount_rub, опрос 5 мин); pytest integrations 4 passed. | Следующий шаг: `go` п.3 Kanban DnD. | Статус: done

2026-06-08 | Действие: п.3 Kanban DnD — `funnelDnD.js`, drag-drop на `/leads/funnel`, rollback при блоке стадии; pytest 16 passed (funnel_dnd + leads_api). | Следующий шаг: `go` п.4 список/фильтры. | Статус: done

2026-06-08 | Действие: п.4 список — `leadListFilter.js`: фильтр приоритета, сортировка балл/приоритет/компания; UI select + клик по заголовку; pytest 3 passed. | Следующий шаг: `go` п.5 карточка. | Статус: done

2026-06-08 | Действие: п.5 карточка — `leadCardActivity.js` (apiFetch), `leadCardMoney.js`, поле должность; `test_lead_engagement` + card tests 10 passed. | Следующий шаг: `go` п.6 задачи. | Статус: done

2026-06-08 | Действие: п.6 задачи/SLA — `task_dates.py`, `lead_id` фильтр, карточка лида задачи+создание; `taskApi`/`taskSla`; pytest 6 passed. | Следующий шаг: `go` п.7 комментарии. | Статус: done

2026-06-08 | Действие: п.7 комментарии — фикс shadow `postLeadComment`→`submitComment`; `leadComments.js`; API reject пустого body; pytest 7 passed. | Следующий шаг: `go` п.8 аудит полей. | Статус: done

2026-06-08 | Действие: п.8 аудит полей — `leadAudit.js`, RU-лейблы в карточке; тесты util+API 7 passed. | Следующий шаг: `go` п.9 правила стадий. | Статус: done

2026-06-08 | Действие: п.9 правила стадий — `stageTransition.js`, apiUpdateLead→apiPatch, подсказки на кнопках стадий; pytest 11 passed. | Следующий шаг: `go` п.10 лог касаний. | Статус: done

2026-06-08 | Действие: п.10 лог касаний — `leadCommunications.js`, RU-лейблы типов, валидация content; pytest 9 passed. | Следующий шаг: `go` п.11 /crm редиректы. | Статус: done

2026-06-08 | Действие: п.11 /crm редиректы — `crmRedirectMap.js`, +/crm/campaign/{id}; pytest 3 passed. | Следующий шаг: `go` п.12 смоук /leads/*. | Статус: done

2026-06-08 | Действие: п.12 смоук /leads/* — `smoke_leads_block.py`, `leadsRouteManifest.js`, E2E smoke; 71 pytest passed; блок Лиды закрыт. | Следующий шаг: Фаза 1 — следующий модуль PRD_MAP. | Статус: done

2026-06-08 | Действие: acceptance блока Лиды — 81 pytest + 14 HTTP + DevTools все экраны; фикс `/leads/tasks` createTask shadow; `test_leads_block_acceptance.py`, `LEADS_BLOCK_ACCEPTANCE.md`. | Следующий шаг: апрув пользователя → следующий модуль Фазы 1. | Статус: done

2026-06-08 | Действие: Единое правило `smartcrm-commit-ops.mdc` — всегда commit+ops, push по апруву; убраны дубли/конфликты в `.mdc`, `.cursorrules`, RULES_MATRIX, SESSION_STATE; `check_rules_commit_conflict.py`. | Следующий шаг: Фаза 1 PRD_MAP п.3 + `go`. | Статус: done

2026-06-08 | Действие: User Rules — проверка: в локальных файлах Cursor нет (облако); добавлены `AGENTS.md`, `verify_cursor_rules_precedence.py`, `CURSOR_USER_RULES_STATUS.md` — Project Rules перебивают User Rules. | Следующий шаг: PRD_MAP п.3 + `go`. | Статус: done

2026-06-08 | Действие: PRD_MAP Фаза 1 п.1 «CRUD лидов» — перепроход: pytest `test_leads_api` 12 passed (+ amountRub camelCase); live Postgres CRUD OK; код API `leads/crud.py` + UI list/card — review; UI смоук DevTools заблокирован (frontend rolldown). ISSUES: UI update неполный, rolldown. | Следующий шаг: апрув п.1 → п.2 «Поля уровня Битрикс» или фикс UI edit по go. | Вопросы: фиксить контакты в карточке в этом шаге? | Статус: ждём апрув

2026-06-08 | Действие: Вариант B п.1 CRUD — UI edit форма на `/leads/{id}` (`leadCardEdit.js`); frontend Vite 6 + rollup wasm + `ensure-native-deps.cjs`; убран `editingLead`; тесты 15 passed + `crm_leads` 22 passed; DevTools CRUD+карточка OK. | Следующий шаг: `go` на п.2 PRD_MAP. | QA: crm_leads PASS, DevTools contact/industry PATCH OK | Статус: done

2026-06-08 | Действие: PRD_MAP §Лиды — таблица перепрохода: п.1 CRUD ✅ OK (2026-06-08); указатель на п.2 «Поля Битрикс». | Следующий шаг: `go` на п.2. | Статус: done

2026-06-08 | Действие: п.2 «Поля Битрикс» — маппинг + `amount_rub`; автосинк: `POST /api/webhooks/bitrix/events` + фон `BITRIX_AUTO_SYNC_MINUTES=5`; `GET /api/leads/bitrix-sync-status`; pytest bitrix 7 passed (3 live). Файлы: `bitrix24_sync.py`, `webhooks_bitrix.py`, `bitrix.md`. | Следующий шаг: перезапуск uvicorn; вебхук ONCRMLEADADD; `go` на п.3 Kanban DnD. | Статус: done (код), ждёт настройку портала

2026-05-04 | Действие: ROOT CAUSE найден и устранён — база `smartcrm` и юзер `smartcrm` отсутствовали в Postgres; созданы через psql; uvicorn перезапущен → `init_db` применил схему; проверено: `/api/leads` → 200 OK, `/api/leads/1791` → 404 (база пустая). Ошибок 500 нет. | Следующий шаг: импорт/сид данных (Bitrix или `seed_eval_benchmark_leads.py`) при необходимости. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Доп. фикс RST при connect — в `db/session.py`: нормализация `@localhost`→`127.0.0.1` (env `DATABASE_FORCE_IPV4`), дефолт URL на `127.0.0.1`, `connect_args` timeout + опционально `DATABASE_SSL=disable`; `.env.example` обновлён. | Следующий шаг: перезапуск uvicorn; при своём `.env` с localhost — перезагрузить без смены файла (нормализация сработает). | Вопросы: нет | Статус: done

2026-05-04 | Действие: 500 на `/api/leads` — по логам не ORM, а обрыв TCP к Postgres (`ConnectionResetError` 10054, `ConnectionDoesNotExistError`). В `db/session.py`: `pool_pre_ping=True`, `pool_recycle` (+ опция в `.env.example`). | Следующий шаг: перезапуск uvicorn; проверить что Postgres стабилен (Docker/VPN). | Вопросы: нет | Статус: done

2026-05-04 | Действие: Дожат операционка под hotfix — строка в `CHANGELOG`, уточнён `HANDOFF` (след. шаг + voice WS). | Следующий шаг: смоук по HANDOFF. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Фикс старта API — в `LeadFieldAudit` не был импортирован `Optional` для `audit_metadata`; добавлены `typing.Any`/`Optional` и аннотация `dict[str, Any]`; у `Lead.approvals` — то же для JSON. Импорт `main:app` проверен. | Следующий шаг: перезагрузить uvicorn; повторить запросы к `/api/leads/...`. | Вопросы: нет | Статус: done

2026-05-04 | Действие: P3 CRM points — UI чеклиста `approvals`, блок касаний и `eventType` в истории на `/leads/[id]`; merge апрувов в `enrichLeadForCard`; тесты бонуса/cap в `test_lead_score_advisory.py`; `docs/modules/leads.md` + батч `CHANGELOG`/`HANDOFF`. | Следующий шаг: смоук UI + перезапуск бэка/`init_db` для DDL; при необходимости — интеграционные тесты PATCH апрувов и POST communications. | Вопросы: нет | Статус: done

2026-05-03 | Действие: Аудит всех основных `docs/*.md`, сводка в `CHANGELOG`; заведены записи в `ISSUES` (🟡×2, 🟢×1); обновлены `HANDOFF`, `SESSION_STATE`. Файлы: `docs/operations/*.md`. | Следующий шаг: по приоритету пользователя — BA/PM дельта PRD или Backend политика БД (только с `go` на код). | Вопросы: нет | Статус: done

2026-05-04 | Действие: Architect Pre-Feature Gate — фича «балльные лиды как в CRM points»: осмотр `Lead`, `Task` (есть `lead_id`, `sla_due`), `crm_settings_store` (stages/thresholds, нет весов формулы). | Следующий шаг: ждать `go` — либо дельта `docs/product/PRD.md`+`docs/product/ARCHITECTURE.md`, либо сразу P1-код (веса+пересчёт) после явного go на миграции/контракт. | Вопросы: нет | Статус: in_progress

2026-05-04 | Действие: PM + Architect по `go` — расширены `docs/product/PRD.md` (роли, P1–P3, метрики, риски, приложения) и `docs/product/ARCHITECTURE.md` (домен лидов, API/DDL план, агенты); батч `CHANGELOG` + `HANDOFF`. | Следующий шаг: пользователь отвечает на приложение C PRD или подтверждает defaults из ARCH; затем `go` на P1 backend. | Вопросы: см. PRD приложение C | Статус: done (документный шаг)

2026-05-04 | Действие: P1 по `go` — суммы `amount_rub`/`paid_amount_rub`, `lead_score_advisory`, флаги CRM, `scoreAdvisory` в GET/PATCH лида, гейт `update_lead_score`, UI карточки, тесты `test_lead_score_advisory.py`; PRD/ARCH синхронизированы с решением «балл = менеджер». | Следующий шаг: смоук UI + при желании P2. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Завершение итерации (`go` «добей») — оптимизация `page.subscribe` на карточке лида (fetch только при смене `id`); обновлён `docs/agents/langgraph.md` (гейт `update_lead_score`, `scoreAdvisory`); pytest `test_lead_score_advisory` + выборочные тесты зелёные; полный `tests/` падает на несвязанном `test_email_sync`. | Следующий шаг: P2 по отдельному `go`. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Техдельта v3 в доки — `voice_action`, email режимы, Search-to-Q&A, gate тендеров, lookalike, fanout; файлы: PRD, ARCHITECTURE, PRD_MAP, PRD_NOTES (журнал), langgraph, RAG, leadgen, tenders; ops батч. | Следующий шаг: проход Фазы 1 по PRD_MAP (ждать `go`). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Правила структуры репо и сплита кода — `.cursor/rules/smartcrm-repo-layout.mdc`, `smartcrm-code-split.mdc`; канон `docs/dev/REPO_LAYOUT.md`; аудит `LAYOUT_AUDIT.md` (пакеты P1–P6 без переносов); обновлены CONTRIBUTING, docs/README. | Следующий шаг: пользователь выбирает `go P1`… для переносов. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P1 layout — корневой `tests/` → `backend/tests/{api,core,rag}/`; `conftest.py` с auth для pytest; удалён `/tests/`; pytest: 25 passed (api+rag+hermes unit). | Следующий шаг: `go P2` или Фаза 1 PRD_MAP. | QA: api 13, rag 7, hermes parser 5 green | Статус: done

2026-06-07 | Действие: P2 layout — корень очищен; openapi → `docs/api/openapi/`; артефакты → `backend/data/artifacts/`; `.gitignore`; правила анти-мусора в `smartcrm-repo-layout.mdc`, REPO_LAYOUT. | Следующий шаг: ждать апрув — P3/P4/P5 или Фаза 1. | Статус: done

2026-06-07 | Действие: P3 — `backend/backend/data/` удалён; `tender_sources_ab.json` → `backend/data/`; комментарий в `tender_sources_ab.py` (cwd backend/). | Следующий шаг: апрув P4/P5 или Фаза 1. | Статус: done

2026-06-07 | Действие: P4 — `test_email_integration.py` → `backend/tests/integration/`; обновлён `docs/email/setup.md`. | Следующий шаг: апрув P5 или Фаза 1. | Статус: done

2026-06-07 | Действие: P5 — git-коммит миграции docs: удалены плоские `docs/*.md`, добавлены `start/`, `modules/`, `email/`, `voice/`, `archive/`, `ISSUES.md`; таблица в README. CRM-points-system не в git. | Следующий шаг: P6 или Фаза 1. | Статус: done

2026-06-07 | Действие: P6 (шаг 1) — сплит `api/routes/leads.py` → пакет `leads/` (6 файлов); pytest leads 21 passed. | Следующий шаг: P6 следующий файл по апруву или Фаза 1. | QA: 21 passed | Статус: done

2026-05-04 | Действие: P2 по явному `go` пользователя — `LeadComment`/`LeadFieldAudit`, `GET/POST /api/leads/{id}/comments`, `GET .../audit`, валидация `stage_transition_rules` при PATCH, аудит полей; `crm_settings` + Ops + публичный config; UI карточки лида (комментарии, история) и Ops JSON для правил; `core/stage_transition.py`, тесты `test_stage_transition.py`; правка `docs/product/ARCHITECTURE.md`. | Следующий шаг: P3/доки по сделке или смоук; референс Rails без кода в репо — уточнять по экранам при необходимости. | Вопросы: нет | Статус: done

2026-05-04 | Действие: Разбор референса `https://github.com/Razmik-Kutinava/CRM---points-system` — shallow clone в `docs/reference/CRM-points-system`; прочитаны `Lead`, `ScoreCalculator`, `LeadStateMachine`, `db/schema.rb` (булевы «апрувы»/доки на `leads`, `lead_histories`, `communication_logs`, авто-`score` после save). | Следующий шаг: по `go` — матрица переноса в PRD/ARCH или очередь фич (булевы флаги, communication log, формула как опция поверх advisory). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Реорганизация `docs/` — папки product, start, api, modules, email, voice, agents, stack, operations, dev, archive, reference; `docs/README.md` карта; обновлены README, `.cursorrules`. | Следующий шаг: пользователь — полировка лидов по экранам. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Удалён устаревший alwaysApply-процесс; канон перенесён в `smartcrm-*.mdc`; ссылки в `.cursorrules` и operations. | Следующий шаг: вехи/доки по апруву пользователя. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Добавлено правило агента `.cursor/rules/smartcrm-agent-workflow.mdc` (коммиты, операционка, стоп до `go`); ссылка в `.cursorrules`. | Следующий шаг: ждать go пользователя (вехи/доки). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Создан `docs/product/PRD_DELTA_v2.md` — дельта PRD v2 (Voice Layer, Email-агент, Self-improvement, Оркестрация, Тендеры, Аналитика v2). | Следующий шаг: по go — ревью/слияние в основной PRD или вехи. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Слияние PRD Delta v2 в `docs/product/PRD.md` — roadmap Фаза 1–3, дубли убраны, дельта помечена архивом. | Следующий шаг: по go — раскидать задачи по спринтам / полировка лидов. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Карта CRM из дельты вынесена в `docs/product/PRD_MAP.md`; дубль убран из `PRD.md` и `PRD_DELTA_v2.md`; ссылки в `docs/README.md`, `.cursorrules`. | Следующий шаг: по go — спринты по фазам из PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Создан инбокс `docs/product/PRD_NOTES.md` — пользователь вставляет отрывки по модулям/фазам/навигации для последующего разбора. | Следующий шаг: пользователь загружает тексты в PRD_NOTES. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Из PRD_NOTES собраны чеклисты Фаза 1–3 в `PRD_MAP.md` ([x] сдано + хвосты); NOTES: навигация, роуты, стек-placeholder, журнал. | Следующий шаг: проход Фазы 1 по PRD_MAP (баги в ISSUES). | Вопросы: нет | Статус: done

2026-06-07 | Действие: Оглавление в начале `PRD_NOTES.md` (модули, агенты, фазы, строки). | Следующий шаг: по go — проход Фазы 1. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P6 hermes — `core/hermes.py` → пакет `core/hermes/` (config, prompts, parse, rescue, cache, providers); rollout → `config`; тесты Parser 5 passed + voice prompt 1 passed; `LAYOUT_AUDIT` обновлён. | Следующий шаг: `go P6 ops` или Фаза 1. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P6 ops — `api/routes/ops.py` → пакет `api/routes/ops/` (10 модулей, 34 роута); тест review_fixes + hermes Parser 6 passed; коммит P6 hermes+ops. | Следующий шаг: P6 pipeline/search/tenders или Фаза 1 PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: P6 остаток — `qa/`, `tenders/`, `analyst/`, `rag/search/`, `leadgen/pipeline/`, `checko/`; фикс cross-imports + `_resplit_leadgen_pkgs.py`; тесты leadgen+voice+tenders+qa+analyst+rag: **114 passed**. | Следующий шаг: Фаза 1 PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: коммит `725b284` (P6+CRM+tenders+leads UI) + push `main` → origin (25 коммитов). | Следующий шаг: **Фаза 1 PRD_MAP** — баги/чеклист в ISSUES. | Вопросы: нет | Статус: done

2026-06-07 | Действие: 15× `backend/**/README.md` (карта бэкенда); ссылка в REPO_LAYOUT; черновик правила README-sync — ждёт апрув. | Следующий шаг: апрув правила → push. | Вопросы: нет | Статус: in_progress

2026-06-07 | Действие: push `351fc23` — backend README pack + BACKEND_README_SYNC_DRAFT. | Следующий шаг: апрув правила → влить в smartcrm-repo-layout.mdc. | Вопросы: нет | Статус: done

2026-06-07 | Действие: правило §5 Backend README Sync в `smartcrm-repo-layout.mdc`; DRAFT → применено; CHANGELOG+HANDOFF. | Следующий шаг: push; ждём задачу пользователя (Фаза 1 PRD_MAP). | Вопросы: нет | Статус: done

2026-06-07 | Действие: `smartcrm-task-workflow.mdc` (go, тесты, авто commit/ops, push/deploy по апруву); ссылка в repo-layout §6. | Следующий шаг: ждём пункт PRD_MAP от пользователя. | Вопросы: нет | Статус: done

2026-06-07 | Действие: § anti-hallucination в task-workflow (честный отчёт «Не сделано / не проверено»). | Следующий шаг: ждём пункт PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: BACKLOG.md + § бэклог в task-workflow (связь с пунктами PRD_MAP, фаза опционально). | Следующий шаг: ждём пункт PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: smartcrm-dev-gates.mdc (DoD, регрессия, миграции, API, hot-path); .cursorrules→индекс; agent-workflow+BACKLOG. | Следующий шаг: ждём пункт PRD_MAP. | Вопросы: нет | Статус: done

2026-06-07 | Действие: Аудит правил — канон в `smartcrm-*.mdc`; п.0 коммит+ops; honest report; `run_zone_regression.py`; CURSOR_USER_RULES_SNIPPET. | Следующий шаг: Фаза 1 PRD_MAP + go. | Вопросы: нет | Статус: done

2026-06-07 | Действие: коммит `28ab125`; регрессия p1/p6 PASS, hermes_eval 9 FAIL → ISSUES+BACKLOG. | Следующий шаг: Фаза 1 PRD_MAP + go. | Вопросы: push по апруву | Статус: done

2026-06-08 | Действие: ops sync — RULES_MATRIX, check_agent_step.py, fix agent-workflow.mdc, BACKLOG/PRD_MAP, зачистка журналов, archive rename. | Следующий шаг: Фаза 1 PRD_MAP (интенты Hermes) + go. | Тесты: p6 PASS, check_agent_step | Статус: done

2026-06-08 | Действие: коммит `bcce33c` (ops sync). Регрессия p6: All zones passed (121 tests). | Следующий шаг: Фаза 1 PRD_MAP + go. | push по апруву | Статус: done

2026-06-08 | Действие: push `main` → origin (6 коммитов: rules + ops sync). | Следующий шаг: Фаза 1 PRD_MAP с начала — пункт + go. | Статус: done

2026-06-08 | Действие: правила — коммит+ops безусловно; check_agent_step FAIL на незакоммиченное. | Коммит: `86a8e7a` | Статус: done

2026-06-08 | Действие: коммит `86a8e7a`. | Следующий шаг: Фаза 1 PRD_MAP + go. | Статус: done

---
