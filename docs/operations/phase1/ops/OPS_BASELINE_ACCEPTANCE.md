# Ops baseline — acceptance (2026-06-11)

PRD_MAP: **«Ops `/ops`»** · Ф1 baseline **закрыт** (версионирование промптов → Ф2).

## Команда

```bash
cd backend && python scripts/smoke_ops_baseline.py
```

## Источник данных (без UI-моков)

| Вкладка | API | Мок? |
|---------|-----|------|
| Обзор | `GET /api/ops/overview` | Нет — трейсы, LLM health, очередь |
| Интенты | `/api/ops/traces`, `hermes/*`, `scenarios`, `history` | Нет |
| Голос | `GET/PUT /api/ops/voice/whisper` | Нет |
| Агенты | `GET/PUT/DELETE /api/ops/agents/{id}/prompt` | Нет — builtin + override в `data/` |
| Поиск | `/api/search/config`, `providers`, `run` | Нет |
| Очередь | `GET /api/ops/queue` | Нет — `ops_store` |
| Статистика | `GET /api/ops/stats` | Нет — `traces` |
| Инсайты | `GET /api/ops/insights` | Нет |
| API лимиты | `GET /api/usage/stats`, `live` | Нет |
| Логи | `GET/DELETE /api/ops/logs` | Нет — буфер логов |
| CRM | `GET/PUT /api/ops/crm-settings` | Нет — `crm_settings.json` |
| Промпты Hermes | `GET/POST/DELETE /api/ops/hermes/prompt` | Нет |

Доп. вкладка **«Агенты почты»** (`/ops/email-agents`) — `/api/agents/email-*`, вне строк MAP, но реальный API.

## Закрыто

| # | Пункт | Проверка |
|---|--------|----------|
| 1 | Обзор + очередь | overview, queue, snapshot/recompute |
| 2 | Интенты | traces, improve, import, eval, scenarios, history |
| 3 | Голос | whisper settings |
| 4 | Агенты + промпты | 5 агентов, PUT/DELETE prompt roundtrip |
| 5 | Поиск Ops | search config/providers |
| 6 | Статистика / инсайты | stats, insights |
| 7 | API лимиты | usage/stats |
| 8 | Логи | ops/logs |
| 9 | CRM-конфиг | crm-settings GET/PUT |

## DevTools (2026-06-11)

- `/ops` — h1 «Ops / Качество», пайплайн, очередь
- `/ops/agents` — 5 агентов, UI промпта

## Не в scope Ф1

| Пункт | Куда |
|-------|------|
| Версионирование промптов | Фаза 2 (`PRD_MAP` п.207) |
