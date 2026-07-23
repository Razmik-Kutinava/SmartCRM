# Чеклист: Фаза 2 — Автоматизация

**Статус фазы:** ✅ очереди 1–9 пройдены

> **Легенда:** ✅ готово (код + смоук + acceptance) · ⚠️ код ✅, хвост в `BACKLOG.md` · 🔲 не начато · `[x]` = ✅ по коду/автомату · `[ ]` = 🔲 или хвост.
> **Закрытие пункта:** pytest + acceptance → `[x]`; финальный `[x]` — только после «ок» оператора. DoD пункта → [`dev-gates`](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).
> Результаты (acceptance) — в папках областей рядом: `./{область}/*.md`. Хвосты → [`../session/BACKLOG.md`](../session/BACKLOG.md).

---

### Definition of Done — Фаза 2

> Шаблон — заполняем по мере закрытия очереди 1–9. **DoD фазы** ≠ DoD пункта → [dev-gates](../../../.cursor/rules/workflow/smartcrm-dev-gates.mdc).

| # | Критерий | Статус |
|---|----------|--------|
| 1 | Фундамент: §1 Voice Layer (все модули) + §2 fanout Стратега | 🟡 §1 ✅ · §2 🔲 |
| 2 | §3 Email: IMAP/SMTP, черновик, апрув и отправка | ✅ |
| 3 | §4 RAG: кэш enrich + авто-чанки | ✅ |
| 4 | Сценарий **«голосом письмо → апрув → отправка»** E2E | 🔲 |
| 5 | §8 leadgen+голос: live UI + полный pipeline | ✅ |
| 6 | Решение: **«ок, идём в Фазу 3»** | 🔲 |

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

> Не очередь «после фич», а **гейт деплоя**. Хвосты → [`BACKLOG.md`](../session/BACKLOG.md) § Безопасность.

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

- [x] Hermes: `module` + `intent` + `ui_action` для email, поиска, аналитики, агентов, RAG — ✅ [`HERMES_MODULES_ACCEPTANCE.md`](../phase2/voice/HERMES_MODULES_ACCEPTANCE.md) · [`VOICE_LAYER_ACCEPTANCE.md`](../phase2/voice/VOICE_LAYER_ACCEPTANCE.md)
- [x] Событие `voice_action` на фронте (WS `/ws/voice`) — `+layout.svelte` → `handleVoiceAction`
- [x] UI: модалка с ответом агента — `VoiceActionHost.svelte` (агенты, RAG, email)
- [x] UI: навигация SvelteKit по голосу — route + `/search?q=` + analytics context
- [x] UI: фильтр/подсветка в списках — `voiceLeadFilter` + minScore + highlight banner
- [x] Апрув перед отправкой/деструктивом (кнопка) — delete_lead, send_email, save_to_rag

### 2. Оркестрация (Стратег fanout)

