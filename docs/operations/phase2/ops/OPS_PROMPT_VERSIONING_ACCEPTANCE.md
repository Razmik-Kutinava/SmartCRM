# Ops: версионирование промптов (Ф2 §5)

**PRD_MAP:** §5 Self-improvement — п.1–3 (версии, откат, сравнение)

## Было

- Агенты: один override `agent_prompt_{id}.txt` без истории
- Hermes: один override `hermes_system_prompt.txt` без истории
- Откат только «сброс к встроенному»
- Нет diff между версиями
- Роут `compare` конфликтовал с `{version_id}` → 404

## Стало

| Область | Поведение |
|---------|-----------|
| Store | `agent_prompt_versions.py` — `data/prompt_versions/{agent\|hermes}/` |
| Агенты `/ops/agents` | PUT → версия; list/restore/compare API; `PromptVersionPanel` |
| Hermes `/ops/intents/improve` | POST/DELETE/bulk/add-example → версии; те же API; `PromptVersionPanel` |
| Compare | Статический роут **до** `{version_id}` (агенты + Hermes) |
| UI | `promptBasePath` — общая панель на обеих страницах |

## API

**Агенты:** `/api/ops/agents/{id}/prompt/versions[...]`

**Hermes:** `/api/ops/hermes/prompt/versions[...]`

Compare: `?left=current|builtin|v000001&right=...`

## Команды

```bash
cd backend
python -m pytest tests/core/test_agent_prompt_versions.py tests/api/test_ops_baseline_api.py -q --override-ini="filterwarnings="
```

## Критерии

- [x] Версионирование агентов + Hermes
- [x] Откат на предыдущую версию (оба UI)
- [x] Сравнение версий (unified diff)
- [x] pytest agents + hermes API

## Не в scope §5

- A/B прогон промптов — Ф3
