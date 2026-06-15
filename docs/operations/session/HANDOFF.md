# HANDOFF

`Спринт:[Ф3] | Задача:[Email хвосты A — me@, relink, FAQ] | Статус: ✅ done`

> **→ Следующий агент:** Ф3 Self-improvement — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-13:** me@ — MX Яндекс, хост `imap.yandex.com` (не Hostland); connect OK `imported=50`; relink+FAQ OK. **Коммит:** `6ff7f4e`.

**2026-06-15 (Ф3 Email live):** ib@ connect+sync+SMTP OK; me@ connect 400; `smoke_email_smtp_send.py`; acceptance §Live. **Коммит:** `b207622`.

**2026-06-15 (Ф3 Email):** FAQ autoreply; segment campaigns; nurture; domain autolink; pytest 17; MAP Email `[x]`. **Коммит:** `9a3be09`.

**Следующий `go`:** Ф3 Self-improvement / тендеры / ручной email смоук.

---

`Спринт:[Ф3] | Задача:[Voice — апрув, revise, history] | Статус: ✅ done`

> **→ Следующий агент:** Ф3 Email (цепочки, FAQ) — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-15 (Ф3 Voice):** голосовой follow-up да/нет/короче (`voiceFollowup.js` + layout intercept); `POST /api/voice/revise-draft`; `GET /api/ops/voice/history` + UI `/ops/voice`; pytest 27 passed 1 skipped; `F3_VOICE_APPROVAL_ACCEPTANCE.md`; MAP Voice 3 пункта `[x]`. **Коммит:** `cad831c`.

**Следующий `go`:** Ф3 Email или ручной смоук голосового апрува.

---

`Спринт:[Ф2] | Задача:[§9 Лиды enrich голос] | Статус: ✅ done`

> **→ Следующий агент:** §1 Voice Layer или Ф3 gate tuning — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (§9):** голос `enrich_lead` → enrich preview modal → апрув PATCH; rescue+pipeline без orchestrator; pytest 21 passed; DevTools `lead-card-enrich` на `/leads/3187`; MAP §9 полностью `[x]`. **Коммит:** `cb0de76` (ops `b82a2b8`).

**Следующий `go`:** §1 Voice Layer или Ф3 gate.

---

`Спринт:[Ф2] | Задача:[§8 Лидоген + голос] | Статус: ✅ done`

> **→ Следующий агент:** §1 Voice Layer или Ф3 gate tuning — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (§8):** live UI autorun `/leadgen`, voiceLeadgenContext, won-portrait API (DB), lookalike modal+import; pytest 23 passed; DevTools `/leadgen?autorun=1`; MAP §8 закрыт. **Коммит:** `0c3ae08` (ops `89cdf0e`).

**Следующий `go`:** §1 Voice Layer (единый контракт) или Ф3 gate.

---

`Спринт:[Ф2] | Задача:[§7 Тендеры] | Статус: ✅ done`

> **→ Следующий агент:** §8 Лидоген + голос — [`PRD_MAP.md`](../product/PRD_MAP.md) · **Ф3:** gate tuning по `go`

**2026-06-14 (§7):** evaluate API + document_text; search/list_tenders voice; linked_lead_id + link/create-lead; pytest 20 passed; MAP §7 закрыт. **Коммит:** `829d340` (ops `ef9c8d8`).

**Следующий `go`:** §8 лидоген+голос или Ф3 gate.

---

`Спринт:[Ф2] | Задача:[§6 Аналитика + голос] | Статус: ✅ done`

> **→ Следующий агент:** §6 Аналитика + голос — [`PRD_MAP.md`](../product/PRD_MAP.md) · **Ф3:** gate tuning по `go`

**2026-06-14 (§5):** `agent_prompt_versions.py`; API list/restore/compare; UI `PromptVersionPanel` на `/ops/agents`; pytest 26 passed; MAP §5 п.1–3 `[x]`. **Коммит:** `a883410`.

