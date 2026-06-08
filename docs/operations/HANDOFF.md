# HANDOFF

`Спринт:[Фаза 1] | Задача:[блок «Лиды»] | Статус:ACCEPTANCE DONE — ждём апрув`

**Блок «Лиды» готов к закрытию.** Перепроход п.1–12 + финальный acceptance 2026-06-08.

## Прогоны (все зелёные)

| Проверка | Результат |
|----------|-----------|
| `python scripts/smoke_leads_block.py` | **81 pytest PASS** + **14 HTTP frontend PASS** (`localhost:5174`) |
| `python scripts/run_zone_regression.py crm_leads` | PASS |
| DevTools UI | list, funnel, calendar, **tasks (после фикса)**, focus, analytics, card, /crm redirects |

Детали: `docs/operations/LEADS_BLOCK_ACCEPTANCE.md`

## Фикс в этом шаге

- `/leads/tasks` — shadow `createTask` → `submitTaskForm` / `apiCreateTask` (ISSUES закрыт)

## Следующий шаг (после апрува)

Фаза 1 → следующий модуль PRD_MAP: **балльная воронка (смоук формулы)** или **голос → лиды**.

**Блокеры:** нет 🔴

---
