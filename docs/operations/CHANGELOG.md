# CHANGELOG (операционный)

**Роль:** источник правды по истории — что сделано, когда, почему и при каком `go`.

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

## [2026-06-08] — Правила: только безусловный commit+ops (процесс)

**Сделано:** зачистка всех формулировок отложенного коммита в `.mdc`, `AGENTS.md`, ops-журналах; `check_rules_commit_conflict.py` сканирует `SESSION_STATE`; канон — один: `git commit` при закрытии шага.

**Зачем:** агенты не откладывали коммит и не спрашивали разрешение.

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
| `docs/operations/RULES_MATRIX.md` | Живая матрица правил + таблицы старта/регрессии/финиша |
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

**Сделано:** `docs/operations/BACKLOG.md`; § бэклог в `smartcrm-task-workflow.mdc` — привязка **только к пунктам PRD_MAP**, фаза MAP опционально («когда закрывать»).

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
