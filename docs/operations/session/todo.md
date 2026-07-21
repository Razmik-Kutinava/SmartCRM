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

- [x] **RED:** `backend/tests/api/test_email_accounts_api.py` — 3 FAIL / 1 PASS (`ae5d842`)
- [x] **GREEN backend:** явный `commit` в `POST /accounts/connect` (`api/routes/email.py`) — 4 PASS
- [x] **GREEN frontend:** модал «Почтовые ящики»: синк на каждый ящик + IMAP/дата синка, секция «Ящики в .env» + «Импортировать из .env» (`bootstrapEmailFromEnv`), скролл модалки
- [x] Регрессия зоны email: 33 PASS, 1 FAIL `test_faq_autoreply_mocked` — **pre-existing** (падает и на чистом HEAD: в корневом `.env` `EMAIL_FAQ_AUTOREPLY=0` — тест зависит от окружения) → ISSUES
- [x] Доки: `F4_EMAIL_TUNING.md` § A + `backend/tests/README.md`
- [x] UI-проверка `/email` (DevTools MCP) — модалка: список ящиков (Agneko AM/IB), синк/отключить, «Все ящики из .env уже подключены (2)»

---

## Архив (последние закрытые)

_После PHASE 3 REVIEW — перенести сюда одной строкой или очистить._
