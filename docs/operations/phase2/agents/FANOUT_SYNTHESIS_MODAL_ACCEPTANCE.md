# Fanout synthesis → modal — acceptance (Ф2 §2 п.3)

**PRD_MAP:** «Синтез в один ответ → модалка»

## Было

- Стратег синтезировал `final_reply`, но `create_lead` / `update_lead` / `run_analysis` уходили в `navigate`
- В `voice_action.payload` не было блока `synthesis` (decision, next_action, coach_tip)
- Модалка показывала секции агентов по отдельности без единого «Решение»

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `voice/synthesis.py` | `has_multi_agent_synthesis`, `build_synthesis_payload` |
| `voice/voice_action.py` | fanout+strategist → `ui: modal`, payload.synthesis, route на лид |
| `VoiceActionHost.svelte` | блок «Решение» + badges agents_used |
| Тесты | `tests/voice/test_synthesis.py` |

## Критерии

- [x] После fanout 2+ и стратега — `voice_action.ui === modal`
- [x] `payload.synthesis` с decision / next_action / priority / coach_tip
- [x] Одиночный агент create_lead — по-прежнему navigate (без регрессии S02)
- [x] pytest зелёный

## Не в scope

- п.393–396 именованные сценарии
- live LLM eval стратега

## Коммит

См. CHANGELOG текущего шага.
