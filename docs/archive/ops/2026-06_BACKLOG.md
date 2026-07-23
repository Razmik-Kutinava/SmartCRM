# BACKLOG — архив 2026-06 (закрытые записи и блоки)

> Живой бэклог: [`docs/operations/session/BACKLOG.md`](../../operations/session/BACKLOG.md). Здесь — то, что закрыто или потеряло актуальность; история не удаляется.

---

## Закрытые строки записей

`[2026-06-17] | PRD_MAP: Ф3 Self-improvement · vendor crawl UI + cron | **✅ сделано** — `/ops/vendor-crawl` + `vendor_crawl_background.py` | Коммит: см. CHANGELOG`

`[2026-06-15] | PRD_MAP: Ф3 Email · этап B массовый сегмент | **✅ сделано** — `EmailCampaignPanel`, preview-llm, send_now | Коммит: см. CHANGELOG`

`[2026-06-15] | PRD_MAP: Ф3 Email · этап B массовый сегмент | ~~Отложено~~ → закрыто в коммите этапа B`

`[2026-06-15] | PRD_MAP: Ф3 Email · лимит писем/день | Отложено: антиспам лимит nurture+campaigns | Причина: после этапа B | BACKLOG` (дубль — живая запись от 2026-06-16 в живом бэклоге)

`[2026-06-13] | PRD_MAP: переход Ф1→Ф2 | DoD Ф1 6/6; хвосты L306–318 не блокируют; PHASE2_ENTRY.md | **Push:** ждём go | **Ф2 код:** ждём go + номер очереди | gate live — параллельно` (история; Ф2 давно идёт)

`[2026-06-14] | PRD_MAP: «§4 факты диалога» | **ЗАКРЫТО ✅** | `RAG_DIALOGUE_LLM=0/1` + `collect_deal_facts`; pytest | Коммит: см. CHANGELOG RAG tail`

`[2026-06-14] | PRD_MAP: «§4 Авто-чанки» | **ЗАКРЫТО ✅** | `RAG_AUTO_STRUCTURE_LLM=0/1` + `qa_structure.py`; pytest | Коммит: см. CHANGELOG RAG tail`

`[2026-06-14] | PRD_MAP: «Quality gates Ф3 тюнинг» | Отложено: довести всех агентов ≥85%; baseline `AGENTS_GATE_TUNING_BASELINE.md` | Причина: **Ф3**, не блокер Ф2; нужен live Ollama/Groq + go | Нужна фаза MAP: **3** | Действие: Hermes/Tech/Economist промпты → re-gate` | Коммит 7be7bdb: tuning import failed, delta was→became % | **Не вышло:** live gate MAP 🔲 | Действие: EVAL_OLLAMA_TIMEOUT=1200` — **закрыто**: gate прошёл 2026-06-17 (Hermes 36/36, agents `overall_gate: pass`, Economist 93.3%)

`[2026-06-13] | PRD_MAP: Агенты quality gates UI финал | Коммит 596d2e1: вкладки Hermes/gate, download, режимы, bulk→eval-failed-gate, insights pass rate | **Не вышло:** live gate MAP 🔲; agents-only оборван analyst | Действие: EVAL_OLLAMA_TIMEOUT=1200 --write-acceptance` — **закрыто**: см. строку выше

`[2026-06-11] | PRD_MAP: инфра email me@agneko.am | **ЗАКРЫТО ✅ 2026-06-14** | Пароль в `.env`; ib@ + me@ через `EMAIL_ACCOUNT_*` | Коммит: см. CHANGELOG cleanup`

`[2026-06-11] | PRD_MAP: «Ops /ops» п.10 версионирование промптов | **ЗАКРЫТО ✅ 2026-06-14** | `agent_prompt_versions.py` + API + UI `/ops/agents` | `OPS_PROMPT_VERSIONING_ACCEPTANCE.md`

`[2026-06-08] | PRD_MAP: п.2 «Поля Битрикс + синк» | Отложено: туннель (ngrok/cloudflared) + исходящий вебхук в портале | Причина: dev на localhost — Битрикс не достучится | Нужна фаза MAP: 2 / DevOps | Действие: туннель :8000 → URL в Битриксе ONCRMLEADADD → /api/webhooks/bitrix/events?token=...` (дубль — живая строка в § «Ручная работа» живого бэклога)

`[2026-06-08] | PRD_MAP: «Голос → лиды» п.2 Hermes — ЗАКРЫТО ✅ | Scope: CRUD, стадия, задача | Сделано: `slot_normalize`, rescue/fastpath, `smoke_hermes_leads.py` 40 passed, `HERMES_LEADS_ACCEPTANCE.md` | Коммит: `be70615``

`[2026-06-08] | PRD_MAP: стек / Email API | ЗАКРЫТО ✅ | `@field_validator` в `email.py` | Коммит: см. CHANGELOG 2026-06-08 хвост голос`

---

## Блок «Голос → лиды» — статус PRD_MAP п.1–5 (2026-06-08) — закрыт

