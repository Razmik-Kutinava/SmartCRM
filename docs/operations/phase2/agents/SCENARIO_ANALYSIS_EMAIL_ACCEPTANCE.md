# Сценарий analysis+email — acceptance (Ф2 §2 п.393)

**PRD_MAP:** «Сценарий: анализ + письмо»

## Было

- Фраза «проанализируй лид и напиши письмо» попадала в `analyze_lead` (4 агента) или `write_email` (только маркетолог)
- Нет именованного сценария Аналитик ∥ Маркетолог → Стратег
- `first_email` маркетолога не попадал в `draft_email` модалки

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `agents/scenarios/analysis_email.py` | intent `analyze_and_email`, AGENTS analyst+marketer |
| `supervisor.py` | fanout 2 + strategist |
| `rescue.py` | CPU-маршрут до generic analyze_lead |
| `module_contract.py` | module agents, ui modal |
| `analyst` / `marketer` | поддержка intent |
| `voice_action.py` | modal + synthesis + `first_email` → draft |
| `pipeline.py` | fix `agents` до run_agents |

## Критерии

- [x] «проанализируй … и напиши письмо» → `analyze_and_email`, parallel, modal
- [x] Supervisor: analyst + marketer, strategist=true
- [x] Modal: analysis + draft_email + send/save/reject
- [x] pytest `tests/agents/scenarios/test_analysis_email.py`

## Не в scope

- п.394–396 (тендер, отчёт, похожие клиенты)
- live LLM прогон