> См. [`langgraph.md`](../agents/langgraph.md#пакет-voice_action-стратег--ui)

- [x] LangGraph supervisor: выбор агентов (выборочный fanout) — ✅ [`FANOUT_SUPERVISOR_ACCEPTANCE.md`](../phase2/agents/FANOUT_SUPERVISOR_ACCEPTANCE.md)
- [x] Параллельный fanout 2+ агентов — ✅ [`FANOUT_PARALLEL_ACCEPTANCE.md`](../phase2/agents/FANOUT_PARALLEL_ACCEPTANCE.md)
- [x] Синтез в один ответ → модалка — ✅ [`FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md`](../phase2/agents/FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md)
- [x] Сценарий: анализ + письмо — ✅ [`SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md`](../phase2/agents/SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md)
- [x] Сценарий: оценка тендера (тех + эконом) — ✅ [`SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md`](../phase2/agents/SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md)
- [x] Сценарий: еженедельный отчёт — ✅ [`SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md`](../phase2/agents/SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md)
- [x] Сценарий: похожие клиенты — ✅ [`SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md`](../phase2/agents/SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md)

### 3. Email-агент

> Режимы: Ассистирующий (Ф2) / Автономный (Ф3) — [`PRD.md`](PRD.md) Email-агент

- [x] IMAP/SMTP, credentials в env — ✅ [`EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md`](../phase2/email/EMAIL_IMAP_SMTP_ENV_ACCEPTANCE.md)
- [x] Фоновый синк входящих — ✅ [`EMAIL_BACKGROUND_SYNC_ACCEPTANCE.md`](../phase2/email/EMAIL_BACKGROUND_SYNC_ACCEPTANCE.md)
- [x] Список `/email` — ✅ [`EMAIL_LIST_PAGE_ACCEPTANCE.md`](../phase2/email/EMAIL_LIST_PAGE_ACCEPTANCE.md)
- [x] Анализ типа письма + черновик (Маркетолог) — ✅ [`EMAIL_DRAFT_ANALYZE_ACCEPTANCE.md`](../phase2/email/EMAIL_DRAFT_ANALYZE_ACCEPTANCE.md)
- [x] Апрув и отправка (голос или кнопка) — ✅ [`EMAIL_APPROVE_SEND_ACCEPTANCE.md`](../phase2/email/EMAIL_APPROVE_SEND_ACCEPTANCE.md)
- [x] Голосовые команды email — ✅ [`EMAIL_VOICE_COMMANDS_ACCEPTANCE.md`](../phase2/email/EMAIL_VOICE_COMMANDS_ACCEPTANCE.md)

### 4. Поиск → RAG авто

> Пайплайн Search-to-Q&A: [`RAG.md`](../stack/RAG.md#search-to-qa-фаза-2)  
> **Enrich Ф1 закрыт** — `/search` + PATCH в карточку: [`SEARCH_ENRICH_LEAD_ACCEPTANCE.md`](../phase1/search/SEARCH_ENRICH_LEAD_ACCEPTANCE.md)

- [x] Авто-чанки при релевантности > порога — ✅ [`SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md`](../phase2/rag/SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md)
- [x] Факты из диалога агента → RAG — ✅ [`AGENT_DIALOGUE_RAG_ACCEPTANCE.md`](../phase2/rag/AGENT_DIALOGUE_RAG_ACCEPTANCE.md)
- [x] «Сохранить в базу» везде в поиске — ✅ [`SEARCH_SAVE_EVERYWHERE_ACCEPTANCE.md`](../phase2/rag/SEARCH_SAVE_EVERYWHERE_ACCEPTANCE.md)
- [x] **Кэш результата enrich** (ключ: company + ИНН + industry, TTL ~24 ч) — ✅ [`SEARCH_ENRICH_CACHE_ACCEPTANCE.md`](../phase2/rag/SEARCH_ENRICH_CACHE_ACCEPTANCE.md)

### 5. Self-improvement

- [x] Версионирование промптов в Ops (агенты `/ops/agents` + Hermes `/ops/intents/improve`) — ✅ [`OPS_PROMPT_VERSIONING_ACCEPTANCE.md`](../phase2/ops/OPS_PROMPT_VERSIONING_ACCEPTANCE.md)
- [x] Откат на предыдущую версию — ✅ (restore API + UI)
- [x] Сравнение версий — ✅ (compare API + diff в UI)

### 6. Аналитика + голос

- [x] «Воронка за период» — ✅ `analytics_funnel` + API/UI period filter · acceptance: [`ANALYTICS_VOICE_ACCEPTANCE.md`](../phase2/analytics/ANALYTICS_VOICE_ACCEPTANCE.md)
- [x] «Цикл сделки / средний чек» — ✅ `analytics_cycle` + KPI на `/leads/analytics`
- [x] «Лиды со скором > N» — ✅ `analytics_score` → minScore на `/leads/list`
- [x] «Конверсия по источнику» — ✅ `conversionBySource` + `analytics_conversion`
- [x] Навигация на `/leads/analytics` с фильтром — ✅ voice_action query + UI context

### 7. Тендеры 

- [x] Агентский анализ документации тендера — ✅ `/evaluate` + document_text + UI · acceptance: [`TENDERS_VOICE_ACCEPTANCE.md`](../phase2/tenders/TENDERS_VOICE_ACCEPTANCE.md)
- [x] Голосовые команды по тендерам — ✅ `evaluate_tender`, `search_tenders`, `list_tenders`
- [x] Связь лида со сделкой по тендеру — ✅ `linked_lead_id`, link/create-lead API, `tenderLink` на карточке

### 8. Лидоген + голос

- [x] WS audio → `generate_lead` + navigate `/leadgen` — smoke `test_leadgen_voice_ws.py` · acceptance: [`LEADGEN_VOICE_ACCEPTANCE.md`](../phase1/leadgen/LEADGEN_VOICE_ACCEPTANCE.md)
- [x] Live UI + полный pipeline leadgen по голосу — ✅ autorun `/leadgen` + `voiceLeadgenContext` · [`LEADGEN_VOICE_F2_ACCEPTANCE.md`](../phase2/leadgen/LEADGEN_VOICE_F2_ACCEPTANCE.md)
- [x] Lookalike из won-сделок + апрув менеджера — ✅ `find_similar_clients` + `lookalike-import` + `/won-portrait`

### 9. Лиды + обогащение (enrich)

> **Ближайшее в Ф2** после закрытия Voice Layer / авто-RAG. Ф1: таб «Обогащение» на `/search`, выбор лида, «Сохранить в карточку» — ✅.

- [x] Кнопка **«Обогатить»** на карточке `/leads/{id}` (one-click → `enrich-lead` → PATCH полей без перехода в `/search`) — ✅ [`LEADS_CARD_ENRICH_ACCEPTANCE.md`](../phase2/leads/LEADS_CARD_ENRICH_ACCEPTANCE.md)
- [x] (опц.) Голос Hermes: «обогати лид …» — modal preview + апрув перед PATCH · [`LEADS_ENRICH_VOICE_ACCEPTANCE.md`](../phase2/leads/LEADS_ENRICH_VOICE_ACCEPTANCE.md)

---
