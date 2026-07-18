# SmartCRM — карта PRD

> Навигатор и **рабочие чеклисты по фазам**. Детали — [`PRD.md`](PRD.md), черновики — [`PRD_NOTES.md`](PRD_NOTES.md).  
> **MAP-doc:** выровнен 2026-06-10 — таблицы = истина; хвосты → [`BACKLOG.md`](../operations/session/BACKLOG.md).
>
> **Легенда статусов**
>
> | Метка | Смысл |
> |-------|--------|
> | ✅ | Готово полностью: код + автомат-смоук + acceptance (+ E2E, если нужен) |
> | ⚠️ | **Код/автомат ✅**; хвост — `BACKLOG.md` или acceptance § хвост |
> | 🔲 | Не начато / перенесено в Ф2–3 |
> | `[x]` | = ✅ по коду и автомату (перепроходим на баги); **не** скрывает ⚠️ в колонке «Итог» |
> | `[ ]` | = 🔲 или явный хвост |
>
> **Закрытие пункта MAP:** pytest + acceptance → `[x]` / ✅ в «Итог». **Снять ⚠️:** ручной E2E OK → `SESSION_STATE` → убрать ⚠️ в MAP + строку в `BACKLOG`.
>
> **DoD пункта** (pytest, smoke, миграции) → `.cursor/rules/workflow/smartcrm-dev-gates.mdc`.

---

## Что строим (одна строка)

**Один человек голосом управляет 5 AI-агентами = полноценный отдел продаж.**

## Оглавление

