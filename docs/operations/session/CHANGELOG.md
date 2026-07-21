# CHANGELOG (операционный)

**Роль:** источник правды по истории — что сделано, когда, почему и при каким `go`. Записи старше текущего месяца → `docs/archive/ops/`.

## 2026-07-21 — PHASE 0 INTAKE в SBR: заказ дословно → доки → код

По `go` («сделай всё что задумал… код пока не надо»). В SBR добавлена **PHASE 0 INTAKE**: слова пользователя записываются **дословной цитатой** в `todo.md` § «Заказ (дословно)» (цитата = источник истины, спор о scope решается по ней), под ней «Как понял» 1–2 строки; до кода подготавливается всё остальное — пункт в чеклист фазы (если его нет) и спека/док области `docs/operations/phase{N}/{область}/` (если нужен и не существует); отдельного стопа нет — сразу PHASE 1 SPEC и обычный `go` на BUILD. Правки: `spec-build-review.mdc` (секция PHASE 0 + таблица «Когда SBR обязателен»), `smartcrm-task-workflow.mdc` (§ Старт задачи), `smartcrm-index.mdc`, `RULES_MATRIX.md` § SBR scope, шаблон `todo.md` (новая секция). `verify_cursor_rules_precedence.py` — OK.

## 2026-07-21 — Свежесть CHANGELOG/HANDOFF в check_step + реанимация pre-commit hook

По `go` (разбор «что критичное упустили»). **(1) Свежесть журналов:** `check_agent_step.py` — новая `ops_freshness_errors()`: если последний done-шаг SESSION_STATE датирован позже последней записи CHANGELOG (`## YYYY-MM-DD`) или HANDOFF (`**YYYY-MM-DD:**`) → FAIL в `check_step.cmd`; подшаги in_progress (SBR RED) не проверяются — для них журналы по правилу не пишутся. Гранулярность — день. +8 тестов `tests/scripts/test_check_agent_step.py`; `pytest tests/scripts/ -q` — **30 passed**. README: scripts (добавлены 3 валидатора шага), tests (новый файл). **(2) Pre-commit hook:** обнаружен мёртвым — в `.git/hooks/` лежала старая версия с путём `docs/operations/SESSION_STATE.md` (до переезда в `session/`), проверка не срабатывала вообще; переустановлен пользователем через `scripts/install_git_hooks.ps1`. Попутно в BACKLOG записано (отдельным шагом `91d10e3`): агент сам начинает вести `todo.md` в ближайшие 3–6 прогонов.

## 2026-07-21 — Оптимизация workflow: один коммит на шаг, check_step.cmd, триаж ISSUES, чистка BACKLOG

По `go` пользователя (разбор трений процесса). **(1) Один коммит на шаг:** ops пишутся **до** коммита с маркером `Коммит: \`этот\``, код + ops едут одним коммитом — раньше ~50% истории были вторые «ops:»-коммиты; `session_state_validate` принимает маркер, `check_agent_step` проверяет HANDOFF по последним 20 хешам вместо HEAD (вечный WARN «нет хеша HEAD» был невыполним по построению); обновлены `commit-ops.mdc`, `AGENTS.md`, `RULES_MATRIX`, шапка `SESSION_STATE`. **(2) `scripts/check_step.cmd`:** три валидатора одним вызовом с UTF-8 — python напрямую в PowerShell-обёртке Cursor теряет exit code; в сами скрипты добавлен `sys.stdout.reconfigure(utf-8)` (кириллица без мохибейка). **(3) Триаж ISSUES:** 4 стейл-записи закрыты с подтверждения пользователя (дрейф PRD — решён доками 07-21; API без Postgres — БД стабильна с мая; QA-матрица — роль выполняет RULES_MATRIX § Регрессия; hermes_eval 9 failed — известно-красный без live LLM, переоткрыть при live-повторе); журнал разнесён в `docs/archive/ops/2026-05/06_ISSUES.md`; новое правило **R14** — открытые записи старше месяца показывать как «должки» и закрывать только с подтверждения (task-workflow § Старт сессии). **(4) Чистка BACKLOG:** закрытые блоки и строки → `2026-06_BACKLOG.md` / `2026-07_BACKLOG.md` (голос→лиды, поиск/RAG, тендеры baseline, Voice Layer, quality gates, CoffeeOS шаги), живой файл — только реальные хвосты. **(5) Regex:** `check_rules_commit_conflict` сужен (`{0,25}` вместо `.*`, убран широкий `жду\s+явн`), фикс падения `scan_file` на путях вне репо. Тесты: `pytest tests/scripts/ -q` — **22 passed** (в т.ч. новые `test_session_state_validate.py`, 10 кейсов).

