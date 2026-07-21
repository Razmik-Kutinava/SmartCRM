# todo — микро-чеклист текущей фичи

> **Живой чеклист шага.** Макро-веха — пункт чеклиста фазы (`../phase4/CHECKLIST.md`).  
> SBR: PHASE 1 заполняет этот файл → PHASE 3 очищает или архивирует.  
> Канон: [`spec-build-review.mdc`](../../../.cursor/rules/workflow/spec-build-review.mdc)

---

## Заказ (дословно)

> Цитата пользователя из чата — **источник истины** (PHASE 0 INTAKE). Спор о scope решается по ней.

> «иатк вот тебе задача · ### Email (тюнинг Ф4) · доку мент @docs/operations/phase4/CHECKLIST.md · сделай ка · [ ] Ящики в UI (`/email` Настройки или `/ops/integrations`) — без единственной зависимости от `.env` · сделай ее»

**Как понял:** закрыть пункт Ф4 Email «Ящики в UI»: управление почтовыми ящиками полностью из UI `/email` (Настройки), чтобы `.env` был лишь опциональным bootstrap, а не единственным путём.

---

## Текущая задача

| Поле | Значение |
|------|----------|
| **Пункт чеклиста** | Ф4 · Email (тюнинг) · «Ящики в UI (`/email` Настройки или `/ops/integrations`) — без единственной зависимости от `.env`» |
| **Описание** | Модалка подключения, `POST /accounts/connect`, шифрование и DELETE уже есть. Гэпы: в настройках `/email` нет списка ящиков со сводкой env (хелпер `fetchEmailConfigStatus` мёртвый), bootstrap из env не выведен в UI, нет API-тестов на `GET /accounts` / `POST /accounts/connect`. Поверхность — модалка настроек `/email` (роута `/ops/integrations` не существует, он — отдельный пункт «Интеграции CRM») |
| **Started** | 2026-07-21 (PHASE 1 SPEC, ждём `go` на BUILD) |

---

## Чеклист

- [ ] **RED:** `backend/tests/api/test_email_accounts_api.py` — `GET /api/email/accounts`, `POST /accounts/connect` (mock sync, пустые `EMAIL_*` env → работает), `POST /bootstrap-from-env` идемпотентен при уже подключённом из UI ящике
- [ ] **GREEN backend:** минимальные правки `api/routes/email.py` по итогам RED (ожидается почти без кода — контракт уже есть)
- [ ] **GREEN frontend:** модалка настроек `/email` → секция «Подключённые ящики»: список из `GET /accounts` (синк/отключить), сводка env через `fetchEmailConfigStatus()` (`/config/status`), кнопка «Импортировать из `.env`» → `POST /bootstrap-from-env`
- [ ] Регрессия зоны email: `python -m pytest tests/email/test_email_f3.py tests/api/test_email_sync_api.py tests/api/test_email_env_config.py tests/api/test_email_account_delete.py -q`
- [ ] Доки: отметки в `F4_EMAIL_TUNING.md` § A + `backend/tests/README.md` (новый тест-файл)
- [ ] UI-проверка `/email` (DevTools MCP) — модалка: список ящиков, сводка env, импорт

---

## Архив (последние закрытые)

_После PHASE 3 REVIEW — перенести сюда одной строкой или очистить._
