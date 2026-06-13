# ISSUES

Журнал инцидентов и багов. Приоритеты: 🔴 блокер, 🟡 важно, 🟢 потом.

Шаблон одной записи:

`[YYYY-MM-DD] — [название]`  
`Приоритет: 🔴/🟡/🟢 | Статус: открыта/в работе/закрыта`  
`Описание:[...] | Влияние:[...] | Решение:[...] | Агент:[...]`

---

[2026-06-08] — `/leads/tasks`: 500 compile (shadow `createTask`)

Приоритет: 🔴 | Статус: закрыта ✅

Описание: DevTools смоук п.12 — `+page.svelte` 500, рекурсия импорта `createTask`.

Решение: `apiCreateTask` + `submitTaskForm` в `frontend/src/routes/leads/tasks/+page.svelte`.

Агент: PRD_MAP п.12 acceptance

---

[2026-06-08] — Битрикс: мгновенный синк (вебхук + публичный URL)

Приоритет: 🟡 | Статус: отложена → [`BACKLOG.md`](BACKLOG.md)

Описание: Код готов; для мгновенного синка нужны публичный URL (туннель/деплой) + исходящий вебхук в портале. Сейчас: импорт кнопкой + опрос раз в 5 мин.

Решение: см. BACKLOG «туннель :8000 + ONCRMLEADADD».

Агент: PRD_MAP п.2

---

[2026-06-08] — PRD_MAP п.1: UI Update лидов неполный (контакты read-only)

Приоритет: 🟡 | Статус: закрыта ✅

Описание: На `/leads/{id}` не было формы правки контактов/деталей.

Решение: `leadCardEdit.js` + «Сохранить карточку»; убран `editingLead` в list. DevTools: PATCH contact/industry OK.

Агент: PRD_MAP Фаза 1 pass

---

[2026-06-08] — Frontend dev: native bindings win32-arm64 (rollup/lightningcss)

Приоритет: 🟡 | Статус: закрыта ✅

Описание: `npm run dev` падал на rollup/lightningcss (npm/cli#4828).

Решение: Vite 6 + rollup wasm override + `scripts/ensure-native-deps.cjs`. Dev server OK.

Агент: PRD_MAP Фаза 1 pass

---

[2026-06-07] — `test_hermes_eval.py`: 9 failed (интенты create/update/noop)

Приоритет: 🟡 | Статус: открыта

Описание: `python scripts/run_zone_regression.py all` — зона `hermes_eval` падает: `TestHermesIntents` case0–3 create/update, noop case2. P1/P6 смоук без hermes_eval — зелёные.

Влияние: регрессия зоны «Hermes eval» не проходит локально; голос (`test_voice_pipeline`) — OK.

Решение: проверить Ollama/LLM env, обновить фикстуры/ожидания после сплита `core/hermes/`; не смешивать hermes_eval с p1/p6 смоуком.

Агент: rules-audit session

---

[2026-05-04] — GET /api/leads → 500: обрыв соединения с Postgres, не бизнес-логика

Приоритет: 🟡 | Статус: закрыта ✅

Описание: В логах uvicorn: `ConnectionResetError: [WinError 10054]`, затем `asyncpg.exceptions.ConnectionDoesNotExistError` на `db.get` / `db.execute`.

Root cause (финальный): База данных `smartcrm` и пользователь `smartcrm` отсутствовали в Postgres — asyncpg падал ещё на TCP handshake, до авторизации. Промежуточные правки (`pool_pre_ping`, `localhost→127.0.0.1`) были корректны, но не помогали именно по этой причине.

Решение:
1. `psql -U postgres -c "CREATE USER smartcrm WITH PASSWORD 'smartcrm';"` — создан пользователь.
2. `psql -U postgres -c "CREATE DATABASE smartcrm OWNER smartcrm ENCODING 'UTF8';"` — создана БД.
3. `GRANT ALL ON SCHEMA public TO smartcrm; ALTER SCHEMA public OWNER TO smartcrm;` — права на схему.
4. Uvicorn перезапущен (через touch `db/session.py`) → `init_db` создал все таблицы.
5. Проверка: `GET /api/leads` → 200 OK, `GET /api/leads/1791` → 404 (база пустая — OK).

Примечание: Предыдущие патчи (`pool_pre_ping`, `pool_recycle`, нормализация URL) оставлены — они верны для стабильности пула.

Агент: —

---

[2026-05-04] — Uvicorn/SQLAlchemy: падение импорта `LeadFieldAudit` (MappedAnnotationError)

Приоритет: 🔴 | Статус: закрыта

Описание: В `lead_field_audit.py` поле `audit_metadata` имело аннотацию `Mapped[Optional[dict]]` без импорта `Optional` из `typing`. При загрузке приложения SQLAlchemy вызывал `NameError: name 'Optional' is not defined` → 500 на всех маршрутах лидов.

Влияние: Локальный бэкенд не поднимался; фронт получал 500 на `/api/leads/...`, comments, audit.

Решение: Импорт `Any`, `Optional`; аннотация `Mapped[Optional[dict[str, Any]]]`; для согласованности — `Lead.approvals: Mapped[Optional[dict[str, Any]]]`.

Агент: —

---

[2026-05-03] — Дрейф PRD (MVP) относительно фактических фич

Приоритет: 🟡 | Статус: открыта

Описание: В `docs/product/PRD.md` чекбоксы Фазы 1 не отмечены и не отражают уже существующие области (тендеры, расширенный CRM UI, ops). Риск: PM/BA не могут опереться на один согласованный scope.

Влияние: Планирование спринтов и приёмка без единого источника правды по «что уже продукт».

Решение: BA + PM: дельта PRD ↔ факт (таблица фича/done/источник); отдельный `go` на правку `docs/product/PRD.md` или заведение `docs/product/PRD.md` по процессу.

Агент: —

---

[2026-05-03] — Локальная среда: API лидов без PostgreSQL

Приоритет: 🟡 | Статус: открыта

Описание: При недоступной БД `GET /api/leads` даёт 500 (asyncpg); в логах старта — предупреждение о недоступности БД.

Влияние: Локальная разработка без Postgres ломает основной список лидов; UX/QA неясно, ожидаемый ли degraded mode.

Решение: Architect + Backend: политика «жёсткий фейл vs пустой список + явная ошибка в UI»; отдельный `go` на изменение кода. QA: сценарий смоука «без БД».

Агент: —

---

[2026-05-03] — QA-матрица покрытия не документирована

Приоритет: 🟢 | Статус: открыта

Описание: Тесты в `tests/` и `backend/tests/`; нет одного индекса «модуль → тесты → смоук».

Влияние: Регрессии при параллельной разработке CRM/tenders/voice.

Решение: QA: таблица покрытия + минимальный CI-чеклист; ссылка из `docs/dev/WORKFLOW.md` или отдельный раздел — после `go`.

Агент: —

---