**Следующий `go`:** §6 аналитика+голос или Ф3 gate.

---

`Спринт:[Ф2] | Задача:[RAG хвост + §9 enrich карточка] | Статус: ✅ done`

> **→ Следующий агент:** §5 Self-improvement — [`PRD_MAP.md`](../product/PRD_MAP.md) · **Ф3:** quality gate tuning по `go`

**2026-06-14:** Закрыт хвост BACKLOG §4: `RAG_AUTO_STRUCTURE_LLM`, `RAG_DIALOGUE_LLM`, `page_fetch`, smoke+cache; кнопка «Обогатить» на `/leads/{id}`; pytest 31 passed. **Quality gate ≥85%** — остаётся **Ф3** (`AGENTS_GATE_TUNING_BASELINE.md`). **Коммит:** `934a84f`.

**Следующий `go`:** §5 Self-improvement или Ф3 gate tuning.

---

`Спринт:[Ф2] | Задача:[§4 RAG п.4 кэш enrich] | Статус: ✅ done`

> **→ Следующий агент:** §5 Self-improvement (версионирование промптов) — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §4 п.4):** `enrich_cache.py` (company+ИНН+industry, TTL 24ч); API `force`; UI бейдж+чекбокс; pytest 14 passed; **§4 закрыт** (п.1–4); `SEARCH_ENRICH_CACHE_ACCEPTANCE.md`; MAP `[x]`. **Коммит:** `9dcf749`.

**Следующий `go`:** §5 Self-improvement или §9 enrich на карточке лида.

---

`Спринт:[Ф2] | Задача:[§4 RAG п.3 save везде в поиске] | Статус: ✅ done`

> **→ Следующий агент:** §4 п.4 «Кэш enrich» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §4 п.3):** SearchSaveRagBar на 5 вкладках `/search`; pytest 7 + smoke OK; MAP `[x]`. **Коммит:** `41c8f55`.

**Следующий `go`:** §4 п.4 кэш enrich.

---

`Спринт:[Ф2] | Задача:[§4 RAG п.2 факты диалога] | Статус: ✅ done`

> **→ Следующий агент:** §4 п.3 «Сохранить в базу везде в поиске» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §4 п.2):** `dialogue_facts` + `ingest-dialogue` + авто ops/voice + UI `/agents`; pytest 7 passed; MAP `[x]`. **Коммит:** `a27bf1c`.

**Следующий `go`:** §4 п.3 save everywhere в поиске.

---

`Спринт:[Ф2] | Задача:[gate baseline → Ф3 тюнинг в BACKLOG] | Статус: ✅ done`

> **→ Следующий агент:** §4 п.2 «Факты из диалога агента → RAG» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14:** full gate fail зафиксирован; baseline [`AGENTS_GATE_TUNING_BASELINE.md`](../baselines/AGENTS_GATE_TUNING_BASELINE.md); тюнинг ≥85% все → **Ф3 BACKLOG**, не блокер Ф2. **Коммит:** `f5d4266`.

**Следующий `go`:** §4 п.2 или продолжение MAP Ф2.

---

`Спринт:[Ф2] | Задача:[§4 RAG п.1 авто-чанки] | Статус: ✅ done`

> **→ Следующий агент:** §4 п.2 «Факты из диалога агента → RAG» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §4 п.1):** relevance + auto-ingest-rag + UI `/search`; pytest 10 passed; MAP `[x]`. **Коммит:** `c1302fc`.

**Следующий `go`:** §4 п.2 факты из диалога → RAG.

---

`Спринт:[Ф2] | Задача:[§3 email п.407 голосовые команды] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент **закрыт** · следующий блок MAP — §4 Поиск→RAG или §1 Voice E2E — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §3 п.407):** list_emails/write_email/send_email голосом; voiceEmailContext; orchestrator→marketer; pytest 33 passed (voice email zone); MAP п.407 `[x]`; **§3 все пункты `[x]`.** **Коммит:** `cbc44c0`.

**Следующий `go`:** §4 Поиск→RAG или full gate итог.

---

`Спринт:[Ф2] | Задача:[§3 email п.406 апрув и отправка] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент п.407 «Голосовые команды email» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §3 п.406):** EmailApproveModal на `/email` (reply + compose); voice send_email approve с превью + thread_id reply; pytest 8 passed; MAP п.406 `[x]`. **Коммит:** `1b3cfb3`.

