# HANDOFF

Передача между сессиями: статус задачи, следующий шаг, блокеры.

`Спринт:[N] | Задача:[название] | Статус:[в работе/завершено/заблокировано]`  
`Следующий шаг:[что делать]`  
`Блокеры:[список или "нет"]`  
`Последние коммиты:[3 последних]`  
`Открытые вопросы:[список или "нет"]`

Спринт:[Фаза 1] | Задача:[Проход PRD_MAP + порядок в репо] | Статус:в работе

Следующий шаг: **P6 остаток** (`pipeline.py` / `rag/search.py` / `tenders.py` — по одному `go`) или **Фаза 1 PRD_MAP**. P6: `leads/`, `hermes/`, `ops/` done; P1–P5 layout — done.

Блокеры: нет

Последние коммиты (на ветке, последние известные):
- 46d634f refactor: P6 split api/routes/leads into package
- 1d02403 docs: P5 migrate flat docs to nested structure
- 9b45686 refactor: P4 move email integration test to tests/integration
- 9c6ef13 chore: P3 remove backend/backend/data nesting
- 7432d2b chore: P2 clean repo root, openapi in docs/api, artifact gitignore
- 2e0cd60 refactor: move root tests/ to backend/tests/ (P1 layout)
- 637941c chore: repo layout rules, code split limits, structure audit
- a619ee8 docs: update HANDOFF with v3 delta commit hash
- 67150fc docs: integrate PRD tech delta v3

Открытые вопросы: какой пакет аудита апрувить первым (P1 тесты / P2 мусор в корне / P6 сплит кода).

---
