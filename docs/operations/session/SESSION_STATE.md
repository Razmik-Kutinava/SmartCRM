# SESSION_STATE

Краткий прогресс сессии — **обязательно** после каждого действия (1–2 строки). Шаг с изменениями файлов → запись сюда → `git commit` (код + ops **одним** коммитом) → отчёт. Канон: `workflow/smartcrm-commit-ops.mdc`.

**В строке журнала:** `Коммит: \`этот\`` — запись едет в том же коммите, что и код; реальный хеш агент называет в ответе пользователю. Хеши в старых записях — история, не переписывать. «Прочерк» / «потом» — запрещены.

2026-07-21 | Действие: оптимизация workflow — (1) один коммит на шаг: ops с `Коммит: этот` едут вместе с кодом, валидаторы принимают маркер, HANDOFF-проверка по последним 20 хешам (вечный WARN убран); (2) `scripts/check_step.cmd` — 3 валидатора одним вызовом UTF-8 (python в PowerShell Cursor теряет exit code); (3) триаж ISSUES: 4 стейл-записи закрыты с подтверждения, архив 2026-05/06_ISSUES, правило R14 «должки >месяца»; (4) BACKLOG: закрытое → архив 2026-06/07_BACKLOG; (5) regex сужены `{0,25}` + фикс scan_file; pytest tests/scripts 22 PASS | Коммит: `этот` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-21 | Действие: чеклисты фаз вместо PRD_MAP — созданы `docs/operations/phase{1-4}/CHECKLIST.md` (Ф1–Ф3 из архива, Ф4 из живого MAP + сводка модулей); `PRD_MAP.md` и `PRD_MAP_F1-F3.md` удалены; PHASE2_ENTRY → `docs/archive/ops/`; правила и доки переведены на «чеклист фазы»; +phase3/README; фикс ссылок PRD_NOTES; линк-чек 0 битых, валидаторы OK | Коммит: `7462df9` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-21 | Действие: разгрузка токенов — 4 шага: (1) дедуп правил: agent-workflow влит в commit-ops, task-workflow/-40%, .cursorrules/AGENTS.md/index сжаты, repo-layout+file-size-split на globs; (2) архив ops по месяцам → docs/archive/ops/; (3) продукт: VISION/ROADMAP/BUSINESS_LOGIC/FUNCTIONAL созданы, PRD/PRD_MAP разгружены, NOTES/DELTA/Ф1-Ф3 в архив; (4) DESIGN_SYSTEM.md; линк-чек 0 битых, все валидаторы OK | Коммит: `fdadf31`+`119d94d`+`8ffc43b`+`5b2070d`+ops | Хвост A: нет | Хвост B: BACKLOG редизайн UI | Хвост C: починены 7 старых битых ссылок в доках | Статус: done

2026-07-21 | Действие: чистка git status — runtime backend/data (api_stats, traces, checko_cache, ops_queue, sqlite и др.) в .gitignore + untrack; eval_benchmark_data.py → scripts/; .pytest_cache корня удалён; pytest tests/scripts 12 PASS | Коммит: `7a57856` | Хвост A: нет | Хвост B: BACKLOG архивация толстых ops-файлов | Хвост C: нет | Статус: done

2026-07-21 | Действие: BACKLOG § фронт/бэк связка — BFF-прокси, SSR-load, стриминг агентов; пока не делаем, ждёт go | Коммит: `3a98435` | Хвост A: нет | Хвост B: BACKLOG § фронт/бэк связка | Хвост C: нет | Статус: done

2026-07-18 | Действие: кнопка «+ Добавить ящик» в сайдбаре под «Все ящики»; browser-проверка через DevTools MCP (2 ящика видны, модал открывается) | Коммит: `f5d94d6` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-18 | Действие: управление ящиками — DELETE /api/email/accounts/{id} + сервис purge + UI кнопка «Отключить»; pytest 30 PASS | Коммит: `dfe93de` | Хвост A: browser не кликали; второй ящик не подключали | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-18 | Действие: BACKLOG § улучшения CI — 3 апгрейда (GROQ_API_KEY secret, зоны регрессии в CI, check_agent_step в CI); не срочно | Коммит: `f58fbde` | Хвост A: нет | Хвост B: BACKLOG § улучшения CI | Хвост C: нет | Статус: done

2026-07-18 | Действие: `.claude/` в .gitignore — untrack (git rm --cached), файлы на диске остались; секреты settings.local.json больше не в git | Коммит: `3e69864` | Хвост A: нет | Хвост B: нет | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 6 — SBR scope апрув (MAP+фичи; one-liner без SBR); миграция закрыта; BACKLOG post-migration долги | Коммит: `4a77384` | Хвост A: нет | Хвост B: BACKLOG § долги post-migration | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 5 — doc links workflow/ (PRD_MAP, PHASE2_ENTRY, docs/README, archive, debt); backend/scripts/scratch/; scripts/README | Коммит: `e89aa99` | Хвост A: SBR scope апрув (шаг 6) | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 4 — merged отчёт: таблица Сделано/Не сделано + A/B/C в task-workflow, commit-ops, agent-workflow, SBR, AGENTS, RULES_MATRIX | Коммит: `c872031` | Хвост A: doc links, scratch, SBR scope | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 3 — project-rules: 6× smartcrm-{core,tests,http,data,agents,performance}.mdc; index, .cursorrules, RULES_MATRIX; BACKLOG 4–6 | Коммит: `4456d72` | Хвост A: merged отчёт, doc links, scratch, SBR scope | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 2 — SBR: spec-build-review.mdc, todo.md, RED/GREEN в commit-ops/task-workflow/dev-gates/index; BACKLOG шаги 3–6 | Коммит: `a5f72b3` | Хвост A: project-rules, merged отчёт, doc links, scratch, scope SBR апрув | Хвост B: BACKLOG обновлён | Хвост C: нет | Статус: done

2026-07-18 | Действие: CoffeeOS workflow шаг 1 — `.cursor/rules/workflow/` (6 mdc), `project/` placeholder, `smartcrm-index.mdc`; rename code-split→file-size-split; обновлены AGENTS.md, .cursorrules, RULES_MATRIX, verify_cursor_rules_precedence.py; BACKLOG шаги 2–6 | Коммит: `c4318aa` | Хвост A: SBR, project-rules, merged отчёт, mass doc links, scratch | Хвост B: BACKLOG § CoffeeOS migration | Хвост C: нет | Статус: done

2026-07-01 | Действие: spawn_bitrix_backfill_focused — поля/tasks/products/import; task scope OK; timeline done; FAQ/IMAP выкл; pytest 2 PASS | Коммит: `7d40b32` | Хвост A: дождаться fields+import | Хвост B: нет | Хвост C: requisite.list Access denied (не блокер) | Статус: in_progress

> Архив: `docs/archive/ops/` (записи по месяцам).
