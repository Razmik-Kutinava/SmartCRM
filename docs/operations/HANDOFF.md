# HANDOFF

`Спринт:[Ф1→Ф2] | Задача:[agents quality gates] | Статус:шаг 4 acceptance sync ✅ · live 5 агентов 🔄 · MAP 🔲`

**Quality gates:** [`AGENTS_QUALITY_GATE_ACCEPTANCE.md`](AGENTS_QUALITY_GATE_ACCEPTANCE.md) · обучение [`AGENTS_LEARNING_MAP.md`](AGENTS_LEARNING_MAP.md).  
**Следующий `go`:** дождаться live `--agents-only` → Hermes ночной прогон → шаг 5 UI.

**Процесс:** `git commit` + ops **до** ответа агента — канон [`smartcrm-commit-ops.mdc`](../../.cursor/rules/smartcrm-commit-ops.mdc). **`git push`** — только по явному go.

**Хвост Фазы 1 = только `BACKLOG.md`.** В `PRD_MAP.md` § «Открытые хвосты Ф1» — указатель; Hermes + voice_action **не** в хвосте (закрыты в таблице «Голос → лиды»).

**Фаза 1:** ✅ DoD 6/6 — `VOICE_MIC_E2E_ACCEPTANCE.md`.

**Фаза 2:** очередь **5** §8 leadgen+голос — smoke WS; дальше live UI + полный pipeline.

**Порядок Ф2:** [`PRD_MAP.md` § Порядок Фазы 2](../product/PRD_MAP.md#порядок-фазы-2) — `go` только по номеру очереди.

**MAP-doc:** **закрыт** (2026-06-11) — PRD синхрон (Ф1 ✅, навигация); MAP: DoD Ф2, сценарии Ф2, TOC, `LEADGEN_VOICE_ACCEPTANCE.md`, сводка «✅ (хвосты 🟡)».

**Тендеры Ф1:** Serper/Tavily, Мои/Архив БД, LLM analyze, Gosplan UI — `2acf0da`+.

**Аналитика Ф1 ✅** — `ANALYTICS_BASELINE_ACCEPTANCE.md`.

**Ops Ф1 ✅** — `OPS_BASELINE_ACCEPTANCE.md`, `smoke_ops_baseline.py` (33 pytest).

**Email 🟡** — `EMAIL_CONNECT_ACCEPTANCE.md`: ib@ Yandex ✅; **Sync** на `/email` или `smoke_email_sync.py`; me@ → mail.agneko.am ждёт пароль.

**Следующий `go`:** пароль `me@agneko.am` **или** Агенты (MAP) перепроход **или** Ф2 §8 live leadgen.

**RAG п.5 save ✅** — `smoke_rag_save_from_search.py`, DevTools полный flow, `SEARCH_RAG_SAVE_ACCEPTANCE.md`.

**п.4 ✅** `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`. **п.3 ✅** `SEARCH_CHROMA_ACCEPTANCE.md`. **п.2 ✅** `SEARCH_MODES_ACCEPTANCE.md`. **п.1 ✅** `SEARCH_PROVIDERS_ACCEPTANCE.md`.

**enrich-lead ✅** — `SEARCH_ENRICH_LEAD_ACCEPTANCE.md`. **Ф2 ближайшее (enrich):** кэш enrich §4, кнопка на карточке §9 — `PRD_MAP.md`. **Хвост:** авто-чанки → `BACKLOG.md`.

**Активный хвост (топ):** см. `BACKLOG.md` § [Активный хвост](../operations/BACKLOG.md) — не дублировать здесь.

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

Детали: `docs/operations/LEADS_BLOCK_ACCEPTANCE.md`

## Фикс в этом шаге

- `/leads/tasks` — shadow `createTask` → `submitTaskForm` / `apiCreateTask` (ISSUES закрыт)

## Прогон балльной воронки

`cd backend && python scripts/smoke_scoring_funnel.py` — **21 pytest PASS**

## Следующий шаг (после апрува)

Следующий фокус: **Фаза 2** (голос вне лидов) или **Битрикс синк** (BACKLOG 🟡).

**Блокеры:** нет 🔴

---
