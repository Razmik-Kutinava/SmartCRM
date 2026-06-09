# SESSION_STATE

Краткий прогресс сессии — **обязательно** после каждого действия (1–2 строки). Шаг с изменениями файлов → `git commit` **до** отчёта. Канон: `smartcrm-commit-ops.mdc`.

Шаблон строки:

`[время] | Действие:[что сделал] | Следующий шаг:[что дальше] | Вопросы:[если есть]`

2026-06-08 | Действие: RAG п.5 save из поиска — `source_url` в metadata, `test_rag_ingest_batch*.py` 6 pytest, `smoke_rag_save_from_search.py`; DevTools `/search` таб RAG → 1 чанк cbr.ru; `SEARCH_RAG_SAVE_ACCEPTANCE.md`; блок п.1–5 ✅. | Следующий шаг: enrich-lead smoke или Ф2. | Статус: done

2026-06-08 | Действие: RAG п.4 upload PDF/txt — `test_rag_upload.py`, `test_rag_upload_api.py`, `smoke_rag_upload.py` 8 pytest; DevTools `/rag` текст «В базу» 1 чанк + PDF в источниках; `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`; PRD_MAP п.4 ✅. | Следующий шаг: `go` п.5 save из поиска. | Статус: done

2026-06-08 | Действие: RAG п.3 Chroma — `test_rag_api.py`, `smoke_rag_chroma.py` 11 pytest, live 1592 чанка (economist 960 / all 624 / marketer 8); `/rag` apiFetch; `SEARCH_CHROMA_ACCEPTANCE.md`; PRD_MAP п.3 ✅. DevTools: серверы не запущены — pytest + прямой count Chroma OK. | Следующий шаг: коммит → `go` п.4. | Статус: done

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

2026-06-08 | Действие: PRD_NOTES §CHANGELOG → шапка `operations/CHANGELOG.md`; NOTES — ссылка на канон. | Следующий шаг: хвост Ф1 Hermes/voice или `go` Фаза 2. | Статус: done

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
