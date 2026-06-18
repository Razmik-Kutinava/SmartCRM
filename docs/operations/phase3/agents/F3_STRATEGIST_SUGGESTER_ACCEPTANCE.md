# Ф3 — Авто-суфлёр Стратега

**PRD_MAP:** Self-improvement → Авто-суфлёр Стратега.

## Критерии

| # | Пункт | Проверка |
|---|-------|----------|
| 1 | Сбор слабых сигналов | 👎 Hermes, 👎 agent_run_log, gate fail |
| 2 | Предложения без автоприменения | Groq + persona Стратега |
| 3 | API suggest + apply | `POST /api/ops/strategist/suggest-prompts`, `apply-suggestion` |
| 4 | UI Ops | `/ops/agents` — блок «Авто-суфлёр Стратега» |
| 5 | Апрув оператора | apply дописывает в промпт + версия |

## Команды

```bash
cd backend
python -m pytest tests/core/test_strategist_suggester.py tests/api/test_strategist_suggester_api.py -q
```

## Поток

1. 👎 на трейсах `/ops/traces` или на ответе агента на карточке лида
2. Провал gate → `/ops/eval` (опционально)
3. `/ops/agents` → **Предложить правки**
4. Оператор **Применить** → промпт обновлён (override + версия)

## Файлы

- `core/strategist_suggester.py`
- `api/routes/ops/strategist_routes.py`

## Не в scope (Ф4)

- Runtime агентов читает override из `agent_prompt_*.txt` (сейчас только Ops-хранилище)
