# Ф3 — Тех. спец: уведомления + календарь дедлайнов

**PRD_MAP:** Фаза 3 → Тех. спец — тендеры → п.2.

**Суть:** in-app уведомления (новые тендеры + напоминания 7/3/1/0 дней и просрочка) + календарь дедлайнов по «Мои» и мониторингу.

---

## Сделано

| # | Что | Где |
|---|-----|-----|
| 1 | Хранилище уведомлений | `data/tender_notifications.json` |
| 2 | Новый тендер → уведомление | `tender_monitor.push_new_to_queue` |
| 3 | Tracked для календаря | `tender_monitor_state.json` → `tracked` |
| 4 | Скан дедлайнов 7/3/1/0 + overdue | `tender_calendar.scan_deadline_notifications` |
| 5 | Срочные → Ops-очередь | `auto-tender-deadline-*` |
| 6 | Фон: скан каждые N ч | `deadline_scan_interval_hours` в monitor config |
| 7 | API | `/api/tenders/notifications`, `/calendar/month`, `POST /calendar/scan-deadlines` |
| 8 | UI | `/tenders/notifications`, `/tenders/calendar`, колокольчик на `/tenders` |

---

## Проверка

1. Мониторинг находит тендер → `/tenders/notifications` — «Новый тендер».
2. Сохранить тендер с дедлайном в «Мои» → `/tenders/calendar` — день в сетке.
3. «Проверить дедлайны» — напоминание за 3/1/0 дней (подставить дату в snapshot).
4. Просрочка → уведомление + пункт в `/ops/queue`.

```bash
cd backend
python -m pytest tests/services/test_tender_calendar.py tests/api/test_tenders_calendar_api.py -q
```

---

## Не в этом шаге

- Email/Telegram push
- Контур API
- Авто-разбор ТЗ → RAG
