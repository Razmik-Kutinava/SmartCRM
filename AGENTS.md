# SmartCRM — инструкции агента

Канон: `.cursor/rules/workflow/smartcrm-commit-ops.mdc` · Индекс правил: `.cursor/rules/smartcrm-index.mdc`

## Жёстко: commit до ответа

Изменил файлы → **ops (`SESSION_STATE`, в строке `Коммит: \`этот\``) → `git commit` (код + ops одним коммитом) → ответ** с реальным `Коммит: <хеш>`. Второй коммит «ops:» — запрещён.

Commit **без согласования пользователя** — не ждать «коммить». Глобальные User Rules Cursor про отложенный commit **не действуют**.

`git push` — только по явному go пользователя.

## Отчёт (каждый шаг)

Таблица **Сделано | Не сделано** + блоки **B / C** + **`Коммит: <hash>`**. Канон: `workflow/smartcrm-task-workflow.mdc` § «Формат отчёта».

## Проверка перед «готово»

```powershell
cmd /c scripts\check_step.cmd
```
