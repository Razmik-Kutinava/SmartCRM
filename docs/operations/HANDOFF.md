# HANDOFF

`Спринт:[Фаза 1] | Задача:[Голос → лиды, п.2 Hermes] | Статус:DONE — ждём апрув`

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

Голос → лиды: **п.3 voice_action UI** или **полный набор интентов** (история/аналитика).

**Блокеры:** нет 🔴

---
