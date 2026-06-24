# Ф4 — X5-gap шаг 4: webhook scope **task** + resync задач

**PRD_MAP:** «Webhook scope task» · задачи/встречи из Битрикс → `tasks`.

**Код:** ✅ (`59490d3`). **Портал:** 🔲 scope **task** не включён (live probe 2026-06-24).

---

## Что нужно на вебхуке

| Scope | Зачем в SmartCRM | Probe |
|-------|------------------|-------|
| **crm** | лиды, контакты, activity, реквизиты, UF, productrows | `crm.lead.list` |
| **user** | имена ответственных | `user.current` |
| **task** | `tasks.task.list` — дела/задачи по лиду | `tasks.task.list` |

Без **task** работают: импорт лидов, UF, контакты, история (`crm.activity`), mass-resync полей.  
**Реквизиты:** `crm.requisite.list` на портале может дать `Access denied` (400) — ИНН тогда из UF; не блокер mass-resync полей.

**Не работает:** импорт задач из `tasks.task` (resync задач блокируется preflight).

---

## Live probe (2026-06-24, crm.agneko.com)

```
CRM (crm):     ok
Пользователи:  ok
Задачи (task): missing — tasks.task.list → 401
```

Feature API при crm ok: `lead.get`, `activity.list`, `contact.items`, `requisite.list`, `userfield.list`, `productrows` — **ok**.  
`tasks.task.list` — **missing** (нужен scope task).

---

## 👤 Оператор: включить scope task

1. Битрикс24 → **Разработчикам** → **Другое** → **Входящий вебхук** (тот же, что в `BITRIX24_WEBHOOK_URL`).
2. **Настройка прав** — отметить:
   - CRM (crm) — уже есть
   - Пользователи (user) — уже есть
   - **Задачи (task)** — **включить**
3. **Сохранить** — Битрикс может выдать **новый URL** (секрет в пути).
4. Скопировать полный URL в корень репо:
   ```env
   BITRIX24_WEBHOOK_URL=https://crm.agneko.com/rest/USER/секрет/
   ```
5. Перезапустить uvicorn.
6. Проверка:
   ```bash
   cd backend
   python scripts/check_bitrix_webhook_scopes.py
   ```
   Ожидание: `OK: crm + user + task` + JSON `data/bitrix_webhook_scope_report.json`.

---

## Resync задач (после OK probe)

```bash
cd backend
# smoke
python scripts/resync_bitrix_lead_tasks.py --limit 5 --workers 2

# полный прогон (~3228 лидов)
python -u scripts/resync_bitrix_lead_tasks.py --workers 3 --batch-size 30 --delay-ms 50
```

Preflight: без scope **task** скрипт **не стартует** — понятная ошибка + `webhook_setup_hint`.

Параллельно тянет `crm.activity` (встречи/звонки) — это scope **crm**, уже ok.

---

## Команды диагностики

| Команда | Назначение |
|---------|------------|
| `python scripts/check_bitrix_webhook_scopes.py` | Scope + feature API → `data/bitrix_webhook_scope_report.json` |
| `python scripts/resync_bitrix_lead_engagement.py --check-scopes-only` | Только probe |
| `python scripts/resync_bitrix_lead_tasks.py --skip-scope-check` | **Не использовать** без task — только для отладки activity |

---

## Критерий закрытия шага 4

- [ ] `check_bitrix_webhook_scopes.py` → exit 0, task **ok**
- [ ] `resync_bitrix_lead_tasks.py --limit 5` → без FAILED
- [ ] На карточке лида с задачами в B24 — блок задач в CRM пополнился

---

## Статус

| Часть | Статус |
|-------|--------|
| Probe + понятный 401 | ✅ |
| `resync_bitrix_lead_tasks.py` | ✅ |
| Extended feature API probe | ✅ |
| 👤 Scope task на портале | 🔲 blocked |
| Mass resync задач | 🔲 после scope |
