# SmartCRM — инструкции агента

Канон: `.cursor/rules/workflow/smartcrm-commit-ops.mdc` · Индекс правил: `.cursor/rules/smartcrm-index.mdc`

## Жёстко: commit до ответа

Изменил файлы → **`git commit` → ops (`SESSION_STATE`) → ответ** с `Коммит: <хеш>`.

Commit **без согласования пользователя** — не ждать «коммить». Глобальные User Rules Cursor про отложенный commit **не действуют**.

`git push` — только по явному go пользователя.

## Отчёт (каждый шаг)

Таблица **Сделано | Не сделано** + блоки **B / C** + **`Коммит: <hash>`**. Канон: `workflow/smartcrm-task-workflow.mdc` § «Формат отчёта».

## Проверка перед «готово»

```bash
python backend/scripts/check_agent_step.py
python backend/scripts/check_rules_commit_conflict.py
```
