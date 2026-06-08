# Блок «Лиды» — acceptance (2026-06-08)

## Команды

```bash
cd backend && python scripts/smoke_leads_block.py
cd backend && python scripts/run_zone_regression.py crm_leads
LEADS_SMOKE_STRICT_FRONTEND=1 python scripts/smoke_leads_block.py   # fail если фронт недоступен
```

**Фронт:** Vite на `http://localhost:5174` (если 5173 занят). Скрипт сам ищет 5174/5173.

## Pytest (авто)

| Пакет | Модулей | Тестов (ориентир) |
|-------|---------|-------------------|
| smoke + acceptance + lib + api + core | 20 | 81+ |

## DevTools UI (ручной прогон 2026-06-08)

| Экран | URL | Маркер | Статус |
|-------|-----|--------|--------|
| Список | `/leads/list` | h1 «Список лидов», GET `/api/leads` 200 | OK |
| Воронка | `/leads/funnel` | h1 «Воронка» | OK |
| Календарь | `/leads/calendar` | h1 «Календарь задач» | OK |
| Задачи | `/leads/tasks` | **был баг** shadow `createTask` → 500 compile | **FIX** `submitTaskForm` |
| Фокус | `/leads/focus` | layout + табы | OK |
| Аналитика | `/leads/analytics` | h1 «Аналитика CRM» | OK |
| Карточка | `/leads/{id}` | Комментарии, Касания, Сменить этап, История | OK |
| CRM редирект | `/crm/list` | → `/leads/list` | OK |
| CRM редирект | `/crm/funnel` | → `/leads/funnel` | OK |

Консоль: единственный шум — `favicon.ico` 404 (не блокер).

## PRD_MAP п.1–12

Все пункты перепрохода отмечены ✅ в `docs/product/PRD_MAP.md`.

## Известные хвосты (не блокер Лиды)

- Битрикс: исходящий вебхук в портале → `BACKLOG.md`
- Pydantic `validation_alias` warnings в pytest (техдолг схем)
