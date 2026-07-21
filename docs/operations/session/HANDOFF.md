# HANDOFF

`Спринт:[Наведение порядка] | Задача:[свежесть CHANGELOG/HANDOFF в check_step + hook] | Статус: ✅ done | 👤 —`

**2026-07-21:** `check_agent_step.py` теперь ловит отставание журналов: done-шаг в SESSION_STATE без записи CHANGELOG/HANDOFF за ту же дату → FAIL (RED-подшаги не трогает). 8 тестов, 30 PASS по tests/scripts. Pre-commit hook был мёртвый (старый путь до `session/`) — переустановлен пользователем. В BACKLOG: агент сам начинает вести `todo.md` через 3–6 прогонов (коммит `91d10e3`). Коммит: `этот`. **👤:** ничего не требуется; следующий шаг — пункт Ф4 из чеклиста.

---

`Спринт:[Наведение порядка] | Задача:[оптимизация workflow: 1 коммит/шаг + check_step + триаж ISSUES/BACKLOG] | Статус: ✅ done | 👤 ревью новых правил`

**2026-07-21:** Разбор трений процесса, по `go`: (1) **один коммит на шаг** — ops с `Коммит: \`этот\`` в том же коммите, что код; «ops:»-коммиты запрещены; (2) **`cmd /c scripts\check_step.cmd`** — все валидаторы одним вызовом (python в PowerShell Cursor теряет exit code — не запускать напрямую); (3) ISSUES: должки закрыты и в архиве, живой журнал пуст, правило R14; (4) BACKLOG: закрытое в `docs/archive/ops/`, живы только хвосты. Коммит: `этот`. **👤:** глянуть обновлённый `commit-ops.mdc` и пустой `ISSUES.md`; в глобальных User Rules Cursor удалить правило про CoffeeOS и дубль про SmartCRM-коммиты (Settings → Rules) — из репо это не чинится.

---

`Спринт:[Наведение порядка] | Задача:[чеклисты фаз вместо PRD_MAP] | Статус: ✅ done | 👤 ревью чеклистов`

**2026-07-21:** Фазами управляем из операционки: `docs/operations/phase{1-4}/CHECKLIST.md` (Ф1–Ф3 закрыты, Ф4 — рабочий). `PRD_MAP.md` удалён из продукта (архив Ф1–Ф3 тоже — содержимое 1:1 в чеклистах); `ROADMAP.md` — навигатор; `PHASE2_ENTRY` → `docs/archive/ops/`. Все правила и доки на «чеклист фазы». Коммит `7462df9`. **👤:** глянуть `phase4/CHECKLIST.md` — это теперь рабочий чеклист; дальше пункт Ф4 или редизайн UI (BACKLOG).

---

`Спринт:[Наведение порядка] | Задача:[разгрузка токенов: правила + ops-архив + продуктовые доки] | Статус: ✅ done | 👤 ревью новых доков`

**2026-07-21:** 4 шага: дедуп правил (agent-workflow удалён, layout/file-size на globs, always-объём −49%); ops-журналы по месяцам → `docs/archive/ops/` (живые — текущий месяц); продукт: +VISION/ROADMAP/BUSINESS_LOGIC/FUNCTIONAL/DESIGN_SYSTEM, PRD/PRD_MAP разгружены, NOTES/DELTA/Ф1-Ф3 → `docs/archive/product/`; линк-чек 0 битых. Коммиты `fdadf31`, `119d94d`, `8ffc43b`, `5b2070d`. **👤:** прочитать новые доки `docs/product/` — поправить формулировки под себя; дальше PRD_MAP Ф4 или редизайн UI (BACKLOG).

---

`Спринт:[Наведение порядка] | Задача:[чистка git status] | Статус: ✅ done | 👤 продукт / PRD_MAP`

**2026-07-21:** Runtime-файлы `backend/data/` (api_stats, traces, checko_cache, ops_queue, sqlite, state/notifications) → `.gitignore` + untrack (диск цел); `eval_benchmark_data.py` → `backend/scripts/`; `.pytest_cache` корня удалён. git status теперь чистый. Коммит `7a57856`. **👤:** следующая задача — PRD_MAP или BACKLOG (архивация толстых ops-файлов — записана).

---

`Спринт:[Ф4 Email] | Задача:[+ Добавить ящик в сайдбаре] | Статус: ✅ done | 👤 проверка`

**2026-07-18:** Кнопка «+ Добавить ящик» под селектом «Все ящики» в сайдбаре `/email` (открывает модал подключения). Диагностика DevTools MCP: оба ящика уже подключены (`me@agneko.am` + `ib@agneko.com`), второй был в скрытом селекте. **👤:** обновить `/email`, кнопка под «Все ящики».

---

`Спринт:[Ф4 Email] | Задача:[управление ящиками] | Статус: ✅ done (код) | 👤 browser`

**2026-07-18:** Отключение ящика из UI — кнопка «Отключить» в модалке `/email` + `DELETE /api/email/accounts/{id}` (очистка переписки/кампаний/цепочек). **👤:** открыть настройки почты, отключить лишний ящик; подключить второй и переключиться.

---

`Спринт:[Наведение порядка] | Задача:[.claude → gitignore] | Статус: ✅ done | 👤 продукт / PRD_MAP`

**2026-07-18:** `.claude/` в .gitignore, untrack (файлы на диске). Коммит `3e69864`. **👤:** следующая задача — PRD_MAP или чистка доков.

---

`Спринт:[CoffeeOS workflow] | Задача:[миграция rules] | Статус: ✅ done | 👤 продукт / PRD_MAP`

**2026-07-18:** CoffeeOS workflow **закрыт** (1–6). SBR scope зафиксирован. Коммит `4a77384`. **👤:** PRD_MAP или `go` на долг из BACKLOG § post-migration.

---

`Спринт:[CoffeeOS workflow] | Задача:[шаг 5 — doc links + scratch] | Статус: ✅ done (код) | 👤 go / апрув шаг 6`

**2026-07-18:** SBR — `spec-build-review.mdc`, `todo.md`, RED/GREEN в commit-ops. Коммит `a5f72b3`. Scope: PRD_MAP + фичи; one-liner без SBR. **👤:** `go` на шаг 3 (project-rules) или правки scope SBR (BACKLOG §6).

---

`Спринт:[CoffeeOS workflow] | Задача:[шаг 1 — каркас rules] | Статус: ✅ done (код) | 👤 go на шаг 2`

**2026-07-18:** Правила Cursor реорганизованы: `.cursor/rules/workflow/` (6 файлов), `smartcrm-index.mdc`, `project/` placeholder. Коммиты `c4318aa` + `4861e9e`. **👤:** `go` на шаг 2 (SBR) или правки по BACKLOG § CoffeeOS migration.

---

`Спринт:[B24 backfill] | Задача:[фокусный backfill + task scope] | Статус: 🔄 in_progress | 👤 мониторинг`

**2026-07-01:** `spawn_bitrix_backfill_focused.py` — поля, задачи (scope task OK), продукты, import; таймлайн/watch **не** запускаются. Почта: FAQ=0, IMAP=0, uvicorn перезапущен. **👤:** `bitrix_fields_resync_state.json`, `check_lead_coverage.py`.

---

> Архив: `docs/archive/ops/` (блоки по месяцам).
