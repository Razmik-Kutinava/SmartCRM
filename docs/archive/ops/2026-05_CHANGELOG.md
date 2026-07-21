# CHANGELOG — архив 2026-05

> Вынесено из `docs/operations/session/CHANGELOG.md` (распил по месяцам, 2026-07-21).

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