**Следующий `go`:** §3 п.407 голосовые команды email.

---

`Спринт:[Ф2] | Задача:[§3 email п.405 анализ + черновик] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент п.406 «Апрув и отправка» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §3 п.405):** `POST /threads/{id}/analyze` — rule-based тип + черновик маркетолога; UI кнопка «Анализ + черновик» + «В ответ»; pytest 15 passed (email zone); MAP п.405 `[x]`. **Коммит:** `2216377`.

**Следующий `go`:** §3 п.406 апрув и отправка (кнопка / голос).

---

`Спринт:[Ф2] | Задача:[full live quality gate — фон] | Статус: 🔄 in_progress`

> **→ После прогона:** итог JSON + `AGENTS_QUALITY_GATE_ACCEPTANCE.md` → сказать агенту «ок» для MAP.

**2026-06-14 (live):** Full quality gate **111 кейсов** в фоне. Лог: `backend/data/artifacts/eval/gate_full_20260614_1628.log`. Ollama `hermes3:latest` + backend :8000. ETA **2–4 ч**. **Коммит ops:** `6e28c5f`.

**Фон backend (авто при uvicorn):** Email IMAP `EMAIL_AUTO_SYNC_MINUTES=5` · Bitrix `BITRIX_AUTO_SYNC_MINUTES=5` — **не нужен отдельный запуск**.

**Следующий шаг:** дождаться `Overall gate: pass|warn|fail` в логе → анализ → go §3 п.405.

---

`Спринт:[Ф2] | Задача:[email cleanup — legacy route + BACKLOG me@] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент п.405 «Анализ типа письма + черновик» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (cleanup):** Удалён `email/[mailbox].svelte`; BACKLOG `me@agneko.am` закрыт (пароль в `.env`); PRD_MAP инфра п.5 ✅; pytest 9 passed. **Коммит:** `1bd3c95` · ops `1e26702` · `fb924c8`.

**Следующий `go`:** §3 п.405 анализ + черновик (Маркетолог).

---

`Спринт:[Ф2] | Задача:[§3 email п.404 список /email] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент п.405 «Анализ типа письма + черновик» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §3 п.404):** Список `/email` — enriched threads API, emailListLogic, sync status bar, apiFetch; pytest 13 passed; MAP п.404 `[x]`. **Коммит:** `8f6f3ed` · ops `3f61222`.

**Следующий `go`:** §3 п.405 анализ + черновик (Маркетолог).

---

`Спринт:[Ф2] | Задача:[§3 email п.403 фоновый синк] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент п.404 «Список `/email`» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §3 п.403):** Фоновый IMAP-синк — `EMAIL_AUTO_SYNC_MINUTES` (default 5), poll loop в lifespan, `GET /api/email/sync/status`; pytest 19 passed; MAP п.403 `[x]`. **Коммит:** `20ce084` · ops `fc06460`.

**Следующий `go`:** §3 п.404 UI `/email`.

---

