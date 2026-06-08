# HANDOFF

`Спринт:[Фаза 1] | Задача:[PRD_MAP перепроход /leads] | Статус:п.2 закрыт → п.3`

**Следующий шаг:** **п.3 «Воронка Kanban drag & drop»** — перепроход (есть `[x]` в коде, проверить DnD). Ждём `go`.

**Процесс:** `smartcrm-commit-ops.mdc` → тесты → **всегда** commit + ops → стоп до `go`. Push — только по апруву.

**Последние коммиты:** `f2727a3` feat автосинк Битрикс · `32d1537` ops sync

**User Rules:** не в репо — `CURSOR_USER_RULES_STATUS.md`; для SmartCRM достаточно `AGENTS.md` + `commit-ops.mdc`.

**Сделано в шаге (п.2):**
- Маппинг полей Битрикс → Lead (+ `amount_rub` из OPPORTUNITY/RUB)
- Автосинк: исходящий вебхук `POST /api/webhooks/bitrix/events` + фоновый опрос каждые 5 мин
- `GET /api/leads/bitrix-sync-status`
- pytest: `test_bitrix_row_map`, `test_bitrix_webhook`, live `test_bitrix_integration` — 7 passed

**Отложено (бэклог):** туннель + исходящий вебхук Битрикса → [`BACKLOG.md`](BACKLOG.md). Не блокер п.3.

**Блокеры:** нет 🔴

**Открытые вопросы:** нет.

---
