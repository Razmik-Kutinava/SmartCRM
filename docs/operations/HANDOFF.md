# HANDOFF

`Спринт:[Фаза 1] | Задача:[PRD_MAP блок «Лиды»] | Статус:ЗАКРЫТ`

**Блок «Лиды `/leads`» (п.1–12) — перепроход завершён 2026-06-08.**

**Следующий шаг:** Фаза 1 — следующий модуль по PRD_MAP (балльная воронка смоук / голос / поиск). Ждём `go` от пользователя.

**П.12 смоук:**
- `backend/scripts/smoke_leads_block.py` — 19 модулей pytest, **71 passed**
- `leadsRouteManifest.js` — канон 6 вкладок + card/campaign
- `run_zone_regression.py crm_leads` — зона расширена
- Frontend HTTP: WARN (dev-сервер не был запущен); при смоук UI — `npm run dev` + повтор скрипта

**Команда регрессии:**
```bash
cd backend && python scripts/smoke_leads_block.py
cd backend && python scripts/run_zone_regression.py crm_leads
```

**Блокеры:** нет 🔴

---
