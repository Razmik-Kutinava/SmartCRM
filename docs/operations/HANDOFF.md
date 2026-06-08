# HANDOFF

Передача между сессиями: статус задачи, следующий шаг, блокеры.

`Спринт:[N] | Задача:[название] | Статус:[в работе/завершено/заблокировано]`  
`Следующий шаг:[что делать]`  
`Блокеры:[список или "нет"]`  
`Последние коммиты:[3 последних]`  
`Открытые вопросы:[список или "нет"]`

Спринт:[Фаза 1] | Задача:[Проход PRD_MAP] | Статус:в работе

Следующий шаг: **Фаза 1 PRD_MAP** — явный пункт + `go`. Процесс: `smartcrm-task-workflow.mdc` (старт сессии, honest report, стоп после шага) + **всегда** коммит+ops + `run_zone_regression.py` по зоне.

Блокеры: `tests/core/test_hermes_eval.py` — 9 failed без LLM/Ollama (см. ISSUES при необходимости)

Последние коммиты:
- (ожидается) docs: rules cleanup PRD Factory, always commit+ops, zone regression
- 9e40e19 docs: add smartcrm-dev-gates
- 1815598 docs: BACKLOG + PRD_MAP backlog rule

Открытые вопросы:
- Вставить `CURSOR_USER_RULES_SNIPPET.md` в Cursor Settings → User Rules (вручную)
- Push `main` — только по апруву

---