`Спринт:[Ф2] | Задача:[§3 email п.402 IMAP/SMTP env] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент п.403 «Фоновый синк входящих» — [`PRD_MAP.md`](../product/PRD_MAP.md)

**2026-06-14 (Ф2 §3 п.402):** IMAP/SMTP из `.env` — `core/email_config`, bootstrap API, status без секретов; pytest 20 passed; MAP п.402 `[x]`. **Коммит:** `2b84cfd` · ops `42fd984`.

**Следующий `go`:** §3 п.403 фоновый синк входящих.

---

`Спринт:[Ф2] | Задача:[хвосты B/C + lookalike import] | Статус: ✅ done`

> **→ Следующий агент:** §3 Email-агент — [`PRD_MAP.md`](../product/PRD_MAP.md) п.402

**2026-06-14 (хвост B/C):** Lookalike approve → `POST /api/leads/lookalike-import`; VoiceActionHost импорт + toast; check_agent_step paths OK. pytest 8 passed. **Коммит:** `bf3e4d8` · ops `8d009ef` · `b1052de`.

**Следующий `go`:** §3 Email-агент п.402 «IMAP/SMTP, credentials в env».

---

`Спринт:[Ф2] | Задача:[§2 оркестрация — закрыта] | Статус: ✅ все 6 сценариев`

> **→ Следующий агент:** [`SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md`](../phase2/agents/SCENARIO_SIMILAR_CLIENTS_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.396):** Сценарий `find_similar_clients` — analyst∥marketer→strategist→modal; lookalike из won/эталона; pytest 6 passed. MAP п.396 `[x]`. **§2 Оркестрация закрыта.** **Коммит:** `d9d5f4b` · ops `9c0fa76` · `d686a32` · `2a93780`.

**Следующий `go`:** §3 Email-агент **или** §8 лидоген lookalike POST /api/leads.

---

`Спринт:[Ф2] | Задача:[§2 п.395 еженедельный отчёт] | Статус: ✅ weekly_report`

> **→ Следующий агент:** [`SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md`](../phase2/agents/SCENARIO_WEEKLY_REPORT_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.395):** Сценарий `weekly_report` — analyst∥economist∥marketer→strategist→modal; CRM KPI в `payload.report`; rescue CPU; route `/leads/analytics`; pytest 7 passed. MAP п.395 `[x]`. **Коммит:** `c799a4d` · ops `bc5b462`.

**Следующий `go`:** §2 п.396 «Похожие клиенты».

---

`Спринт:[Ф2] | Задача:[§2 п.394 оценка тендера] | Статус: ✅ evaluate_tender`

> **→ Следующий агент:** [`SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md`](../phase2/agents/SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.394):** Сценарий `evaluate_tender` — tech∥economist→strategist→modal; rescue CPU; module tenders; pytest 15+ passed. MAP п.394 `[x]`. **Коммит:** `96b9843`.

**Следующий `go`:** §2 п.395 «Еженедельный отчёт».

---

`Спринт:[Ф2] | Задача:[§2 п.393 анализ+письмо] | Статус: ✅ scenario analysis_email`

> **→ Следующий агент:** [`SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md`](../phase2/agents/SCENARIO_ANALYSIS_EMAIL_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.393):** Сценарий `analyze_and_email` — analyst∥marketer→strategist→modal; rescue CPU; first_email в draft; pytest 48 passed. MAP п.393 `[x]`. **Коммит:** `8af96ec`.

**Следующий `go`:** §2 п.394 «Оценка тендера (тех + эконом)».

---

`Спринт:[Ф2] | Задача:[§2 п.3 синтез → модалка] | Статус: ✅ synthesis modal`

> **→ Следующий агент:** [`FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md`](../phase2/agents/FANOUT_SYNTHESIS_MODAL_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.3):** Синтез fanout → `voice_action` modal с `payload.synthesis`; UI блок «Решение»; pytest 44 passed. MAP п.392 `[x]`. **Коммит:** `338d4f5` (feat) · ops `383562d`.

**Следующий `go`:** §2 п.393 «Сценарий: анализ + письмо» **или** другой именованный сценарий.

---

`Спринт:[Ф2] | Задача:[§2 п.2 parallel fanout 2+] | Статус: ✅ fanout_parallel`

> **→ Следующий агент:** [`FANOUT_PARALLEL_ACCEPTANCE.md`](../phase2/agents/FANOUT_PARALLEL_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.2):** Параллельный fanout 2+ — `fanout_parallel.py`, Hermes `parallel`, метрики в result; leadgen: fanout до pipeline; pytest 20 passed. MAP п.391 `[x]`. **Коммит:** `1460d62` (+ ops `36a9cfe`, `6c6de75`).

**Следующий `go`:** §2 п.392 «Синтез в модалку voice_action» **или** именованный сценарий (п.393+).

---

`Спринт:[Ф2] | Задача:[§2 п.1 LangGraph supervisor] | Статус: ✅ fanout выборочный`

> **→ Следующий агент:** [`FANOUT_SUPERVISOR_ACCEPTANCE.md`](../phase2/agents/FANOUT_SUPERVISOR_ACCEPTANCE.md)

**2026-06-14 (Ф2 §2 п.1):** LangGraph supervisor — `supervisor.py` + `graph.py` (supervisor→fanout→strategist); Hermes `agents[]` задаёт подмножество; pytest 15 passed. MAP п.390 `[x]`. **Коммит:** `d3ca7e0`.

**Следующий `go`:** §2 п.2 «Параллельный fanout 2+ агентов» **или** именованный сценарий.

---

`Спринт:[Ф2] | Задача:[Voice Layer §1 — закрыт] | Статус: ✅ Hermes + UI voice_action`

> **→ Следующий агент:** [`operations/README.md`](../README.md) → [`phase2/voice/VOICE_LAYER_ACCEPTANCE.md`](../phase2/voice/VOICE_LAYER_ACCEPTANCE.md)

**2026-06-14 (Ф2 §1 закрыт):** Voice Layer полностью — Hermes `module`+`ui_action`, фронт (WS, modal, navigate, filter/minScore, approve send_email/save_to_rag), rescue eval `cases_modules.jsonl`, smoke `scripts/smoke_voice_layer.py` **72 passed**. MAP §1 п.379–384 — `[x]`. **Коммит:** `f2b618e`. Хвост 🟢: live LLM eval (не rescue) — опционально.

**Следующий `go`:** §2 fanout Стратега **или** очередь 5 §8 leadgen+голос **или** full live gate.

**Quality gates (фон):** full live gate 🔲 — `GATE_FULL_RUNBOOK.md`.

---

`Спринт:[Ф1→Ф2] | Задача:[agents quality gates — хвост] | Статус: шаг 7 ✅ · live gate 🟡`

**Шаг 7 (2026-06-13):** pytest gate **34 passed**; live LLM не в CI; cp1251 fix в CLI.

**Live gate:** smoke ✅ `agents_gate_20260613_143114.json`; full — см. `gate_full_20260613.log`.

**Quality gates:** [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](../phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md) · [`AGENTS_LEARNING_MAP.md`](../phase2/agents/AGENTS_LEARNING_MAP.md).

**Процесс:** `git commit` + ops — [`smartcrm-commit-ops.mdc`](../../.cursor/rules/smartcrm-commit-ops.mdc). **`git push`** — только по явному go.

**Хвост Фазы 1 = только `BACKLOG.md`.** В `PRD_MAP.md` § «Открытые хвосты Ф1» — указатель; Hermes + voice_action **не** в хвосте (закрыты в таблице «Голос → лиды»).

**Фаза 1:** ✅ DoD 6/6 — `VOICE_MIC_E2E_ACCEPTANCE.md`.

**Фаза 2:** очередь **5** §8 leadgen+голос — smoke WS; дальше live UI + полный pipeline.

**Порядок Ф2:** [`PRD_MAP.md` § Порядок Фазы 2](../product/PRD_MAP.md#порядок-фазы-2) — `go` только по номеру очереди.

**MAP-doc:** **закрыт** (2026-06-11) — PRD синхрон (Ф1 ✅, навигация); MAP: DoD Ф2, сценарии Ф2, TOC, `LEADGEN_VOICE_ACCEPTANCE.md`, сводка «✅ (хвосты 🟡)».

**Тендеры Ф1:** Serper/Tavily, Мои/Архив БД, LLM analyze, Gosplan UI — `2acf0da`+.

**Аналитика Ф1 ✅** — `ANALYTICS_BASELINE_ACCEPTANCE.md`.

**Ops Ф1 ✅** — `OPS_BASELINE_ACCEPTANCE.md`, `smoke_ops_baseline.py` (33 pytest).

**Email ✅** — `EMAIL_CONNECT_ACCEPTANCE.md`: ib@ + me@ в `.env`; UI `/email`; фоновый sync Ф2.

**Следующий `go` (история):** Ф2 §3 email-агент п.405+ или §8 leadgen.

**RAG п.5 save ✅** — `smoke_rag_save_from_search.py`, DevTools полный flow, `SEARCH_RAG_SAVE_ACCEPTANCE.md`.

**п.4 ✅** `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`. **п.3 ✅** `SEARCH_CHROMA_ACCEPTANCE.md`. **п.2 ✅** `SEARCH_MODES_ACCEPTANCE.md`. **п.1 ✅** `SEARCH_PROVIDERS_ACCEPTANCE.md`.

**enrich-lead ✅** — `SEARCH_ENRICH_LEAD_ACCEPTANCE.md`. **Ф2 ближайшее (enrich):** кэш enrich §4, кнопка на карточке §9 — `PRD_MAP.md`. **Хвост:** авто-чанки → `BACKLOG.md`.

**Активный хвост (топ):** см. `BACKLOG.md` § [Активный хвост](../operations/session/BACKLOG.md) — не дублировать здесь.

**Код/автотесты закрыты** — коммит `352eed2`, acceptance `VOICE_LEADS_TAIL_ACCEPTANCE.md`.

**Хвост #2–#11 ✅** — `VOICE_LEADS_TAIL_ACCEPTANCE.md` (add_communication, fuzzy stage, чипы, fanout UI, eval, whisper health, email validators).

**Блок «Голос → лиды» п.1–5 ✅** — `smoke_voice_lead_scenarios.py`, матрица `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md`, DevTools partial.

**Полные интенты лидов ✅** — `smoke_hermes_leads_full.py`, `HERMES_LEADS_FULL_ACCEPTANCE.md`.

**voice_action UI ✅** — modal/navigate/filter/approve, `smoke_voice_action.py`, `VOICE_ACTION_ACCEPTANCE.md`.

**Hermes интенты по лидам ✅** — `smoke_hermes_leads.py` 40 pytest, `HERMES_LEADS_ACCEPTANCE.md`.

**Whisper STT перепроход ✅** — `smoke_whisper_stt.py`, `WHISPER_STT_ACCEPTANCE.md`.

**Блок «Балльная воронка» закрыт.** Смоук формулы + приоритеты 2026-06-08 (`SCORING_FUNNEL_ACCEPTANCE.md`).

**Блок «Лиды» закрыт ранее.** Перепроход п.1–12 + acceptance (`LEADS_BLOCK_ACCEPTANCE.md`).

## Прогоны (все зелёные)

| Проверка | Результат |
|----------|-----------|
| `python scripts/smoke_leads_block.py` | **81 pytest PASS** + **14 HTTP frontend PASS** (`localhost:5174`) |
| `python scripts/run_zone_regression.py crm_leads` | PASS |
| DevTools UI | list, funnel, calendar, **tasks (после фикса)**, focus, analytics, card, /crm redirects |

Детали: `docs/operations/phase1/leads/LEADS_BLOCK_ACCEPTANCE.md`

## Фикс в этом шаге

- `/leads/tasks` — shadow `createTask` → `submitTaskForm` / `apiCreateTask` (ISSUES закрыт)

## Прогон балльной воронки

`cd backend && python scripts/smoke_scoring_funnel.py` — **21 pytest PASS**

## Следующий шаг (после апрува)

Следующий фокус: **Фаза 2** (голос вне лидов) или **Битрикс синк** (BACKLOG 🟡).

**Блокеры:** нет 🔴

---
