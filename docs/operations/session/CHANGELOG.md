# CHANGELOG (операционный)

**Роль:** источник правды по истории — что сделано, когда, почему и при каким `go`.

## 2026-07-21 — Чистка git status: runtime-данные вне git

По `go` пользователя («устрани всё»): runtime-файлы `backend/data/` (api_stats, traces, checko_cache, ops_queue, ops_snapshots, agent_memory.sqlite3, hermes_system_prompt.txt, prompt_versions/, *_state/*_notifications/логи) добавлены в `.gitignore` и убраны из индекса (`git rm --cached`, файлы на диске целы). `eval_benchmark_data.py` перенесён из корня `backend/` в `backend/scripts/` (импорты в двух скриптах работают без правок — проверено). `.pytest_cache` в корне репо удалён (pytest гонять из `backend/`). `__pycache__` и `frontend/.svelte-kit` уже ловились правилами (`git check-ignore` подтвердил) — в статусе их больше нет. README backend/scripts обновлены. Тесты: `pytest tests/scripts/ -q` — 12 passed. Архивация толстых ops-файлов → BACKLOG. Коммит `7a57856`.

## 2026-07-18 — Ф4: кнопка «+ Добавить ящик» в сайдбаре почты

Под селектом «Все ящики» — явная кнопка добавления ящика (открывает модал подключения). Проверено в браузере через DevTools MCP: оба ящика (`me@agneko.am`, `ib@agneko.com`) видны.

## 2026-07-18 — Ф4: управление почтовыми ящиками (отключение)

`DELETE /api/email/accounts/{id}` + `services/email_account_delete.py` (purge переписки/кампаний/цепочек); UI — кнопка «Отключить» у каждого аккаунта в модалке `/email`.

## 2026-07-18 — `.claude/` в gitignore

Папка Claude Code (agents, commands) убрана из git (`git rm --cached`), файлы на диске остались. `.gitignore`: `.claude/` вместо `.claude/settings.local.json` — секреты локальных настроек больше не попадут в git.

## 2026-07-18 — CoffeeOS workflow: шаг 6 + закрытие миграции

SBR scope зафиксирован: PRD_MAP + фичи/API/миграции; one-liner без SBR.  
RULES_MATRIX § SBR scope; BACKLOG post-migration долги.

## 2026-07-18 — CoffeeOS workflow: шаг 5 (doc links + scratch)

Ссылки на rules → `.cursor/rules/workflow/` в PRD_MAP, PHASE2_ENTRY, docs/README, archive, debt.  
`backend/scripts/scratch/` + README; repo-layout, scripts/README.

## 2026-07-18 — CoffeeOS workflow: шаг 4 (merged отчёт)

Таблица **Сделано | Не сделано** + A/B/C в task-workflow, commit-ops, agent-workflow, spec-build-review, AGENTS, RULES_MATRIX.  
A = колонка «Не сделано»; RED-substep — без полного отчёта.

## 2026-07-18 — CoffeeOS workflow: шаг 3 (project-rules)

6 файлов в `.cursor/rules/project/`: core, tests, http, data, agents, performance.  
Globs по зонам; performance — alwaysApply. Обновлены index, `.cursorrules`, RULES_MATRIX, spec-build-review, BACKLOG.

## 2026-07-18 — CoffeeOS workflow: шаг 2 (SBR)

`workflow/spec-build-review.mdc` — PHASE 1 SPEC / RED / GREEN / REVIEW.  
`docs/operations/session/todo.md` — микро-чеклист фичи.  
RED/GREEN substeps в `commit-ops.mdc`; SBR в `task-workflow`, `dev-gates`, index, `.cursorrules`.  
Scope SBR по умолчанию: PRD_MAP + фичи; one-liner — без SBR.

## 2026-07-18 — CoffeeOS workflow: шаг 1 (каркас + перенос)

`.cursor/rules/workflow/` — 6 правил (commit-ops, task-workflow, agent-workflow, dev-gates, repo-layout, file-size-split).  
`smartcrm-index.mdc`, `project/README.md` (placeholder).  
Обновлены: `AGENTS.md`, `.cursorrules`, `RULES_MATRIX.md`, `verify_cursor_rules_precedence.py`, CONTRIBUTING, REPO_LAYOUT, LAYOUT_AUDIT.  
BACKLOG: шаги 2–6 (SBR, project-rules, отчёт, doc links, scratch).

> Архив: `docs/archive/ops/` (секции по месяцам).
