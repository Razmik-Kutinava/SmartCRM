# CHANGELOG (операционный)

История изменений продукта, архитектуры и согласованных решений.

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
