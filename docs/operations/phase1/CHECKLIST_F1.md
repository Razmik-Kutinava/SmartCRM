# Чеклист: Фаза 1 — MVP

**Статус фазы:** ✅ закрыта (DoD 6/6, 2026-06-11)

> **Легенда:** ✅ готово (код + смоук + acceptance) · ⚠️ код ✅, хвост в `BACKLOG.md` · 🔲 не начато · `[x]` = ✅ по коду/автомату · `[ ]` = 🔲 или хвост.
> **Закрытие пункта:** pytest + acceptance → `[x]`; финальный `[x]` — только после «ок» оператора. DoD пункта → [`dev-gates`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).
> Результаты (acceptance) — в папках областей рядом: `./{область}/*.md`. Хвосты → [`../session/BACKLOG.md`](../session/BACKLOG.md).

---

### Definition of Done — Фаза 1

> **DoD фазы** (здесь) ≠ **DoD пункта** — pytest, smoke, миграции на строку MAP → [`.cursor/rules/workflow/smartcrm-dev-gates.mdc`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).

**Фаза 1 закрыта**, когда все 6 пунктов ниже ✅ **или** п.5 остаётся ⚠️, но владелец явно сказал **«ок, идём в Фазу 2»** (п.6) — не автозакрытие.

| # | Критерий | Статус |
|---|----------|--------|
| 1 | Все таблицы Ф1: ✅ / ⚠️ с хвостом в BACKLOG / явный `→ Ф2\|Ф3` | ✅ |
| 2 | Хвосты в [`BACKLOG.md`](../session/BACKLOG.md) или перенесены в Ф2–3; MAP — только указатель | ✅ |
| 3 | Смоук зон + регрессия зелёные (см. dev-gates по каждому пункту) | ✅ |
| 4 | Acceptance на закрытые блоки (ссылки в колонке «Итог» таблиц) | ✅ |
| 5 | Сценарий **«голосом создать / найти лид»**: E2E audio WS + dev simulate mic | ✅ `VOICE_MIC_E2E_ACCEPTANCE.md` |
| 6 | Решение: **«ок, идём в Фазу 2»** — очередь 5 leadgen+голос | ✅ 2026-06-11 |

**Вердикт (6/6):** Ф1 **закрыта** по DoD; Ф2 старт — **очередь 5** (smoke slice ✅).

### Фаза 1 — сценарии (зачем техтаблицы)

> **Процесс:** продуктовый вопрос → **сначала строка здесь** → потом пункт в техтаблице ниже.  
> **Новая фича Ф1:** сценарий в эту таблицу → строка в блоке MAP → acceptance. Детали PRD — [`PRD.md`](PRD.md), не копировать сюда.

