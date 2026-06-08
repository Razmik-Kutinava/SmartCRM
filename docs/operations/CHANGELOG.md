# CHANGELOG (операционный)

История изменений продукта, архитектуры и согласованных решений.

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
| `docs/product/PRD.md` | Роли; фича «балльная воронка лидов» (проблема, ценность, scope, P1–P3, не-скоуп, метрики, риски, зависимости); приложения A–G; объём приведён к требованию PRD Factory (≥250 строк). |
| `docs/product/ARCHITECTURE.md` | Раздел домена лидов и скоринга: as-is/to-be, решения по умолчанию, план DDL/API/модулей, безопасность, порядок внедрения, матрица агентов, traceability к Rails-референсу; ≥250 строк. |

**Причина:** пользовательский **`go`** на шаг PM и Architect без кода.

---

## 2026-05-03 — Аудит документации + фиксация внедрения PRD Factory v10 (go пользователя)

**Сделано в репозитории (сессия внедрения процесса, без изменения продуктового кода):**

| Артефакт | Назначение |
|----------|------------|
| `.cursor/rules/prd-factory-agent.mdc` | Полный текст PRD Factory v10, `alwaysApply: true`; блок «Применение в репо с кодом» и fallback `docs/product/PRD.md` / `docs/product/ARCHITECTURE.md` вместо `docs/product/*`. |
| `.cursorrules` (секция сверху) | Ссылка на `.mdc`, приоритет операционки над локальными формулировками, текущие пути продуктовых доков. |
| `docs/agents/AGENTS.md` | Точка входа: PRD Factory + ссылка на `docs/agents/langgraph.md` (LangGraph/Hermes). |
| `docs/agents/langgraph.md` | В начале — ссылка на `docs/agents/AGENTS.md` для онбординга. |
| `docs/operations/ISSUES.md`, `SESSION_STATE.md`, `HANDOFF.md`, `CHANGELOG.md` | Заготовки журналов; после этого апдейта — первые содержательные записи. |

**Инвентаризация `docs/` (основное, не исчерпывающе):**

- Продукт/архитектура: `PRD.md`, `ARCHITECTURE.md`, `RUNBOOK.md`, `API.md`, `SETUP.md`.
- Агенты и стек: `AGENTS.md`, `stack/LLM.md`, `stack/RAG.md`, `stack/LANGGRAPH.md`, `stack/SVELTEKIT.md`.
- Домены: `CRM_ROUTES.md`, `LEADGEN.md`, `TENDERS.md`, `EMAIL*.md`, `BITRIX24_IMPORT.md`, `SEARCH.md`, `VOICE_*.md`.
- Процесс/качество: `dev/CONTRIBUTING.md`, `dev/WORKFLOW.md`, `CODE_REVIEW.md`, `code-reviewer-agent.md`, `security-audit-2026-04.md`, `AGENTS_TEST_RESULTS.md`.

**Разрывы с каноном PRD Factory (зафиксировано, без автоматического исправления):**

- Нет каталога `docs/product/` (`PRD.md` / `ARCHITECTURE.md` остаются в корне `docs/` — согласовано fallback в `.mdc` и `.cursorrules`).
- `docs/product/PRD.md`: чекбоксы MVP «Фаза 1» не отражают текущий объём (тендеры, зеркальные маршруты CRM и т.д.) — риск недоговорённости scope.
- Нет отдельных ролевых промптов `docs/agents/AGENTS/*` (200+ строк) — в процессе PRD Factory Режим A; для SmartCRM пока описание в `docs/agents/langgraph.md`.
- Тесты разнесены по `tests/` и `backend/tests/` — для QA-матрицы нужна явная сводка (задача на спринт, не блокер записи).

**Причина записи:** пользовательский **`go`** на аудит и запись во все нужные операционные файлы.

---