- [DoD Ф1](#definition-of-done--фаза-1) · [Сценарии Ф1](#фаза-1--сценарии-зачем-техтаблицы)
- [Фаза 1 — MVP](#фаза-1--mvp-проходим-первой) — [Лиды](#лиды-leads) · [Баллы](#балльная-воронка-p1p2p3-код) · [Голос](#голос--лиды-базово) · [Поиск/RAG](#поиск-и-rag-базово) · [Лидоген](#лидогенерация-leadgen) · [Тендеры](#тендеры-tenders-baseline) · [Агенты](#агенты-по-отдельности) · [Аналитика](#аналитика-базовая)
- [Хвосты Ф1 → BACKLOG](#открытые-хвосты-фазы-1--вернуться)
- [Фаза 2](#фаза-2--автоматизация) — [Порядок 1–9](#порядок-фазы-2) · [DoD Ф2](#definition-of-done--фаза-2) · [Сценарии Ф2](#фаза-2--сценарии) · §[1 Voice](#1-voice-layer-все-модули) … §[9 Enrich](#9-лиды--обогащение-enrich)
- [Фаза 3](#фаза-3--автономия) · [Фаза 4](#фаза-4--тюнинг-и-mvp) · [Сводка модулей](#сводка-модулей)

---

## Как пользоваться чеклистами

1. Идём **Фаза 1 → 2 → 3** сверху вниз.
2. `[x]` — не пропускаем: смоук, регрессия, баги в `ISSUES.md`.
3. После прохода пункта: баг → фикс; ок → оставляем `[x]`.
4. Источник деталей: `PRD_NOTES.md` (разделы по модулям).
5. Хвосты и ручная работа → [`BACKLOG.md`](../operations/session/BACKLOG.md) (не дублировать здесь таблицами).
6. Колонка **«Итог»** с ⚠️ важнее слепого `[x]` в старых списках — сводка смотрит на ⚠️.

### Definition of Done — Фаза 1

> **DoD фазы** (здесь) ≠ **DoD пункта** — pytest, smoke, миграции на строку MAP → [`.cursor/rules/workflow/smartcrm-dev-gates.mdc`](../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).

**Фаза 1 закрыта**, когда все 6 пунктов ниже ✅ **или** п.5 остаётся ⚠️, но владелец явно сказал **«ок, идём в Фазу 2»** (п.6) — не автозакрытие.

| # | Критерий | Статус |
|---|----------|--------|
| 1 | Все таблицы Ф1: ✅ / ⚠️ с хвостом в BACKLOG / явный `→ Ф2\|Ф3` | ✅ |
| 2 | Хвосты в [`BACKLOG.md`](../operations/session/BACKLOG.md) или перенесены в Ф2–3; MAP — только указатель | ✅ |
| 3 | Смоук зон + регрессия зелёные (см. dev-gates по каждому пункту) | ✅ |
| 4 | Acceptance на закрытые блоки (ссылки в колонке «Итог» таблиц) | ✅ |
| 5 | Сценарий **«голосом создать / найти лид»**: E2E audio WS + dev simulate mic | ✅ `VOICE_MIC_E2E_ACCEPTANCE.md` |
| 6 | Решение: **«ок, идём в Фазу 2»** — очередь 5 leadgen+голос | ✅ 2026-06-11 |

**Вердикт (6/6):** Ф1 **закрыта** по DoD; Ф2 старт — **очередь 5** (smoke slice ✅).

### Definition of Done — Фаза 2

> Шаблон — заполняем по мере закрытия очереди 1–9. **DoD фазы** ≠ DoD пункта → [dev-gates](../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).

| # | Критерий | Статус |
|---|----------|--------|
| 1 | Фундамент: §1 Voice Layer (все модули) + §2 fanout Стратега | 🟡 §1 ✅ · §2 🔲 |
| 2 | §3 Email: IMAP/SMTP, черновик, апрув и отправка | ✅ |
| 3 | §4 RAG: кэш enrich + авто-чанки | ✅ |
| 4 | Сценарий **«голосом письмо → апрув → отправка»** E2E | 🔲 |
| 5 | §8 leadgen+голос: live UI + полный pipeline | ✅ |
| 6 | Решение: **«ок, идём в Фазу 3»** | 🔲 |

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
| 6 | Авто-чанки из поиска / диалога | — | ✅ | §4 Ф2 — [`SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md`](../operations/phase2/rag/SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md) + dialogue + save + enrich cache |
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

**Acceptance:** [`TENDERS_BASELINE_ACCEPTANCE.md`](../operations/phase1/tenders/TENDERS_BASELINE_ACCEPTANCE.md)

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

**Acceptance:** [`ANALYTICS_BASELINE_ACCEPTANCE.md`](../operations/phase1/analytics/ANALYTICS_BASELINE_ACCEPTANCE.md)

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

**Acceptance:** [`OPS_BASELINE_ACCEPTANCE.md`](../operations/phase1/ops/OPS_BASELINE_ACCEPTANCE.md)

### Агенты (по отдельности)

> **Ф1:** чат + RAG по PDF ✅. **Ф2:** quality gates ниже — закрытие через [`/ops/eval`](../operations/) и цифры, **не** галочка MAP без измерения.

| # | Пункт | Статус |
|---|--------|--------|
| 1 | 5 агентов отвечают в чате | ✅ |
| 2 | RAG у экономиста / маркетолога / тех. спеца (PDF) | ✅ |
| 3 | Fanout через Стратега | 🔲 → **Фаза 2** §2 |
| 4 | Email-интеграция маркетолога | 🔲 → **Фаза 2** §3 |

**Quality gates (Фаза 2 — не блокер Ф1):**

| Критерий | Статус | Где мерить / закрывать |
|----------|--------|-------------------------|
| **6 агентов: pass rate ≥ порога** | 🟡 full run 2026-06-14 **fail** | [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](../operations/phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md) · `agents_gate_20260614_140940.json` · baseline Ф3: [`AGENTS_GATE_TUNING_BASELINE.md`](../operations/baselines/AGENTS_GATE_TUNING_BASELINE.md) |
| Рамка порогов + цикл обучения | ✅ 2026-06-12 | [`AGENTS_LEARNING_MAP.md`](../operations/phase2/agents/AGENTS_LEARNING_MAP.md) |
| Latency ответа p95 &lt; 3 с | 🔲 | `/ops/stats`, трейсы · [`langgraph.md`](../agents/langgraph.md) |
| RAG-контекст в ответе корректен | 🔲 | `/ops/eval`, `/ops/traces` · gate JSON |
| Fallback «не знаю» без галлюцинации | 🔲 | eval + `HERMES_LEADS_FULL_ACCEPTANCE.md` |
| A/B промптов по трейсам | 🔲 | **Фаза 3** · `qa_agent.py`, Dr. QA |

> **Пороги (черновик):** Hermes ≥85% / 30 кейсов; Analyst, Economist, Marketer, Strategist, Tech ≥75% / 15.  
> **`[x]` по gate (Ф2)** — только после зелёной таблицы в acceptance (не «инфра есть»).  
> **Ф3 (тюнинг):** после закрытия функционала Ф2 — все агенты **≥85%**, stretch **90–100%** → [`AGENTS_GATE_TUNING_BASELINE.md`](../operations/baselines/AGENTS_GATE_TUNING_BASELINE.md) · BACKLOG.  
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

**Acceptance:** [`EMAIL_CONNECT_ACCEPTANCE.md`](../operations/phase1/email/EMAIL_CONNECT_ACCEPTANCE.md)

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

> **Обязательно:** регрессия по зонам + smoke + acceptance ([`smartcrm-dev-gates.mdc`](../../.cursor/rules/workflow/smartcrm-dev-gates.mdc)).  
> **Coverage %:** **не gate** закрытия фазы; ориентир **soft ~40% Ф2**, **~60% к концу Ф2**, **~75% к концу Ф3**.  
> **Baseline:** **51.4%** (2026-06-11) — [`COVERAGE_BASELINE.md`](../operations/baselines/COVERAGE_BASELINE.md); команда `cd backend && pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing`.  
> **CI:** [`CI_BASELINE.md`](../operations/baselines/CI_BASELINE.md) — pytest + smoke на каждый push/PR (`main`). pytest-cov fail-under в CI — отдельный шаг.  
> **Агенты:** quality gates закрываются через `/ops/eval` с цифрами, не `[x]` в MAP без метрик.

### Открытые хвосты Фазы 1 → вернуться

> **Канон:** детали и чеклисты — только [`BACKLOG.md`](../operations/session/BACKLOG.md). Здесь **указатель** (3–5 строк), таблицы BACKLOG **не копировать**.
>
> **Снято с хвоста (закрыто ✅):** «Расширить интенты Hermes», «UI voice_action», «Смоук голос + UI» — см. таблицу **«Голос → лиды»** выше; старый блок «Хвост Фазы 1» удалён.

| Приоритет | Что | Где в BACKLOG |
|-----------|-----|----------------|
| 🟡 | Spot-check approve delete (S04) + fanout (S02/S06) | § [👤 Ручная работа](../operations/session/BACKLOG.md) |
| 🟡 | Битрикс: туннель :8000 + исходящий вебхук | § [Записи](../operations/session/BACKLOG.md) · § [Активный хвост](../operations/session/BACKLOG.md) |
| 🟢 | Live Hermes / whisper health (опц.) | § [👤 Ручная работа](../operations/session/BACKLOG.md) |

**Новый хвост:** запись в `BACKLOG.md` + одна строка в таблице выше — **не** отдельная таблица в MAP.

---

**Статус:** ✅ **Ф1 DoD закрыта** (6/6); **→ работа Ф2** (2026-06-13, см. [`PHASE2_ENTRY.md`](../operations/session/PHASE2_ENTRY.md)). Хвосты L306–318 не блокируют.

## Фаза 2 — Автоматизация

**Статус:** **старт Ф2** — очередь по [`§ Порядок Ф2`](#порядок-фазы-2); код Ф2 **ждёт `go`**. Очередь **5** §8 — smoke slice ⚠️; фундамент §1–§2 🔲.

### Фаза 2 — сценарии

> Процесс как у Ф1: сначала строка здесь → пункт в § MAP ниже → acceptance.

| # | Менеджер может… | Статус | Привязка MAP |
|---|-----------------|--------|--------------|
| 1 | Голосом написать письмо, получить черновик, отправить после апрува | 🔲 | [§1 Voice](#1-voice-layer-все-модули) · [§3 Email](#3-email-агент) |
| 2 | Попросить Стратега: «проанализируй лид и подготовь КП» (fanout) | 🔲 | [§2 Оркестрация](#2-оркестрация-стратег-fanout) |
| 3 | Сказать «найди похожих клиентов» → список с апрувом | ✅ | [§8 Лидоген](#8-лидоген--голос) · lookalike |
| 4 | Поиск/enrich без ручного «Сохранить в базу» — авто в RAG | ✅ | [§4 RAG авто](#4-поиск--rag-авто) |
| 5 | Голосом на `/leadgen` запустить поиск (ИНН/портрет) end-to-end в UI | ✅ | [§8 Лидоген](#8-лидоген--голос) · `LEADGEN_VOICE_F2_ACCEPTANCE.md` |

### Порядок Фазы 2

> **Процесс:** следующий **`go`** = **номер «Очередь»** из таблицы, не «что ближе».  
> **Без `go` — два кандидата:** [§8 Лидоген + голос](#8-лидоген--голос) (узкий scope) **или** [§1 Voice Layer](#1-voice-layer-все-модули) (единый контракт по всем модулям сначала).

| Очередь | MAP § | Блок | Приоритет | Статус |
|---------|-------|------|-----------|--------|
| 1 | §1 | Voice Layer — голос вне `/leads` | **фундамент** | 🟡 §1 ✅ · §2 🔲 |
| 2 | §2 | Оркестрация — fanout Стратега | **фундамент** | 🔲 |
| 3 | §3 | Email-агент | важно | ✅ |
| 4 | §4 | Поиск → RAG авто (кэш enrich, авто-чанки) | важно | ✅ |
| 5 | §8 | Лидоген + голос `/leadgen` | ✅ Ф2 | ✅ |
| 6 | §9 | Лиды enrich — кнопка на карточке | важно | ✅ |
| 7 | §5 | Self-improvement — версии промптов | можно позже | ✅ |
| 8 | §6 | Аналитика + голос | ✅ Ф2 | ✅ |
| 9 | §7 | Тендеры — агент-анализ | ✅ Ф2 | ✅ |
| **10** | **§Безопасность** | **Перед деплоем в интернет** | **блокер прода** | 🔲 |

### Безопасность — Фаза 2 (перед продом)

> Не очередь «после фич», а **гейт деплоя**. Хвосты → [`BACKLOG.md`](../operations/session/BACKLOG.md) § Безопасность.

- [ ] HTTPS + reverse proxy (Nginx / Caddy)
- [ ] `SMARTCRM_REQUIRE_AUTH=1`, ключи не в git, vault на сервере
- [ ] Rate limit на API (особенно `/api/voice`, `/api/search`, webhooks)
- [ ] Маскирование email/телефона/ИНН в логах и трейсах
- [ ] Enforcement: не слать PII/секреты в Groq/Ollama без политики (`LLM.md`)
- [ ] pytest + acceptance `SECURITY_BASELINE_ACCEPTANCE.md` (создать при `go`)

### Безопасность — Фаза 3

- [ ] Пользователи и роли (менеджер / админ / read-only)
- [ ] Аудит: кто отправил письмо, кто удалил лид, кто выгрузил данные

### 1. Voice Layer (все модули)

> **Не Ф1:** голосовой CRUD лидов + mic E2E уже в [«Голос → лиды»](#голос--лиды-базово) (✅ `VOICE_MIC_E2E_ACCEPTANCE.md`). **Здесь — остальные модули:** email, поиск, аналитика, RAG, агенты.  
> Контракт: [`PRD.md`](PRD.md) Voice Layer · [`ARCHITECTURE.md`](ARCHITECTURE.md#контракт-voice_action)

- [x] Hermes: `module` + `intent` + `ui_action` для email, поиска, аналитики, агентов, RAG — ✅ [`HERMES_MODULES_ACCEPTANCE.md`](../operations/phase2/voice/HERMES_MODULES_ACCEPTANCE.md) · [`VOICE_LAYER_ACCEPTANCE.md`](../operations/phase2/voice/VOICE_LAYER_ACCEPTANCE.md)
- [x] Событие `voice_action` на фронте (WS `/ws/voice`) — `+layout.svelte` → `handleVoiceAction`
- [x] UI: модалка с ответом агента — `VoiceActionHost.svelte` (агенты, RAG, email)
- [x] UI: навигация SvelteKit по голосу — route + `/search?q=` + analytics context
- [x] UI: фильтр/подсветка в списках — `voiceLeadFilter` + minScore + highlight banner
- [x] Апрув перед отправкой/деструктивом (кнопка) — delete_lead, send_email, save_to_rag

### 2. Оркестрация (Стратег fanout)

> См. [`langgraph.md`](../agents/langgraph.md#пакет-voice_action-стратег--ui)

- [x] LangGraph supervisor: выбор агентов (выборочный fanout) — ✅ [`FANOUT_SUPERVISOR_ACCEPTANCE.md`](../operations/phase2/agents/FANOUT_SUPERVISOR_ACCEPTANCE.md)
- [x] Параллельный fanout 2+ агентов — ✅ [`FANOUT_PARALLEL_ACCEPTANCE.md`](../operations/phase2/agents/FANOUT_PARALLEL_ACCEPTANCE.md)
- [x] Синтез в один ответ → модалка — ✅ [`FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md`](../operations/phase2/agents/FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md)
- [x] Сценарий: анализ + письмо — ✅ [`SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md`](../operations/phase2/agents/SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md)
- [x] Сценарий: оценка тендера (тех + эконом) — ✅ [`SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md`](../operations/phase2/agents/SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md)
- [x] Сценарий: еженедельный отчёт — ✅ [`SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md`](../operations/phase2/agents/SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md)
- [x] Сценарий: похожие клиенты — ✅ [`SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md`](../operations/phase2/agents/SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md)

### 3. Email-агент

> Режимы: Ассистирующий (Ф2) / Автономный (Ф3) — [`PRD.md`](PRD.md) Email-агент

- [x] IMAP/SMTP, credentials в env — ✅ [`EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md`](../operations/phase2/email/EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md)
- [x] Фоновый синк входящих — ✅ [`EMAIL_BACKGROUND_SYNC_ACCEPTANCE.md`](../operations/phase2/email/EMAIL_BACKGROUND_SYNC_ACCEPTANCE.md)
- [x] Список `/email` — ✅ [`EMAIL_LIST_PAGE_ACCEPTANCE.md`](../operations/phase2/email/EMAIL_LIST_PAGE_ACCEPTANCE.md)
- [x] Анализ типа письма + черновик (Маркетолог) — ✅ [`EMAIL_DRAFT_ANALYZE_ACCEPTANCE.md`](../operations/phase2/email/EMAIL_DRAFT_ANALYZE_ACCEPTANCE.md)
- [x] Апрув и отправка (голос или кнопка) — ✅ [`EMAIL_APPROVE_SEND_ACCEPTANCE.md`](../operations/phase2/email/EMAIL_APPROVE_SEND_ACCEPTANCE.md)
- [x] Голосовые команды email — ✅ [`EMAIL_VOICE_COMMANDS_ACCEPTANCE.md`](../operations/phase2/email/EMAIL_VOICE_COMMANDS_ACCEPTANCE.md)

### 4. Поиск → RAG авто

> Пайплайн Search-to-Q&A: [`RAG.md`](../stack/RAG.md#search-to-qa-фаза-2)  
> **Enrich Ф1 закрыт** — `/search` + PATCH в карточку: [`SEARCH_ENRICH_LEAD_ACCEPTANCE.md`](../operations/phase1/search/SEARCH_ENRICH_LEAD_ACCEPTANCE.md)

- [x] Авто-чанки при релевантности > порога — ✅ [`SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md`](../operations/phase2/rag/SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md)
- [x] Факты из диалога агента → RAG — ✅ [`AGENT_DIALOGUE_RAG_ACCEPTANCE.md`](../operations/phase2/rag/AGENT_DIALOGUE_RAG_ACCEPTANCE.md)
- [x] «Сохранить в базу» везде в поиске — ✅ [`SEARCH_SAVE_EVERYWHERE_ACCEPTANCE.md`](../operations/phase2/rag/SEARCH_SAVE_EVERYWHERE_ACCEPTANCE.md)
- [x] **Кэш результата enrich** (ключ: company + ИНН + industry, TTL ~24 ч) — ✅ [`SEARCH_ENRICH_CACHE_ACCEPTANCE.md`](../operations/phase2/rag/SEARCH_ENRICH_CACHE_ACCEPTANCE.md)

### 5. Self-improvement

- [x] Версионирование промптов в Ops (агенты `/ops/agents` + Hermes `/ops/intents/improve`) — ✅ [`OPS_PROMPT_VERSIONING_ACCEPTANCE.md`](../operations/phase2/ops/OPS_PROMPT_VERSIONING_ACCEPTANCE.md)
- [x] Откат на предыдущую версию — ✅ (restore API + UI)
- [x] Сравнение версий — ✅ (compare API + diff в UI)

### 6. Аналитика + голос

- [x] «Воронка за период» — ✅ `analytics_funnel` + API/UI period filter · acceptance: [`ANALYTICS_VOICE_ACCEPTANCE.md`](../operations/phase2/analytics/ANALYTICS_VOICE_ACCEPTANCE.md)
- [x] «Цикл сделки / средний чек» — ✅ `analytics_cycle` + KPI на `/leads/analytics`
- [x] «Лиды со скором > N» — ✅ `analytics_score` → minScore на `/leads/list`
- [x] «Конверсия по источнику» — ✅ `conversionBySource` + `analytics_conversion`
- [x] Навигация на `/leads/analytics` с фильтром — ✅ voice_action query + UI context

### 7. Тендеры 

- [x] Агентский анализ документации тендера — ✅ `/evaluate` + document_text + UI · acceptance: [`TENDERS_VOICE_ACCEPTANCE.md`](../operations/phase2/tenders/TENDERS_VOICE_ACCEPTANCE.md)
- [x] Голосовые команды по тендерам — ✅ `evaluate_tender`, `search_tenders`, `list_tenders`
- [x] Связь лида со сделкой по тендеру — ✅ `linked_lead_id`, link/create-lead API, `tenderLink` на карточке

### 8. Лидоген + голос

- [x] WS audio → `generate_lead` + navigate `/leadgen` — smoke `test_leadgen_voice_ws.py` · acceptance: [`LEADGEN_VOICE_ACCEPTANCE.md`](../operations/phase1/leadgen/LEADGEN_VOICE_ACCEPTANCE.md)
- [x] Live UI + полный pipeline leadgen по голосу — ✅ autorun `/leadgen` + `voiceLeadgenContext` · [`LEADGEN_VOICE_F2_ACCEPTANCE.md`](../operations/phase2/leadgen/LEADGEN_VOICE_F2_ACCEPTANCE.md)
- [x] Lookalike из won-сделок + апрув менеджера — ✅ `find_similar_clients` + `lookalike-import` + `/won-portrait`

### 9. Лиды + обогащение (enrich)

> **Ближайшее в Ф2** после закрытия Voice Layer / авто-RAG. Ф1: таб «Обогащение» на `/search`, выбор лида, «Сохранить в карточку» — ✅.

- [x] Кнопка **«Обогатить»** на карточке `/leads/{id}` (one-click → `enrich-lead` → PATCH полей без перехода в `/search`) — ✅ [`LEADS_CARD_ENRICH_ACCEPTANCE.md`](../operations/phase2/leads/LEADS_CARD_ENRICH_ACCEPTANCE.md)
- [x] (опц.) Голос Hermes: «обогати лид …» — modal preview + апрув перед PATCH · [`LEADS_ENRICH_VOICE_ACCEPTANCE.md`](../operations/phase2/leads/LEADS_ENRICH_VOICE_ACCEPTANCE.md)

---

## Фаза 3 — Автономия

**Порядок:** голосовой апрув → email цепочки → тех. спец (тендеры) → аналитика v2 → краулинг/A/B → Telegram → CRM → экспорт.

### Voice

- [x] Подтверждение голосом («да, отправляй» / «нет») · [`F3_VOICE_APPROVAL_ACCEPTANCE.md`](../operations/phase3/voice/F3_VOICE_APPROVAL_ACCEPTANCE.md)
- [x] «Переделай короче» голосом · см. acceptance §2
- [x] История команд Ops → Voice · см. acceptance §3

### Email

- [x] Автоответ FAQ по правилам Ops · [`F3_EMAIL_AUTONOMY_ACCEPTANCE.md`](../operations/phase3/email/F3_EMAIL_AUTONOMY_ACCEPTANCE.md)
- [x] Рассылки по сегменту лидов · см. acceptance §2
- [x] Цепочки 20 касаний (автономно) · см. acceptance §3 · LLM под продукт [`email_nurture.md`](../modules/email_nurture.md) · **UI:** `/email` + кнопка «Рассылка» на карточке лида
- [x] Автолинк письмо → лид по домену · см. acceptance §4

### Self-improvement

- [x] **Quality gate tuning:** все агенты ≥85% (baseline 2026-06-14: Hermes 72.2%, Tech 60%) → [`AGENTS_GATE_TUNING_BASELINE.md`](../operations/baselines/AGENTS_GATE_TUNING_BASELINE.md) · [`F3_GATE_TUNING_ACCEPTANCE.md`](../operations/phase3/agents/F3_GATE_TUNING_ACCEPTANCE.md) — **A+B+C ✅ 2026-06-17**, апрув «ок»
- [x] Краулинг URL вендоров → RAG тех. спеца · **live 871 чанк, 10 PDF** · шаг1–4 ✅ [`F3_VENDOR_CRAWL_ACCEPTANCE.md`](../operations/phase3/rag/F3_VENDOR_CRAWL_ACCEPTANCE.md) · тюнинг → **Ф4** · апрув «ок» 2026-06-17
- [x] A/B промптов по трейсам · [`F3_PROMPT_AB_TRACES_ACCEPTANCE.md`](../operations/phase3/agents/F3_PROMPT_AB_TRACES_ACCEPTANCE.md) · апрув «ок» 2026-06-17
- [x] Авто-суфлёр Стратега · [`F3_STRATEGIST_SUGGESTER_ACCEPTANCE.md`](../operations/phase3/agents/F3_STRATEGIST_SUGGESTER_ACCEPTANCE.md) · тюнинг → **Ф4** · апрув «ок» 2026-06-17

### Тех. спец — тендеры

> Один агент: RAG вендоров + мониторинг закупок + разбор ТЗ. Не отдельный «тендерный агент».

- [x] Мониторинг ключевых слов / ОКПД2 24/7 · [`F3_TECH_TENDER_MONITOR_ACCEPTANCE.md`](../operations/phase3/tenders/F3_TECH_TENDER_MONITOR_ACCEPTANCE.md) · апрув «ок» 2026-06-17
- [x] Уведомления + календарь дедлайнов · [`F3_TECH_TENDER_NOTIFY_CALENDAR_ACCEPTANCE.md`](../operations/phase3/tenders/F3_TECH_TENDER_NOTIFY_CALENDAR_ACCEPTANCE.md) · апрув «ок» 2026-06-17
- [x] Дожать бесплатные источники (Gosplan prod, TenderGuru, мониторинг, DataNewton, доки) · [`F3_TECH_TENDER_SOURCES_ACCEPTANCE.md`](../operations/phase3/tenders/F3_TECH_TENDER_SOURCES_ACCEPTANCE.md) · Контур → **Ф4** · апрув «ок» 2026-06-17
- [x] Решение участвовать/нет с обоснованием (Тех. спец + Экономист → Стратег) · [`F3_TECH_TENDER_PARTICIPATION_ACCEPTANCE.md`](../operations/phase3/tenders/F3_TECH_TENDER_PARTICIPATION_ACCEPTANCE.md) · апрув «ок» 2026-06-17

### Аналитика v2

- [x] Когортный анализ · [`F3_ANALYTICS_V2_COHORT_ACCEPTANCE.md`](../operations/phase3/analytics/F3_ANALYTICS_V2_COHORT_ACCEPTANCE.md)
- [x] Эффективность агентов по трейсам · [`F3_ANALYTICS_V2_AGENT_TRACES_ACCEPTANCE.md`](../operations/phase3/analytics/F3_ANALYTICS_V2_AGENT_TRACES_ACCEPTANCE.md)
- [x] Воронка по источнику · [`F3_ANALYTICS_V2_FUNNEL_SOURCE_ACCEPTANCE.md`](../operations/phase3/analytics/F3_ANALYTICS_V2_FUNNEL_SOURCE_ACCEPTANCE.md)
- [x] Прогноз закрытия (Экономист) · [`F3_ANALYTICS_V2_CLOSE_FORECAST_ACCEPTANCE.md`](../operations/phase3/analytics/F3_ANALYTICS_V2_CLOSE_FORECAST_ACCEPTANCE.md)

### Платформа

- [x] Telegram-бот · [`F3_PLATFORM_TELEGRAM_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_TELEGRAM_ACCEPTANCE.md) · апрув 2026-06-17
- [x] Экспорт Excel/PDF (воронка, карточка, тендеры) · [`F3_PLATFORM_EXPORT_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_EXPORT_ACCEPTANCE.md)
- [x] Импорт/экспорт Битрикс24, AmoCRM, HubSpot, CSV · CSV: [`F3_PLATFORM_CSV_SYNC_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_CSV_SYNC_ACCEPTANCE.md) · Битрикс push: [`F3_PLATFORM_BITRIX_PUSH_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_BITRIX_PUSH_ACCEPTANCE.md) · Amo: [`F3_PLATFORM_AMO_SYNC_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_AMO_SYNC_ACCEPTANCE.md) · HubSpot: [`F3_PLATFORM_HUBSPOT_SYNC_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_HUBSPOT_SYNC_ACCEPTANCE.md)
- [x] Автономный поиск новых лидов агентами · шаг 1–7: [`F3_PLATFORM_LEAD_HUNT_ACCEPTANCE.md`](../operations/phase3/platform/F3_PLATFORM_LEAD_HUNT_ACCEPTANCE.md) · апрув 2026-06-17

### Баллы P3 (остаток)

- [x] Расширенные SLA-протоколы + эскалация · [`F3_SLA_PROTOCOLS_ACCEPTANCE.md`](../operations/phase3/leads/F3_SLA_PROTOCOLS_ACCEPTANCE.md) · апрув 2026-06-17
- [x] Экспорт отчёта по баллам и воронке · [`F3_SCORING_EXPORT_ACCEPTANCE.md`](../operations/phase3/leads/F3_SCORING_EXPORT_ACCEPTANCE.md)

---

## Фаза 4 — Тюнинг и MVP

> Polish и доводка после базового Ф3. **Старт Ф4:** обход с дашборда — см. [`F4_DASHBOARD_ACCEPTANCE.md`](../operations/phase4/dashboard/F4_DASHBOARD_ACCEPTANCE.md).

### Дашборд (обход Ф4)

Детали: [`F4_DASHBOARD_ACCEPTANCE.md`](../operations/phase4/dashboard/F4_DASHBOARD_ACCEPTANCE.md)

- [x] Модалка «Новый лид» — дашборд + `/leads/list`, POST в БД · [`F4_DASHBOARD_ACCEPTANCE.md`](../operations/phase4/dashboard/F4_DASHBOARD_ACCEPTANCE.md) · апрув 2026-06-19

### Интеграции CRM (Ф4, перед обходом лидов)

Детали: [`F4_CRM_INTEGRATIONS_ACCEPTANCE.md`](../operations/phase4/platform/F4_CRM_INTEGRATIONS_ACCEPTANCE.md) · тюнинг [`F4_PLATFORM_TUNING.md`](../operations/phase4/platform/F4_PLATFORM_TUNING.md)

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

Детали: [`F4_LEADS_ACCEPTANCE.md`](../operations/phase4/leads/F4_LEADS_ACCEPTANCE.md)

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

Детали: [`F4_DAY_PRIORITY.md`](../operations/phase4/leads/F4_DAY_PRIORITY.md) · спека согласована 2026-06-27

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

Детали: [`F4_EMAIL_TUNING.md`](../operations/phase4/email/F4_EMAIL_TUNING.md)

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

**UI Яндекс.Почта:** [`F4_EMAIL_YANDEX_UI.md`](../operations/phase4/email/F4_EMAIL_YANDEX_UI.md)

- [x] Сайдбар + папки + жёлтая «Написать» · код 2026-06-25
- [x] Поиск pill + чипы фильтров · код 2026-06-25
- [x] «Главное» (звезда на треде) · код 2026-06-25
- [x] Тред: одно письмо + сайдбар «Письма на тему» + strip цитат · код 2026-06-25
- [ ] Browser-апрув по чеклисту `F4_EMAIL_YANDEX_UI.md`
- [ ] IMAP: непрочитанные, вложения, Trash/Drafts/Spam

### Vendor crawl → RAG tech_specialist (тюнинг)

Детали: [`F4_VENDOR_CRAWL_TUNING.md`](../operations/phase4/rag/F4_VENDOR_CRAWL_TUNING.md)

- [ ] Автокраул (`auto_crawl_enabled`, интервал, фоновый poll)
- [ ] Глубже `doc_urls` — KB, datasheet, release notes
- [ ] Метаданные чанков — продукт / тип дока (datasheet, manual, …)
- [ ] Eval retrieval — 10–20 вопросов к tech_specialist, pass rate

### A/B промптов по трейсам (тюнинг)

Детали: [`F4_PROMPT_AB_TUNING.md`](../operations/phase4/agents/F4_PROMPT_AB_TUNING.md)

- [ ] Эталон intent при 👎 на трейсе
- [ ] Больше кейсов + регрессия на 👍 / approved eval
- [ ] Выбор модели (groq / hermes3) в UI
- [ ] A/B для промптов агентов (`/ops/agents`)
- [ ] Suggest-prompt → сразу A/B
- [ ] История отчётов A/B в Ops
- [ ] Dr. QA / KPI-gate в UI

### Авто-суфлёр Стратега (тюнинг)

Детали: [`F4_STRATEGIST_SUGGESTER_TUNING.md`](../operations/phase4/agents/F4_STRATEGIST_SUGGESTER_TUNING.md)

- [ ] Runtime агентов читает `agent_prompt_*.txt`
- [ ] 👎 с ожидаемым ответом / intent
- [ ] Больше сигналов + агрегация по агенту
- [ ] После apply → gate / A/B
- [ ] История предложений суфлёра
- [ ] Периодический запуск / очередь Ops
- [ ] Цепочка Hermes: suggest → A/B → apply
- [ ] Суфлёр по одному агенту в UI

### Контур.Закупки (после gate)

Детали: [`F4_KONTUR_GATE.md`](../operations/phase4/tenders/F4_KONTUR_GATE.md)

- [ ] Gate: первая тендерная сделка + go оператора
- [ ] Адаптер `tender_sources/kontur.py` + `TENDER_PROVIDER=kontur`
- [ ] Smoke: search / monitor / карточка без смены UI

### Тех. спец — тендеры (тюнинг Ф4)

Детали: [`F4_TECH_TENDER_TUNING.md`](../operations/phase4/tenders/F4_TECH_TENDER_TUNING.md)

- [ ] Автопайплайн: мониторинг → скачать доки → оценка → пуш с вердиктом
- [ ] Автозагрузка ТЗ/PDF с площадки (кэш по external_id)
- [ ] UI: матрица «ТЗ ↔ продукты» (ok / gap / risk)
- [ ] Мониторинг → задача/лид в CRM по вердикту + напоминания
- [ ] Eval/gate качества тендерного тех. разбора (15–20 кейсов)

### Аналитика v2 (тюнинг Ф4)

Детали: [`F4_ANALYTICS_V2_TUNING.md`](../operations/phase4/analytics/F4_ANALYTICS_V2_TUNING.md)

- [ ] Прогноз на карточке лида + поле `expected_close_at`
- [ ] Срез «закрытие по кварталу/месяцу» на analytics
- [ ] Калибровка % стадий по реальным won/lost из БД
- [ ] LLM-Экономист по запросу на лид (кэш, rationale)
- [ ] 👎/👍 по агенту в трейсе + связка stats → A/B/суфлёр
- [ ] Когорты по неделе/кварталу (переключатель)

### Баллы (тюнинг Ф4)

Детали: [`F4_SCORING_TUNING.md`](../operations/phase4/leads/F4_SCORING_TUNING.md)

- [ ] UI весов `scoring_advisory` в Ops (`/ops/crm`) — сейчас только API/JSON, на карточке ссылка врёт
- [ ] Breakdown подсказки на карточке лида (этап, сумма, апрувы, штрафы)
- [ ] Список лидов: флаги `hasScoreWarnings` / `scoreDivergent` + фильтры
- [ ] Прогноз закрытия на карточке (перекрёст с Analytics v2)
- [ ] Единые пороги CRM ↔ лидоген или явная подпись в UI
- [ ] Ops-видимость расхождений балла (badge / очередь)

### Платформа

Детали: [`F4_PLATFORM_TUNING.md`](../operations/phase4/platform/F4_PLATFORM_TUNING.md)

- [ ] Экран интеграций в UI (Битрикс, Amo, HubSpot, Telegram) — без правки `.env`
- [ ] Credentials в БД (шифрование), статусы подключения, OAuth/мастера
- [ ] Расписание синка + маппинг стадий + конфликты полей
- [ ] Битрикс: исходящий вебхук из UI + подсказка туннеля
- [ ] Telegram: привязка чата из UI, дайджест, уведомления тендеров
- [x] SLA-протоколы + эскалация — см. P3 [`F3_SLA_PROTOCOLS_ACCEPTANCE.md`](../operations/phase3/leads/F3_SLA_PROTOCOLS_ACCEPTANCE.md)
- [x] Экспорт отчёта по баллам и воронке — см. P3 [`F3_SCORING_EXPORT_ACCEPTANCE.md`](../operations/phase3/leads/F3_SCORING_EXPORT_ACCEPTANCE.md)
- [ ] Acceptance + smoke живых интеграций

---

## Сводка модулей

| Модуль | Фаза | Сдано | Вернуться / следующий шаг |
|--------|------|-------|---------------------------|
| Лиды | 1 | ✅ 2026-06-08 | — |
| Баллы | 1 (+P3) | ✅ P3 | Ф4: [`F4_SCORING_TUNING.md`](../operations/phase4/leads/F4_SCORING_TUNING.md) |
| Голос лиды | 1 | ✅ (хвосты 🟡) 2026-06-11 | `VOICE_MIC_E2E_ACCEPTANCE.md`; п.3/5 spot-check → `BACKLOG` |
| Поиск/RAG | 1→2 | ✅ база | Ф2 §4: кэш enrich, авто-чанки |
| Лиды enrich | 2 | ✅ | Ф2 §9: кнопка + голос enrich — `LEADS_CARD_ENRICH_ACCEPTANCE.md`, `LEADS_ENRICH_VOICE_ACCEPTANCE.md` |
| Лидоген | 1→2 | ✅ Ф1 | **Ф2 §8:** голос ✅ · `LEADGEN_VOICE_F2_ACCEPTANCE.md` |
| Тендеры | 1→2→3 | ✅ baseline 2026-06-11 | `TENDERS_BASELINE_ACCEPTANCE.md` · Ф2 §7 голос/платный API |
| Email | 2→3→4 | 🔲 | Ф4: [`F4_EMAIL_TUNING.md`](../operations/phase4/email/F4_EMAIL_TUNING.md) |
| Оркестрация | 2 | 🔲 | Ф2 §2: fanout |
| Агенты | 1→2 | ✅ чат | Ф2 quality gates → `/ops/eval` |
| Безопасность | 2→3 | ⚠️ dev OK | **Ф2 оч.10** перед продом · **Ф3** роли/аудит |
| Инфра прод | 2→3 | 🔲 | отдельный шаг перед деплоем |
| Качество/coverage | сквозное | ✅ smoke | ориентир 60%/75% Ф2/Ф3 · не gate · dev-gates |
| Ops | 1→2 | ✅ | Ф2 §5: версии промптов |
| Аналитика | 1→2→3 | ✅ база | Ф2 §6: голос |

---

## Карта документа (кратко)

```
PRD_MAP.md  ← ты здесь (чеклисты)
PRD.md      ← требования и детали модулей
PRD_NOTES   ← черновики и «как работает»
ARCHITECTURE ← техника, API, DDL
```

---

## Агенты

```
┌─────────────────────────────────────────────┐
│              СТРАТЕГ (supervisor)            │
└──────┬──────────┬──────────┬───────┬─────────┘
  Аналитик   Экономист  Маркетолог  Тех.спец
```

---

## Цикл голосовой команды

```
Голос → Whisper → Hermes {module,intent} → LangGraph → действие → UI-реакция → [апрув]
```

---

## Стек (кратко)

SvelteKit · FastAPI · PostgreSQL · Redis · LangGraph · Groq → Ollama · Chroma · Docker · Nginx

→ детали и дополнения: раздел в [`PRD_NOTES.md`](PRD_NOTES.md#-стек-и-ключевые-документы)

---

## Связанные документы

| Что | Где |
|-----|-----|
| Чеклисты фаз | `docs/product/PRD_MAP.md` |
| Полный PRD | `docs/product/PRD.md` |
| Черновики / детали | `docs/product/PRD_NOTES.md` |
| Архитектура | `docs/product/ARCHITECTURE.md` |
| Операционка | `docs/operations/` (CHANGELOG, ISSUES, HANDOFF) |
| LangGraph | `docs/agents/langgraph.md` |
| Лиды | `docs/modules/leads.md` |
| Тендеры | `docs/modules/tenders.md` |