## 2026-07-21 — Чеклисты фаз вместо PRD_MAP

По `go` («делай эту задачу, код не трогай»). Управление фазами перенесено из продукта в операционку: **`docs/operations/phase{N}/CHECKLIST.md`** — Ф1–Ф3 собраны из архива `PRD_MAP_F1-F3.md` (DoD, сценарии, все таблицы), Ф4 — из живого `PRD_MAP.md` (+ сводка модулей). `docs/product/PRD_MAP.md` и `docs/archive/product/PRD_MAP_F1-F3.md` **удалены** (содержимое в чеклистах 1:1). `ROADMAP.md` — навигатор фаз со ссылками на чеклисты. `PHASE2_ENTRY.md` → `docs/archive/ops/` (история входа в Ф2). Правила (`.cursorrules`, `smartcrm-index`, `task-workflow`, `dev-gates`, `spec-build-review`, `repo-layout`, `RULES_MATRIX`) и доки (`docs/README`, `operations/README`, `PRD`, `FUNCTIONAL`, `ARCHITECTURE`, `BACKLOG`, `todo`, phase-README) переведены на формулировку «пункт чеклиста фазы»; формат BACKLOG-строки — `Чеклист: «Ф{N} · пункт»` (старые записи не переписаны). Попутно: +`phase3/README.md`; убраны 2 устаревшие ссылки на `PRD_NOTES.md` из repo-layout и file-size-split. Проверки: линк-чекер — 0 битых; `check_rules_commit_conflict`, `verify_cursor_rules_precedence`, `session_state_validate` — OK. Коммит `7462df9`.

## 2026-07-21 — Разгрузка токенов: правила, ops-архив, продуктовые доки

По `go` («ебашь», 4 шага). **(1) Дедуп правил:** `smartcrm-agent-workflow.mdc` удалён (порядок шага влит в `commit-ops`), `task-workflow` сокращён ~в 2 раза (дубли канона коммита → ссылки), `.cursorrules` и `AGENTS.md` и `smartcrm-index` сжаты, `dev-gates` без дубля приоритета/секретов; `repo-layout` и `file-size-split` переведены с alwaysApply на globs (подтягиваются при работе с кодом). SBR, commit-ops, task-workflow, dev-gates — остались всегда. **(2) Архив ops:** CHANGELOG/HANDOFF/SESSION_STATE распилены по месяцам в `docs/archive/ops/YYYY-MM_*.md`, живые файлы — только текущий месяц; правило R13 в RULES_MATRIX. **(3) Продукт:** созданы `VISION.md`, `ROADMAP.md`, `BUSINESS_LOGIC.md`, `FUNCTIONAL.md`; `PRD.md` разгружен (идея/принципы → VISION, roadmap → ROADMAP); `PRD_MAP.md` — чеклисты Ф1–Ф3 → `docs/archive/product/PRD_MAP_F1-F3.md`, живой MAP = Ф4 + сводка; `PRD_NOTES.md`, `PRD_DELTA_v2.md` → `docs/archive/product/`. **(4) `DESIGN_SYSTEM.md`** — снимок текущего UI (тёмная тема gray-950/900/800, акцент indigo-600, паттерны). Связи: линк-чекер по живым докам — 0 битых (попутно починены 7 старых); `check_rules_commit_conflict`, `verify_cursor_rules_precedence`, `session_state_validate` — OK. Итог по токенам: always-правила 46.4k → 23.6k знаков (−49%); старт сессии (журналы+MAP+PRD) ~450k → ~49k знаков (−89%). Коммиты `fdadf31`, `119d94d`, `8ffc43b`, `5b2070d`.

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