| # | Менеджер может… | Статус | Привязка MAP |
|---|-----------------|--------|--------------|
| 1 | Вести лид end-to-end: CRUD, Kanban, задачи, комментарии, касания, аудит | ✅ | [Лиды](#лиды-leads) п.1–12 · ⚠️ Битрикс вебхук п.2 → `BACKLOG` |
| 2 | Видеть балл лида, breakdown и фильтровать список по приоритету | ✅ | [Балльная воронка](#балльная-воронка-p1p2p3-код) п.1–5 |
| 3 | Голосом (текст): создать/найти/обновить лид, стадию, фильтр, апрув | ✅ | [Голос → лиды](#голос--лиды-базово) п.2–4 |
| 4 | **Говорить в микрофон** (или dev 🎤 sim) → Whisper → Hermes → действие | ✅ | Голос п.1 · `VOICE_MIC_E2E_ACCEPTANCE.md` |
| 5 | Найти компанию в поиске, обогатить поля и сохранить в карточку лида | ✅ | [Поиск и RAG](#поиск-и-rag-базово) + enrich · `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` |
| 6 | Найти новых лидов: ИНН, портрет, кластер — с автосейвом в CRM при скор ≥ 30 | ✅ | [Лидогенерация](#лидогенерация-leadgen) · `LEADGEN_*_ACCEPTANCE.md` |
| 7 | Смотреть воронку/конверсию и выгрузить отчёт; спросить 5 агентов в чате (RAG) | ✅ | [Аналитика](#аналитика-базовая) · [Агенты](#агенты-по-отдельности) · качество агентов → Ф2 |

---

## Фаза 1 — MVP (проходим первой)

**Статус:** ✅ **Ф1 закрыта** (DoD 6/6); голос mic E2E — автомат + dev sim.

### Лиды `/leads`

> **Перепроход Фазы 1 (2026-06-08):** чеклист = таблица ниже. После пункта — смоук, pytest, DevTools → следующий пункт.

| # | Пункт | Перепроход | Итог |
|---|--------|------------|------|
| 1 | CRUD лидов (API + UI) | 2026-06-08 | ✅ **OK** — API `crm_leads` 22 passed; live Postgres CRUD; UI create/list/delete + форма edit на `/leads/{id}`; DevTools CRUD+PATCH карточки; `4ec4b6a` |
| 2 | Поля уровня Битрикс + синк | 2026-06-08 | ✅ код · **⚠️** туннель + исходящий вебхук в портале → `BACKLOG` 🟡 |
| 3 | Воронка Kanban DnD | 2026-06-08 | ✅ **OK** — DnD на `/leads/funnel`, PATCH stage, rollback при `stage_transition_blocked`; pytest funnel + API |
| 4 | Список фильтры + сортировка | 2026-06-08 | ✅ **OK** — поиск, этап, приоритет; сортировка балл/приоритет/компания; `leadListFilter.js` |
| 5 | Карточка лида | 2026-06-08 | ✅ **OK** — поля+должность, суммы ₽, апрувы, касания; apiFetch для activity; pytest engagement 10 |
| 6 | Задачи по лиду, SLA | 2026-06-08 | ✅ **OK** — `lead_id` фильтр, overdue; карточка лида грузит задачи; taskApi; pytest 6 |
| 7 | Комментарии | 2026-06-08 | ✅ **OK** — фикс рекурсии submitComment; `leadComments.js`; пустой body 400; pytest 7 |
| 8 | Аудит полей | 2026-06-08 | ✅ **OK** — PATCH→audit; `leadAudit.js` + RU-лейблы; pytest 7 |
| 9 | Правила переходов стадий | 2026-06-08 | ✅ **OK** — `stageTransition.js`, apiPatch, подсказки на кнопках; pytest 11 |
| 10 | Лог касаний | 2026-06-08 | ✅ **OK** — `leadCommunications.js`, RU-типы, пустой content 400; pytest 9 |
| 11 | `/crm/*` редиректы | 2026-06-08 | ✅ **OK** — `crmRedirectMap.js`, +campaign; pytest 3 |
| 12 | Смоук `/leads/*` | 2026-06-08 | ✅ **OK** — 81 pytest + 14 HTTP + DevTools; фикс `/leads/tasks`; блок **закрыт** |

### Балльная воронка (P1+P2+P3 код)

> **Перепроход (2026-06-08):** чеклист = таблица ниже. **Статус блока:** ✅ (п.6 → Ф3).

| # | Пункт | Перепроход | Итог |
|---|--------|------------|------|
| 1 | `scoreAdvisory` + warnings + breakdown | 2026-06-08 | ✅ API GET/PATCH лида, юнит-тесты формулы |
| 2 | Суммы ₽, апрувы, касания в формуле | 2026-06-08 | ✅ golden-тест base+bonus+penalty |
| 3 | Балл менеджера, агенты не пишут score | 2026-06-08 | ✅ `agentsMayUpdateScore=false` в `/api/crm/config` |
| 4 | Приоритеты в списке `/leads/list` | 2026-06-08 | ✅ `lead_priority_tier` = зеркало `crmStages.js`, фильтр critical |
| 5 | Смоук регрессия | 2026-06-08 | ✅ `python scripts/smoke_scoring_funnel.py` — **блок закрыт** |
| 6 | Экспорт по баллам / SLA расширенные | — | 🔲 → **Фаза 3** |

### Голос → лиды (базово)

> **Перепроход (2026-06-08):** чеклист = таблица ниже. **Статус блока:** ✅ (п.3/5 spot-check 🟡 опц.).

| # | Пункт | Перепроход | Статус | Итог |
|---|--------|------------|--------|------|
| 1 | Whisper (Groq STT) → текст | 2026-06-11 | ✅ | API/WS + `smoke_whisper_stt.py` + `smoke_voice_mic_e2e.py` · `VOICE_MIC_E2E_ACCEPTANCE.md` |
| 2 | Hermes → интенты по лидам | 2026-06-08 | ✅ | `smoke_hermes_leads.py` 40 pytest; `HERMES_LEADS_ACCEPTANCE.md` |
| 3 | UI `voice_action` | 2026-06-08 | ⚠️ | ✅ modal/navigate/filter/approve · **⚠️** spot-check delete approve → `BACKLOG` 🟡 · `VOICE_ACTION_ACCEPTANCE.md` |
| 4 | Полные интенты лидов | 2026-06-08 | ✅ | analyze_lead, lead_history, stage/industry/city; `HERMES_LEADS_FULL_ACCEPTANCE.md` |
| 5 | Смоук голосовых сценариев | 2026-06-08 | ⚠️ | ✅ код + автомат S01–S09 · **⚠️** fanout UI 15–30 с, approve UI → `BACKLOG` 🟡 · `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md` |

**Опц. spot-check:** п.3 approve delete, п.5 fanout UI — `BACKLOG` 🟡.

### Поиск и RAG (базово)

> **Перепроход (2026-06-08–09):** чеклист = таблица ниже. **Статус блока:** ✅ база Ф1 закрыта (авто-чанки → Ф2).

| # | Пункт | Перепроход | Статус | Итог |
|---|--------|------------|--------|------|
| 1 | Serper + Brave + Tavily | 2026-06-08 | ✅ | `smoke_search_providers.py` 11 pytest; DevTools `/search`; `SEARCH_PROVIDERS_ACCEPTANCE.md` |
| 2 | 6 режимов поиска | 2026-06-08 | ✅ | `smoke_search_modes.py` 19 pytest; DevTools 6 табов; `SEARCH_MODES_ACCEPTANCE.md` |
| 3 | Chroma RAG (~1592 чанка), по агентам | 2026-06-08 | ✅ | `smoke_rag_chroma.py` 11 pytest; `SEARCH_CHROMA_ACCEPTANCE.md` |
| 4 | Загрузка PDF/текста в `/rag` | 2026-06-08 | ✅ | `smoke_rag_upload.py` 8 pytest; DevTools `/rag`; `SEARCH_RAG_UPLOAD_ACCEPTANCE.md` |
| 5 | «Сохранить в базу» из поиска | 2026-06-08 | ✅ | `smoke_rag_save_from_search.py` 6 pytest; `SEARCH_RAG_SAVE_ACCEPTANCE.md` |
| 6 | Авто-чанки из поиска / диалога | — | ✅ | §4 Ф2 — [`SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md`](../phase2/rag/SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md) + dialogue + save + enrich cache |
| 7 | Смоук enrich-lead | 2026-06-09 | ✅ | `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` |
| 8 | Обогащение → карточка лида (Checko, Brave, CRM) | 2026-06-09 | ✅ | `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` §2 |

### Лидогенерация `/leadgen`

- [x] Анализ по ИНН / названию — **2026-06-08 ✅** (`LEADGEN_INN_ANALYSIS_ACCEPTANCE.md`, smoke + DevTools)
- [x] Поиск по портрету — **2026-06-09 ✅** (`LEADGEN_PORTRAIT_ACCEPTANCE.md`, smoke + DevTools)
- [x] Кластер / холдинг — **2026-06-10 ✅** (`LEADGEN_CLUSTER_ACCEPTANCE.md`, smoke + DevTools)
- [x] Автосохранение в CRM при скор ≥ 30 — **2026-06-10 ✅** (`LEADGEN_AUTOSAVE_ACCEPTANCE.md`, smoke + DevTools)
- [ ] Голосовые команды лидогена → **Фаза 2**
- [ ] Портрет из выигранных сделок → **Фаза 2** ([`leadgen.md`](../modules/leadgen.md#lookalike-из-won-сделок-фаза-2))
- [ ] Авто-мониторинг новых лидов → **Фаза 3**

### Тендеры `/tenders` (baseline)

> **Перепроход (2026-06-11):** чеклист = таблица ниже. **Статус блока:** ✅ baseline (хвосты ⚠️ → `BACKLOG`).

| # | Пункт | Перепроход | Итог |
|---|--------|------------|------|
| 1 | UI `/tenders` + API `/api/tenders` | 2026-06-11 | ✅ **OK** — страница + роутер `tenders/*`; `smoke_tenders_baseline.py` |
| 2 | Поиск 44/223, НМЦ, регион, ОКПД2 | 2026-06-11 | ✅ **OK** — Gosplan+TG+Serper/Tavily; лейбл «без совпадения» + скрыть |
| 3 | Планы закупок (`/plans/search`) | 2026-06-11 | ✅ **OK** — TenderGuru planzakup |
| 4 | Избранное / «Мои» / Архив | 2026-06-11 | ✅ **OK** — `tender_saved` БД · `/api/tenders/saved` · UI вкладки |
| 5 | TenderGuru + Gosplan + Serper/Tavily | 2026-06-11 | ✅ **OK** — `web_search.py` в `/search` |
| 6 | Лимиты Ops → API Limits | 2026-06-11 | ✅ **OK** — `track_api` gosplan/datanewton/serper/tavily |
| 7 | Агентский анализ ТЗ | 2026-06-11 | ✅ **OK** — `POST /analyze` + LLM · сохранение в БД |
| 8 | Платный API (Контур) | — | 🔲 → после 1-й сделки ([`tenders.md`](../modules/tenders.md#экономика-и-gate-платного-api)) |

**Acceptance:** [`TENDERS_BASELINE_ACCEPTANCE.md`](../phase1/tenders/TENDERS_BASELINE_ACCEPTANCE.md)

### Аналитика (базовая)

- [x] `/leads/analytics` — воронка, конверсия, средний чек, цикл
- [x] Экспорт отчёта (базово)
- [ ] Голосовые запросы к метрикам → **Фаза 2**

| # | Пункт | Дата | Статус |
|---|--------|------|--------|
| 1 | Воронка по этапам CRM | 2026-06-11 | ✅ **OK** — `compute_analytics` · реальные лиды из БД |
| 2 | Конверсия + win-rate | 2026-06-11 | ✅ **OK** — `Выигран/всего`, закрытые сделки |
| 3 | Средний чек | 2026-06-11 | ✅ **OK** — `amountRub` / `budget` у выигранных |
| 4 | Цикл сделки | 2026-06-11 | ✅ **OK** — `createdAt`→`updatedAt` (— если нет выигранных) |
| 5 | Экспорт CSV | 2026-06-11 | ✅ **OK** — `GET /api/leads/analytics/export` · UI кнопка |
| 6 | Убрать mock `/analytics` | 2026-06-11 | ✅ **OK** — 308 → `/leads/analytics` |
| 7 | Голос по метрикам | — | 🔲 → **Фаза 2** |

**Acceptance:** [`ANALYTICS_BASELINE_ACCEPTANCE.md`](../phase1/analytics/ANALYTICS_BASELINE_ACCEPTANCE.md)

### Ops `/ops`

- [x] Обзор, интенты, голос, агенты, поиск, очередь, статистика
- [x] Инсайты, API лимиты, логи, CRM-конфиг
- [x] Редактирование промптов агентов
- [ ] Версионирование промптов → **Фаза 2**

| # | Пункт | Дата | Статус |
|---|--------|------|--------|
| 1 | Обзор + очередь | 2026-06-11 | ✅ **OK** — `/api/ops/overview`, `queue` |
| 2 | Интенты (Hermes) | 2026-06-11 | ✅ **OK** — traces, improve, scenarios, eval |
| 3 | Голос (Whisper) | 2026-06-11 | ✅ **OK** — `/api/ops/voice/whisper` |
| 4 | Агенты + промпты | 2026-06-11 | ✅ **OK** — 5 агентов, PUT prompt |
| 5 | Поиск (Ops) | 2026-06-11 | ✅ **OK** — `/api/search/config` |
| 6 | Статистика + инсайты | 2026-06-11 | ✅ **OK** — `stats`, `insights` |
| 7 | API лимиты | 2026-06-11 | ✅ **OK** — `/api/usage/stats` |
| 8 | Логи | 2026-06-11 | ✅ **OK** — `/api/ops/logs` |
| 9 | CRM-конфиг | 2026-06-11 | ✅ **OK** — `crm-settings` GET/PUT |
| 10 | Версионирование промптов | — | 🔲 → **Фаза 2** |

**Acceptance:** [`OPS_BASELINE_ACCEPTANCE.md`](../phase1/ops/OPS_BASELINE_ACCEPTANCE.md)

### Агенты (по отдельности)

> **Ф1:** чат + RAG по PDF ✅. **Ф2:** quality gates ниже — закрытие через [`/ops/eval`](../) и цифры, **не** галочка MAP без измерения.

| # | Пункт | Статус |
|---|--------|--------|
| 1 | 5 агентов отвечают в чате | ✅ |
| 2 | RAG у экономиста / маркетолога / тех. спеца (PDF) | ✅ |
| 3 | Fanout через Стратега | 🔲 → **Фаза 2** §2 |
| 4 | Email-интеграция маркетолога | 🔲 → **Фаза 2** §3 |

**Quality gates (Фаза 2 — не блокер Ф1):**

| Критерий | Статус | Где мерить / закрывать |
|----------|--------|-------------------------|
| **6 агентов: pass rate ≥ порога** | 🟡 full run 2026-06-14 **fail** | [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](../phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md) · `agents_gate_20260614_140940.json` · baseline Ф3: [`AGENTS_GATE_TUNING_BASELINE.md`](../baselines/AGENTS_GATE_TUNING_BASELINE.md) |
| Рамка порогов + цикл обучения | ✅ 2026-06-12 | [`AGENTS_LEARNING_MAP.md`](../phase2/agents/AGENTS_LEARNING_MAP.md) |
| Latency ответа p95 &lt; 3 с | 🔲 | `/ops/stats`, трейсы · [`langgraph.md`](../agents/langgraph.md) |
| RAG-контекст в ответе корректен | 🔲 | `/ops/eval`, `/ops/traces` · gate JSON |
| Fallback «не знаю» без галлюцинации | 🔲 | eval + `HERMES_LEADS_FULL_ACCEPTANCE.md` |
| A/B промптов по трейсам | 🔲 | **Фаза 3** · `qa_agent.py`, Dr. QA |

> **Пороги (черновик):** Hermes ≥85% / 30 кейсов; Analyst, Economist, Marketer, Strategist, Tech ≥75% / 15.  
> **`[x]` по gate (Ф2)** — только после зелёной таблицы в acceptance (не «инфра есть»).  
> **Ф3 (тюнинг):** после закрытия функционала Ф2 — все агенты **≥85%**, stretch **90–100%** → [`AGENTS_GATE_TUNING_BASELINE.md`](../baselines/AGENTS_GATE_TUNING_BASELINE.md) · BACKLOG.  
> **UI eval ✅ (шаг 5):** `/ops/intents/eval` — gate, вкладки, датасет; `/ops/insights` — дыры.  
> **Full gate 2026-06-14:** Hermes 72.2% 🔴, Tech 60% 🔴, Economist 73.3% 🟡 — MAP `[x]` не ставить; тюнинг → Ф3.

### Инфра — dev (Фаза 1)

> **Docker + `.env` ✅** — локальная разработка; **≠ прод готов** (см. блок ниже).

| # | Пункт | Статус |
|---|--------|--------|
| 1 | FastAPI + PostgreSQL + Redis | ✅ |
| 2 | Docker локально, `.env` | ✅ |
| 3 | `pool_pre_ping`, `pool_recycle`, `init_db` | ✅ |
| 4 | P6/CRM/лиды в git | ✅ |
| 5 | `test_email_sync` / connect | ✅ ib@ + me@ в `.env`; Sync на `/email` |

**Acceptance:** [`EMAIL_CONNECT_ACCEPTANCE.md`](../phase1/email/EMAIL_CONNECT_ACCEPTANCE.md)

### Инфра — прод (Фаза 2–3)

> Не блокер leadgen/голос Ф2. Отдельный шаг перед деплоем. Детали: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`RUNBOOK.md`](../start/RUNBOOK.md).

| # | Пункт | Статус |
|---|--------|--------|
| 1 | Структурное логирование (не `print`) | 🔲 |
| 2 | Метрики / health dashboards | 🔲 |
| 3 | Алерты при падении API | 🔲 |
| 4 | Бэкапы PostgreSQL по расписанию | 🔲 |
| 5 | HTTPS / reverse proxy (Nginx) | 🔲 |

### Безопасность (сквозное)

> **Ф1:** dev-режим, не блокер. **Ф2:** обязательно **перед выходом в интернет** (очередь **10**). **Ф3:** роли и мульти-пользователь. Детали: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`LLM.md`](../stack/LLM.md).

**Сейчас (Ф1):** ключи в `.env` + gitignore; `X-API-Key` если ключ задан; без ключа — открытый localhost; пароли почты в БД шифруются (`SECRET_KEY`).

| # | Пункт | Когда | Статус |
|---|--------|-------|--------|
| 1 | HTTPS / Nginx на проде | **Ф2** (с [Инфра прод](#инфра--прод-фаза-2–3) п.5) | 🔲 |
| 2 | Секреты: vault / secrets manager (не `.env` на сервере) | **Ф2** прод | ✅ локально · 🔲 vault |
| 3 | Маскировка PII в логах (email, телефон, ИНН) | **Ф2** | 🔲 |
| 4 | Auth обязателен: `SMARTCRM_REQUIRE_AUTH=1` + ключ на проде | **Ф2** | 🟡 ключ есть · 🔲 enforce |
| 5 | Rate limiting (публичные и тяжёлые эндпоинты) | **Ф2** | 🔲 |
| 6 | Groq/Ollama: что можно слать — **enforcement** в коде | **Ф2** | ⚠️ текст `LLM.md` · 🔲 код |
| 7 | Роли пользователей (не один общий API-ключ) | **Ф3** | 🔲 |
| 8 | Аудит действий / кто что отправил (письма, лиды) | **Ф3** | 🔲 |

**Ф2 чеклист (коротко):** HTTPS → auth на проде → rate limit → маскировка логов → vault → фильтр данных в LLM.

**Ф3 чеклист:** логин/роли, разграничение по модулям, аудит.

### Качество кода и coverage (сквозное)

> **Обязательно:** регрессия по зонам + smoke + acceptance ([`smartcrm-dev-gates.mdc`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc)).  
> **Coverage %:** **не gate** закрытия фазы; ориентир **soft ~40% Ф2**, **~60% к концу Ф2**, **~75% к концу Ф3**.  
> **Baseline:** **51.4%** (2026-06-11) — [`COVERAGE_BASELINE.md`](../baselines/COVERAGE_BASELINE.md); команда `cd backend && pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing`.  
> **CI:** [`CI_BASELINE.md`](../baselines/CI_BASELINE.md) — pytest + smoke на каждый push/PR (`main`). pytest-cov fail-under в CI — отдельный шаг.  
> **Агенты:** quality gates закрываются через `/ops/eval` с цифрами, не `[x]` в MAP без метрик.

### Открытые хвосты Фазы 1 → вернуться

> **Канон:** детали и чеклисты — только [`BACKLOG.md`](../session/BACKLOG.md). Здесь **указатель** (3–5 строк), таблицы BACKLOG **не копировать**.
>
> **Снято с хвоста (закрыто ✅):** «Расширить интенты Hermes», «UI voice_action», «Смоук голос + UI» — см. таблицу **«Голос → лиды»** выше; старый блок «Хвост Фазы 1» удалён.

| Приоритет | Что | Где в BACKLOG |
|-----------|-----|----------------|
| 🟡 | Spot-check approve delete (S04) + fanout (S02/S06) | § [👤 Ручная работа](../session/BACKLOG.md) |
| 🟡 | Битрикс: туннель :8000 + исходящий вебхук | § [Записи](../session/BACKLOG.md) · § [Активный хвост](../session/BACKLOG.md) |
| 🟢 | Live Hermes / whisper health (опц.) | § [👤 Ручная работа](../session/BACKLOG.md) |

**Новый хвост:** запись в `BACKLOG.md` + одна строка в таблице выше — **не** отдельная таблица в MAP.

---

**Статус:** ✅ **Ф1 DoD закрыта** (6/6); **→ работа Ф2** (2026-06-13, см. [архив `PHASE2_ENTRY.md`](../../archive/ops/PHASE2_ENTRY.md)). Хвосты L306–318 не блокируют.
