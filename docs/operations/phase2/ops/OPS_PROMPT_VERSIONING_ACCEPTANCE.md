# Ops: версионирование промптов агентов (Ф2 §5)

**PRD_MAP:** §5 Self-improvement — п.1–3 (версии, откат, сравнение)

## Было

- Один файл override `agent_prompt_{id}.txt` — PUT/DELETE без истории
- Откат только «сброс к встроенному»
- Нет diff между версиями

## Стало

| Компонент | Поведение |
|-----------|-----------|
| `agent_prompt_versions.py` | Снимки в `data/prompt_versions/{agent}/` (до 50 версий) |
| PUT `/prompt` | Перед перезаписью — `before_save`, после — `save` |
| GET `/prompt/versions` | Список версий (новые сверху) |
| POST `/prompt/versions/{id}/restore` | Откат к версии |
| GET `/prompt/versions/compare?left=&right=` | Diff (`current`, `builtin`, `v000001`) |
| UI `/ops/agents` | `PromptVersionPanel` — история, откат, сравнение |

## Команды

```bash
cd backend
python -m pytest tests/core/test_agent_prompt_versions.py tests/api/test_ops_baseline_api.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] Версионирование при сохранении
- [x] Откат на предыдущую версию
- [x] Сравнение двух версий (unified diff)
- [x] pytest API + unit

## Не в scope

- Hermes prompt (`/ops/intents/improve`) — отдельный store
- A/B прогон промптов — Ф3
