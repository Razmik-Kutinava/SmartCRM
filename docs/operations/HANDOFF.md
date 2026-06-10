# HANDOFF

`Спринт:[Фаза 1] | Задача:[Лидогенерация] | Статус:автосейв (direct+portrait+cluster) + dedup ✅ — `LEADGEN_AUTOSAVE_ACCEPTANCE.md``

**Процесс:** `git commit` + ops **до** ответа агента — канон [`smartcrm-commit-ops.mdc`](../../.cursor/rules/smartcrm-commit-ops.mdc). **`git push`** — только по явному go. Последний коммит: `5ef5b3f`.

**Следующий MAP:** голосовые команды лидогена → Фаза 2 (`PRD_MAP.md`).

**RAG п.5 save ✅** — `smoke_rag_save_from_search.py`, DevTools полный flow, `SEARCH_RAG_SAVE_ACCEPTANCE.md`.

**п.4 ✅** `SEARCH_RAG_UPLOAD_ACCEPTANCE.md`. **п.3 ✅** `SEARCH_CHROMA_ACCEPTANCE.md`. **п.2 ✅** `SEARCH_MODES_ACCEPTANCE.md`. **п.1 ✅** `SEARCH_PROVIDERS_ACCEPTANCE.md`.

**enrich-lead ✅** — `SEARCH_ENRICH_LEAD_ACCEPTANCE.md`. **Ф2 ближайшее (enrich):** кэш enrich §4, кнопка на карточке §9 — `PRD_MAP.md`. **Хвост:** авто-чанки → `BACKLOG.md`.

**Голос → лиды** — микрофон E2E на пользователе (`BACKLOG.md` § ручная работа).

**Чеклист ручной работы → `BACKLOG.md` § «👤 Ручная работа (только ты)».**

| Приоритет | Фаза | Блок | Пункт | Действие |
|-----------|------|------|-------|----------|
| 🔴 | 1 | Голос → лиды | п.1 | Микрофон E2E → `WHISPER_STT_ACCEPTANCE.md` |
| 🟡 | 1 | Голос → лиды | п.3, п.5 | Spot-check approve (S04) + fanout (S02/S06) |
| 🟡 | 2 | Лиды | п.2 Битрикс | Туннель :8000 + вебхук (когда дойдёшь) |

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
