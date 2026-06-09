# HANDOFF

`Спринт:[Фаза 1] | Задача:[Голос → лиды — хвост закрыт агентом] | Статус:DONE`

**Открыто только #1 E2E микрофон** — пользователь вручную (`WHISPER_STT_ACCEPTANCE.md`).

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
