# SmartCRM — инструкции агента

Канон: `.cursor/rules/smartcrm-commit-ops.mdc`

## Жёстко: commit до ответа

Изменил файлы → **`git commit` → ops → ответ** с `Коммит: <хеш>`.

Ответ без коммита при изменённых файлах = шаг не закрыт.

## Хвост A / B / C

В каждом отчёте после работы — три блока (`нет` или список). См. `smartcrm-commit-ops.mdc`.

## Push

Только по явному go пользователя.

## Проверка

```bash
python backend/scripts/check_agent_step.py
python backend/scripts/check_rules_commit_conflict.py
```
