# HANDOFF

`Спринт:[Фаза 1] | Задача:[PRD_MAP перепроход /leads] | Статус:п.2 закрыт → п.3`

**Следующий шаг:** **п.3 «Воронка Kanban drag & drop»** — перепроход (есть `[x]` в коде, проверить DnD). Ждём `go`.

**Процесс:** `smartcrm-commit-ops.mdc` → тесты → **всегда** commit + ops → стоп до `go`. Push — только по апруву.

**Последние коммиты:** (см. `git log -3` после шага правил)

**Сделано в шаге (п.2):**
- Маппинг полей Битрикс → Lead (+ `amount_rub` из OPPORTUNITY/RUB)
- Автосинк: исходящий вебхук `POST /api/webhooks/bitrix/events` + фоновый опрос каждые 5 мин
- `GET /api/leads/bitrix-sync-status`
- pytest: `test_bitrix_row_map`, `test_bitrix_webhook`, live `test_bitrix_integration` — 7 passed

**Действие пользователя (критично для «сразу»):**
1. Перезапустить uvicorn (новый код в `main.py` lifespan).
2. В Битрикс24: **исходящий вебхук** → события `ONCRMLEADADD`, `ONCRMLEADUPDATE` → URL `https://<хост>/api/webhooks/bitrix/events?token=<BITRIX_OUTBOUND_TOKEN>`.
3. В `.env`: `BITRIX_AUTO_SYNC_MINUTES=5` (уже в `.env.example`).

**Блокеры:** без исходящего вебхука в портале — только опрос раз в 5 мин (не мгновенно). 🟡

**Открытые вопросы:** нет.

---
