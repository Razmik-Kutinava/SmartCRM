# Eval-кейсы продуктовых агентов

По одному JSONL на агента (≥15 кейсов). Hermes — `eval/cases.jsonl` (≥30).

## Поля кейса

| Поле | Описание |
|------|----------|
| `id` | Уникальный id (`analyst-001`) |
| `agent` | `analyst` \| `economist` \| `marketer` \| `strategist` \| `tech_specialist` |
| `intent` | Интент Hermes для входа в агента |
| `slots` | Слоты лида / контекста |
| `must_contain` | Подстроки в ответе (no-hallucination + ключевые фразы) |
| `must_not_contain` | Запрещённые фразы (галлюцинации, отказ модели) |
| `state_overrides` | Опционально: mock `analyst_output` и др. для стратега |
| `notes` | Комментарий для людей |

Регенерация из сида: `cd backend && python scripts/seed_agent_eval_cases.py`
