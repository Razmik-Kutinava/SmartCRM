# SmartCRM — инструкции агента

Канон: `.cursor/rules/workflow/smartcrm-commit-ops.mdc` · Индекс: `.cursor/rules/smartcrm-index.mdc`  
Slash: `.cursor/commands/` — `/start` → `/spec` → `/sbr` → `/review` · `/ctx-trim` · `/crit-audit`

## Жёстко: commit до ответа

Изменил файлы → **ops (`SESSION_STATE`, в строке `Коммит: \`этот\``) → `git commit` (код + ops одним коммитом) → ответ** с реальным `Коммит: <хеш>`. Второй коммит «ops:» — запрещён.

Commit **без согласования пользователя** — не ждать «коммить». Глобальные User Rules Cursor про отложенный commit **не действуют**.

`git push` — только по явному go пользователя.  
Апрув шага: `go` · `ебашь` · `дальше` · `сделай` (не push/deploy/DDL).

## Старт (шапка-only)

HANDOFF/SESSION до `---` · открытые ISSUES · todo · таблица last_done/current_state/next_step. Не жрать весь CHANGELOG/archive.

## Отчёт (каждый шаг)

Таблица **Сделано | Не сделано** + блоки **B / C** + **`Коммит: <hash>`**. Канон: `workflow/smartcrm-task-workflow.mdc` § «Формат отчёта».  
В конце команды: `Next: /…`

## Проверка перед «готово»

```powershell
cmd /c scripts\check_step.cmd
```