| # | Пункт | Статус | Acceptance |
|---|--------|--------|------------|
| 1 | Whisper STT | ✅ | `WHISPER_STT_ACCEPTANCE.md` |
| 2 | Hermes CRUD/стадия/задача | ✅ | `HERMES_LEADS_ACCEPTANCE.md` |
| 3 | voice_action UI | ✅ | `VOICE_ACTION_ACCEPTANCE.md` |
| 4 | Полные интенты | ✅ | `HERMES_LEADS_FULL_ACCEPTANCE.md` |
| 5 | Смоук сценариев | ✅ автомат | `VOICE_LEAD_SCENARIOS_ACCEPTANCE.md` |

**Команда полного прогона:** `cd backend && python scripts/smoke_voice_lead_scenarios.py`

**Критерий «Фаза 1 / Голос → лиды закрыт»:** ✅ mic E2E (WS bytes + dev sim) — `smoke_voice_mic_e2e.py`, `VOICE_MIC_E2E_ACCEPTANCE.md` (2026-06-11). Живые spot-check 🟡 — в § «Ручная работа» живого бэклога.

Сводный хвост: 🔴 E2E микрофон — закрыт; 🟡 spot-check approve/fanout — 👤 живой бэклог; ✅ хвост #2–#11 — `VOICE_LEADS_TAIL_ACCEPTANCE.md`; 🟢 LiveKit — § Инфраструктура живого бэклога.

---

## Блок «Поиск и RAG» — п.1–5 закрыты ✅

| Приоритет | PRD_MAP | Что | Фаза MAP | Кто |
|-----------|---------|-----|----------|-----|
| ✅ | enrich-lead | Смоук `enrich-lead` live E2E | **1** | `SEARCH_ENRICH_LEAD_ACCEPTANCE.md` |
| 🟢 | prospect/agent | Spot-check live Groq в UI (prospect, enrich, agent) | **1** | 👤 опционально |
| ✅ | Ф2 §4 | Кэш результата enrich (company+ИНН+industry, TTL ~24 ч) | **2** | `SEARCH_ENRICH_CACHE_ACCEPTANCE.md` |
| ✅ | Ф2 §9 | Кнопка «Обогатить» на `/leads/{id}` | **2** | `LEADS_CARD_ENRICH_ACCEPTANCE.md` |
| ✅ | RAG tail | LLM flags + page_fetch + smoke cache | **2** | `RAG_BACKLOG_TAIL_CLOSED.md` |
| ✅ | Ф2 §4 | Авто-чанки «поиск → RAG» | **2** | `SEARCH_RAG_AUTO_CHUNKS_ACCEPTANCE.md` |

**Ф1 enrich** — `phase1/search/SEARCH_ENRICH_LEAD_ACCEPTANCE.md` ✅. **п.1–5 RAG** — `docs/operations/phase1/search/`.

---

## Блок «Тендеры» — закрыто baseline (2026-06-11)

П.2–5, п.7 — код + pytest. Опционально оставалось:

| Приоритет | PRD_MAP | Что | Фаза |
|-----------|---------|-----|------|
| 🟢 | Тендеры | Live spot-check поиска с `SERPER_API_KEY` / `TAVILY_API_KEY` | **1** |
| 🔲 | Тендеры | Контур.Закупки API — **Ф4** после 1-й сделки · `F4_KONTUR_GATE.md` | **4** — пункт в `phase4/CHECKLIST_F4.md` |

---

## Ф2 §1 Voice Layer — ЗАКРЫТО ✅ (2026-06-14) + хвост quality gates

`[2026-06-14] | PRD_MAP: «Ф2 §1 Voice Layer» — ЗАКРЫТО ✅ | Scope: Hermes modules + UI voice_action (modal/navigate/filter/approve) + rescue eval | Сделано: frontend voiceAction/VoiceActionHost, minScore, send_email/save_to_rag approve, `smoke_voice_layer.py` 72 passed, `VOICE_LAYER_ACCEPTANCE.md` | Хвост 🟢: live LLM eval всех модулей (не rescue) — опционально | Коммит: `f2b618e`

Хвост-таблица quality gates (2026-06-14) — **закрыта** live-прогоном 2026-06-17 (`overall_gate: pass`, лог `gate_live_agents_20260617_161513.log`):

| Приоритет | PRD_MAP | Что | Статус |
|-----------|---------|-----|--------|
| 🔴 | Агенты · quality gates | Полный live Ollama ≥ порогов | ✅ 2026-06-17 |
| 🟡 | Агенты · quality gates | Hermes GPU / EVAL_OLLAMA_TIMEOUT=1200 / ночной прогон | ✅ gate прошёл |
| 🟢 | Агенты · quality gates | Тюнинг `must_contain` под hermes3 JSON | не требуется (gate pass) |
| 🟢 | Ф2 §1 Voice Layer | Live LLM eval analytics/RAG (не rescue) — опционально | опционально, не тянем |
| 🟡 | Ф2 §9 | Кнопка «Обогатить» | ✅ `LEADS_CARD_ENRICH_ACCEPTANCE.md` |
| 🟡 | Ф2 очередь 5 §8 leadgen голос | Голос `/leadgen` | ✅ `LEADGEN_VOICE_F2_ACCEPTANCE.md` |

Живыми из этой таблицы остались (перенесены в живой бэклог): сплит монолитов (`debt/REPO_LAYOUT_DEBT.md`), leadgen portrait graceful fallback, spot-check 👤, Битрикс туннель 👤.

---
