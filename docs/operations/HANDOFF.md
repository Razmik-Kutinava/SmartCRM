# HANDOFF

`Спринт:[Фаза 1] | Задача:[балльная воронка] | Статус:DONE — ждём апрув`

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

Фаза 1 → **голос → лиды** или **поиск/RAG**.

**Блокеры:** нет 🔴

---
